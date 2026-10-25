# Story O14: one retry policy for failed commands (exponential backoff, at most 5 retries, then escalate)

**Lane 1, two judges** (it decides whether a step that writes records runs again, and it calls outside services:
Groww, NSE, Drive, Slack). **Builder:** session_016CU8KFuEEtWAM7ZNnFcKxv (O1's owner from 25 Oct). **Status:** story
text round 2 (judges E 682 and F 683: every finding answered below). It links the stories it touches and does not
restate them: O1 (`O1-daily-run.md`), O1-day-lock, GW1a (`GW1a-groww-guard-core.md`), A4, A16
(`A16-intraday-quote-recorder.md`), A22 (`A22-preopen-data.md`), FL1-1d, MS-P1j (`MS-market-school.md`) and T1.

## 1. The owner's decision

Owner, 25 Oct 2026 (`docs/DESK_DECISIONS.md`, "Failed commands: automatic retry with exponential backoff, at most 5
retries, then escalate"): "if a command fails then let's add a retry mechanism to add an exponential backoff policy
with a maximum 5 retries. if it still fails after 5 retries then we highlight and escalate to human or operator. but
what adding an exponential backoff policy is important like we do in circuit-breaker design patterns or the same
mechanism we use in kafka or publisher patterns with always a maximum number of retries before we stop."

"At most 5" allows fewer where a window or a source's limit needs it. Everything below that is not the owner's words
is the builder's design (reasoning only where no data backs it).

## 2. Loops that exist already (one line each; each story owns its loop)

- The 3 pm, indices and `v4` quote parts retry an incomplete capture every 60 s inside their windows (A4, A4c, A4e).
- E3's pack is rebuilt every 30 s until `pack_wait_until`, and the execution snapshot has one common retry (O1, E3).
- A22 reads each pre-open part at its window's opening, then every 30 s, the last at its margin (`fno/preopen/run.py`).
- GW1a's sign-in back-off (+5, +10 minutes, at most 3 tries a process a day) and its 60 s stop after a 429.
- NSE's pacer: 1 s spacing, and two refusals pause the host for 15 minutes (`fno/http_pacing.py`).
- O1 R2: a failed `exits` or `trade_marks` step is retried by CLAUDE.md step 2b's one rerun; `fills` is final.

O14 replaces none of these loops. It adds one rule for a whole failed step or command, and retires step 2b.

## 3. The policy (one interface, one strategy, wired in the composition roots)

- **`RetryPolicy`** (`fno/retry/policy.py`, new package): `next_wait(attempt, now, deadline, expected) -> timedelta |
  None`; None means stop.
- **`ExponentialBackoff`**, its one strategy: wait `min(cap, base * 2**(attempt - 1))` times a jitter in [0.8, 1.2].
  The jitter source is injected, so tests are exact. The numbers (reasoning only):
  - **standard:** base 30 s, cap 8 minutes, at most 5 retries: 30 s, 1, 2, 4, 8 minutes, at most 15.5 minutes plus
    the jitter;
  - **short** (A16's marks, below): base 5 s, cap 30 s, at most 2 retries.
- **`CircuitBreaker`** (`fno/retry/circuit.py`), one per source (Groww, NSE, Drive, Slack). A source's own guard's
  error opens it, and an open circuit stops the retries at once (section 5).
- **`RetryRunner`** (`fno/retry/runner.py`):
  - classifies an attempt as done, retryable, final, or circuit open;
  - waits through the run's `Waiter`, so the 3 pm parts are serviced while it waits (O1 criterion 4a);
  - records each attempt;
  - escalates once.
- **Retryable classes** are the step's own list. The default is a timeout from the step's own call, a connection
  error or a 5xx answer. Always final:
  - a refusal ("nothing written:", a cutoff passed);
  - `AccountWriteRefused`;
  - `CommitFailed` and `GitFailed` (decision 44's run stop);
  - a command stopped at `COMMAND_LIMIT_SECONDS`. After 600 s the child may already have uploaded to Drive before its
    commit, so a stopped command is never retried; it escalates.
- **The settings** live in `config.yaml` under `retry`: the two policies' numbers and the Groww budget.

### 3.1 The deadline rule (judge E should-fix 1)

The daily run is one thread, so a retry delays every later step. A step's **retry deadline** is the earliest of:
1. its own deadline (section 4);
2. the latest start of every later step with a hard time in `DAILY_RUN_STEPS`:
   - the pack by `pack_wait_until` (15:10);
   - `decisions` at `decision_deadline` (15:12);
   - `snapshot` and `fills` by `fills_by` (15:20 in `config.yaml` today);
   - the school by `SLOT_LAST_START` (15:25);
   - `premium_ranges` by its `DEADLINE` (15:30);
   - each read from its own constant, never copied.

A retry is made only if `now + wait + expected <= retry deadline`. Otherwise the policy stops now and escalates with
"the next wait would pass <HH:MM> (<which step's limit>)". A retry never moves a later step past its limit.

**The expected run time** is the step's own duration in the previous session's committed run log (`finished_at -
started_at`), times 1.5. With no earlier run, it is `COMMAND_LIMIT_SECONDS` (600 s) for a command step and 60 s for
an in-process desk step. Reasoning only: the 1.5 margin covers a slower day, and the fallback is the longest a command
may run.

## 4. Every caller, its own deadline and how it plugs in

| Caller | Own deadline (its source) | Retry deadline (section 3.1) | Plugs in |
|---|---|---|---|
| `weather`, `forecasts_v4` | 14:30 cutoff (CLAUDE.md "Daily desk routine") | 14:30 | through `Alerted` (below) |
| `v4_release` | 14:45 (G10: the release by 14:45) | 14:45 | through `Alerted` |
| `forecasts_v4_pack` | 15:10 (committed before 15:10, G7b) | 15:10 | through `Alerted` |
| `book1` | `decision_deadline` 15:12 (E3) | 15:12 (`decisions`, the next timed step; the pack runs before it) | through `Alerted` |
| desk `exits`, `trade_marks` (O1 R2) | none of their own (they read the 15:15 snapshot) | 15:25 (the school) | `_run_step`, for `RETRIED_ON_RERUN` only |
| `reviews`, `card`, `price_distribution` | none of their own | 15:25 (the school) | through `Alerted` (not safe: section 6) |
| `premium_ranges` | 15:30 (`fno/premium_ranges/constants.py` `DEADLINE`) | 15:25 (the school runs after it) | through `Alerted` |
| `recommend`, the score steps, `price_ranges`, `v4_deadline` | 16:00, `close_recheck`'s start (named, judge E m2) | 16:00 | through `Alerted` |
| `candles` (A16b) | 16:00, `close_recheck`'s start | 16:00 | through `Alerted`; a Groww child (section 5) |
| `close_read` (15:40), `close_recheck` (16:00) | 19:53, the evening routine that reads the close (CLAUDE.md, FL1-1d step 1c) | 19:53 | through `Alerted` |
| `fills`, the school | never retried (owner questions 1 and 2) | - | none |
| 3 pm, indices and `v4` quote parts | their own windows (A4) | - | **not wrapped**: their own 60 s loop; an outer retry would start a second capture. O14 sends nothing for them: each part alerts itself (A4c rule 4) |
| E3's pack and execution snapshot | their own windows | - | **not wrapped**: their own loops |
| A22's pre-open reads | GIFT Nifty 08:40-08:44:59; the F&O list 09:08:30-09:10:59; the candle read 09:10:00-09:10:45, window to 09:11:00 (CLAUDE.md "Pre-open capture") | - | **not wrapped**: A22's own 30 s loop (judge F finding 1) |
| A16's marks | each mark + 120 s (A16 "Slots") | the mark + 120 s | the short policy, inside the fire's own process (section 5) |
| `lab open` | before 09:15 (it posts nothing at or after 09:15, FL1-1d) | 09:15 | its entry point; **not safe** (it posts) |
| `lab close` | the next morning's 08:38 routine | 08:38 next day | its entry point; **not safe** (it posts) |
| The evening's librarian commands (FL1-1d step 1c) | before `lab close` in the same routine | `lab close`'s start | each entry point |
| GitHub workflows | their own | - | out of scope (Actions has its own reruns) |

**Through `Alerted`:** O1's wrapper keeps its one alert per failed step. The runner sits inside it, so the step
alerts once, at the end, with the escalation line (section 7), never once per attempt.

## 5. The circuit breaker and Groww's limits

- **A refusing source is never retried blindly.**
  - `GrowwRateLimited` or `GrowwRateLimitPaused` opens Groww's circuit for at least GW1a's 60 s pause. The next wait
    is the larger of the backoff and the pause.
  - NSE's `SourceCoolingOff` opens NSE's circuit for its 15-minute cool-off; a step whose retry deadline falls inside
    it escalates at once.
  - **A Groww sign-in failure is never retried by O14**, in the same process or as a new child, for the rest of the
    day. GW1a's own back-off is the only sign-in retry.
- **How the parent sees a child's Groww error (judge E should-fix 2, judge F finding 4).**
  - A child's failure class reaches the daily run through its last printed line (`outcome()` in
    `fno/daily/steps.py`; class names only, public).
  - The runner matches it against a closed list: GW1a's `GrowwSignInPaused`, `GrowwRateLimited`,
    `GrowwRateLimitPaused` and the sign-in failure class it names, plus NSE's `SourceCoolingOff`. A match opens the
    parent's circuit for that source.
  - **A Groww child whose class cannot be read is treated as a sign-in failure**: no retry, escalate (fail closed).
- **The Groww sign-in budget, with a margin.**
  - Groww's limit is 150 sign-ins in a rolling 24 hours (GW1a, from the 22 Oct probe). GW1a's worst case for one
    session day is 38 processes x 3 = 114.
  - O14 counts **sign-ins, not processes**: at most **12 sign-in tries a day** by O14's Groww child retries, counted
    in the run log (3 per new child, GW1a's per-process maximum), so at most 4 extra Groww children.
  - The worst case becomes 126. That leaves 24 under 150 for the rolling window's overlap: the next morning's 08:36
    pre-open adds 3 inside the same 24 hours, so 129.
  - When the budget is spent, the policy escalates ("the day's Groww retry budget is spent").
  - Today the daily run's Groww children that O14 may retry are `candles` and, once built, `margin_check`. The
    quote parts are not wrapped.
- **Groww calls per retry (judge F finding 2).** A retry repeats its whole attempt. GW1a counts 3-6 calls for an A16
  mark, and the mark already asks once more for failed quotes.
  - **A16:** at most 2 retries per mark, so at most 12 extra calls, within the mark's 120 s, in the fire's own
    process (its signed-in client, no new sign-in).
  - **No Groww retry of a mark whose retry could overlap another Groww window:** the 14:30 mark (the `v4` capture
    starts 14:32), the 14:45, 15:00 and 15:15 marks (the 3 pm capture 14:55-15:10, the indices 15:01-15:13, the
    execution snapshot 15:15-`fills_by`). Each window is read from its owner's constant, never copied.
  - A retried `candles` run repeats its catch-up calls, after 15:33, when no capture runs.
- **No guard's wait is ever shortened**, and A4's pacing and GW1a's pause stay the only Groww pacing.

## 6. Which steps may be retried (judge F finding 3): not safe by default

A step is safe only when its write-once guard refuses a second, different write and accepts the same one, and it posts
nothing to Slack beyond the one escalation (judge E m3: a Slack post is the one write that is not write-once). Each
row's guard is the code's own message; the code round adds one test per safe row that a retry writes and posts
nothing twice. A step not in this table is not safe.

| Step | Its write-once guard (file: message) | Posts to Slack | Retry |
|---|---|---|---|
| `weather` | `fno/weather/`: "a different record is already written" | no | **safe** |
| `forecasts_v4` | `fno/forecast_v4_rules/`: "a different row is already written"; "rows are never changed" | no | **safe** |
| `v4_release` | `fno/v4_pack/`: "already released" | its package's CLI sends (`fno/v4_pack/cli.py`) | **not safe** until the code round shows `v4 release` posts nothing |
| `forecasts_v4_pack` | `fno/forecast_v4_rules/`: "files written or already the same" | no | **safe** |
| `book1` | `fno/playbook/`: "already decided these inputs for {day}: refused"; "decision records are never rewritten" | no | **safe** (a retry after a decision is refused, never a second run) |
| `reviews` (E6) | none named | its package sends (the automatic pauses) | **not safe** |
| `card` (T1) | one delivery record per attempt (`fno/cards/deliveries.py`), no one-post proof | yes | **not safe** |
| `price_distribution` | `fno/price_distribution/`: "already recorded" | no | **safe** |
| `premium_ranges` | `fno/premium_ranges/`: "already issued" | no | **safe** |
| `recommend` | none named for the decide step | yes (its package sends) | **not safe** |
| the score steps (`price_distribution_scores`, `price_range_scores`, `premium_range_scores`) | each package's own write-once store (to be named in the code round) | no | **not safe** until each guard is named and tested |
| `price_ranges` | `fno/price_ranges/`: "already issued" | no | **safe** |
| `v4_deadline` | `fno/v4_pack/`: "REFUSED by the write-once store; nothing overwritten" | yes (the deadline alerts) | **not safe** |
| `candles` (A16b) | `fno/intraday/`: "a mark that already has one is refused (rows are written once)" | its package sends | **not safe** until its sends are shown to be failure alerts only |
| `close_read`, `close_recheck` | `fno/close_read/`: "close already read", "close already rechecked" | its package sends | **not safe** until the same |
| desk `exits`, `trade_marks` | O1 R2's table (event and fill IDs; the day's rows replaced) and `test_late_retries.py` | no | **safe** (owner question 3) |
| `lab open`, `lab close` | `fno/forecast_lab/`: one edition's write-once records | yes (the editions) | **not safe** |
| librarian commands | A9's store: "uploaded {uploaded}, already there {present}" (each session's file once) | on problems only | **not safe** until the same |
| A16's marks | `fno/intraday/`: one row per mark file, a mark that has one refused | on failure | safe inside the mark's window, with section 5's limits |

## 7. Retries are safe, and step 2b retires

- **Completed work is skipped:** the run log's `done` (O1 R2) decides which steps run, so a finished or refused step is
  never retried.
- **The day lock holds** (O1-day-lock): retries happen inside the living run, never as a second run.
- **Step 2b retires** in the same lane-1 change. CLAUDE.md's step 2b, its quiet-hours clause ("2b's once-only rerun
  holds until O14 replaces it") and AGENTS.md's line ("step 2b's once-only rerun holds until story O14 replaces it")
  are updated together, so no rule names a removed step (judge E m1). The run's last line no longer says "a rerun
  today retries it". A hand rerun after an escalation stays possible.

## 8. Escalation

- After the last allowed retry, or when the deadline rule, an open circuit or the Groww budget stops it early: **one**
  #fno-desk alert per step: "F&O <command> <day>: FAILED after <n> attempts (<last error class>); needs a human:
  <why it stopped>". Its reasons:
  - "5 retries used";
  - "the next wait would pass <HH:MM> (<limit>)";
  - "<source> refusing (circuit open)";
  - "the day's Groww retry budget is spent";
  - "stopped at its 600 s limit (it may have written already)".
  It never carries an error message's text, a value or a secret. An alert Slack refuses prints "alert NOT sent"
  (`ReportedAlerts`).
- **The run log records the attempts:** each attempt's start time and error class, in the public log (class names only,
  O1-status-only) and in the private full log. The run's last line names the escalated steps. T1e's card warning
  shows an escalated step as failed (unchanged).

## 9. Owner questions (the builder's recommendation; the orchestrator asks)

1. **Fills.** Owner, 24 Oct: "never retried", "no new trades that day"; the reason was a person choosing a rerun after
   the price moved. An automatic in-run retry has no person in it and prices at the 15:15 snapshot, but the fills start
   about 15:18 and `fills_by` is 15:20. **Recommendation: keep fills never retried** (some evidence: about 2 minutes
   leave at most 2 retries; a failed fills step may have written trades already, O1 R2's `StepInterrupted`).
2. **The school.** Never retried, never started after 15:25. **Recommendation: keep it** (reasoning only: its cutoff
   serves law 6's 15:30 fills refusal).
3. **Exits and marks.** Owner, 24 Oct: one immediate rerun ("once only"). Under O14 they are retried in the run, up to
   5 times, by 15:25, at the same 15:15 snapshot. **Recommendation: yes, O14 replaces "once only"** (some evidence: the
   late-retry tests show neither writes twice). A due stop-loss exit then waits minutes, not a day.

## 10. Acceptance criteria (each with good, bad, boundary and empty cases, and named plants)

1. **The policy.** Waits 30 s, 1, 2, 4, 8 minutes ±20% with a seeded jitter (G); never a sixth retry (B); attempt 5
   waits 8, not 16 minutes (Bd); zero retries means one attempt, then escalate (E); the short policy waits 5 and 10 s,
   then stops (G). Plants: no cap; a sixth retry; jitter outside ±20%.
2. **The deadline rule.**
   - A wait that would pass the retry deadline escalates with its limit named (B).
   - A wait ending exactly at the deadline minus the expected time is allowed (Bd).
   - The expected time comes from the previous session's log, else the fallback (G, E).
   - Plants: the later steps' limits ignored; **`book1` failing at 15:05 delays `fills` past `fills_by`** (it must
     not: the retry stops at 15:12 less its expected time); the expected time taken as zero.
3. **The circuit and a child's class.**
   - A Groww 429 waits at least 60 s (G).
   - A sign-in failure is never retried, in process or as a child (B).
   - NSE's cool-off inside the retry deadline escalates at once (Bd).
   - A child whose last line names no known class is not retried (E).
   - Plants: a 429 retried at the backoff; **after a child's sign-in failure another Groww child runs that day**.
4. **The Groww budget.** The 13th sign-in try by O14's Groww child retries in a day is refused and escalated (Bd: 12
   allowed); a retry in the same process starts no sign-in (G: GW1a's try count unchanged). Plant: a child retry not
   counted.
5. **A16's marks.**
   - A failing mark at 10:00 is retried at most twice, inside 10:02 (G).
   - The 14:30, 14:45, 15:00 and 15:15 marks are never retried (B).
   - A retry that would end past the mark's 120 s is not made (Bd).
   - A mark that succeeds sends nothing (E).
   - Plant: **a 15:00 mark retried during A4's window**.
6. **Safe retries (section 6's table).**
   - A finished or refused step is never retried (B).
   - Each safe row's retry writes and posts nothing twice (G, one test per row).
   - A command stopped at 600 s is never retried (Bd).
   - A step not in the table is not retried (E).
   - Plants: **a not-safe step marked safe** (`card`); `done` ignored.
7. **Escalation.**
   - One alert per escalated step, with the command, the attempts, the class and "needs a human" (G).
   - No error text or value in the alert or the public log (B).
   - A refused alert prints "alert NOT sent" (Bd).
   - A first-try success sends nothing (E).
   - Plants: an alert per attempt; the error text carried.
8. **Not wrapped.** A failing 3 pm part, A22 read, pack or snapshot is not started twice by O14, and O14 sends nothing
   for them. Plant: the 3 pm part wrapped.
9. **Step 2b retired.** CLAUDE.md step 2b and its quiet-hours clause, and AGENTS.md's line, are updated in the same
   change. The run's last line no longer says "a rerun today retries it". Test: those texts.
10. **Gates.** The full suite with the Slack token kept, ruff, ruff format, `check_imports`, `check_records`,
    `check_numbers` on `main`, no file over 350 lines. A rehearsal (REH1) day with one planted timeout per kind of
    caller, in a dry run, is the real output sample.

## 11. Gap list

- **The owner's words:**
  - exponential backoff: sections 3 and 10.1;
  - at most 5 retries: 10.1;
  - escalate to a human: section 8 and 10.7;
  - circuit breaker: section 5 and 10.3-10.5;
  - "always a maximum number of retries before we stop": sections 3.1, 5 and 6.
- **The orchestrator's points:**
  - scope: section 4;
  - the policy and the deadlines: sections 3 and 4;
  - GW1a's caps and the rate limits: section 5;
  - safety and step 2b: sections 6 and 7;
  - escalation: section 8;
  - owner questions: section 9.
- **Judge 682:**
  - SF1: section 3.1 and plant 10.2;
  - SF2: section 5 and plant 10.3;
  - m1: section 7 and 10.9;
  - m2: section 4 (named deadlines);
  - m3: section 6 (Slack posting is not safe).
- **Judge 683:**
  - finding 1: A22 not wrapped, times corrected;
  - finding 2: section 5 and 10.5;
  - finding 3: section 6 and 10.6;
  - finding 4: section 5 and 10.3-10.4;
  - minors: section 2 links, and the 3 pm parts row says O14 sends nothing.
- **Out of scope, with why:**
  - **GitHub workflows:** Actions has its own reruns.
  - **The other stories' loops (section 2)** are not rebuilt on `RetryPolicy`. A later story may move them, after a
    judge compares both.
  - **"fills_by 15:23"** is GW1 parts 5-6, waiting for the owner. O14 reads `fills_by` from the timetable.
  - **GW1a's 38-process worst case** is GW1a's estimate. If it changes, section 5's 12 sign-ins are recomputed from
    the same 150.
  - **A Claude routine that never starts** is the platform's, caught by O10's capture health and A4's overdue alerts.
  - **The steps marked not safe** become safe only by a later change that names their guard and a one-post test.

**Depends:** O1, O1-day-lock, O1 R2, GW1a, A4, A16, A16b, A22, FL1-1d, MS-P1j, T1, G10, G13d · **Size:** M
