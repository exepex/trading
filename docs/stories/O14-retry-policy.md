# Story O14: one retry policy for failed commands (exponential backoff, at most 5 retries, then escalate)

**Lane 1, two judges** (it decides whether a step that writes records runs again, and it calls outside services:
Groww, NSE, Drive, Slack). **Builder:** session_016CU8KFuEEtWAM7ZNnFcKxv (O1's owner from 25 Oct; O1's first builder
is out of reach). **Status:** story text, for the judges. This file links the stories it touches (O1, O1-day-lock,
GW1a, A4, A16, A22, FL1-1d, MS-P1j) rather than restating them.

## 1. The owner's decision

Owner, 25 Oct 2026 (`docs/DESK_DECISIONS.md`, "Failed commands: automatic retry with exponential backoff, at most 5
retries, then escalate"): "if a command fails then let's add a retry mechanism to add an exponential backoff policy
with a maximum 5 retries. if it still fails after 5 retries then we highlight and escalate to human or operator. but
what adding an exponential backoff policy is important like we do in circuit-breaker design patterns or the same
mechanism we use in kafka or publisher patterns with always a maximum number of retries before we stop."

The row replaces the open question of rerunning once or always. Until O14 is live, a human may rerun a failed scheduled
command by hand. Everything below that is not the owner's words is the builder's design, marked (reasoning only)
where no data backs it.

## 2. What exists today (facts, read on `main` at d95d5ea8f)

| Where | Today's retry | Its limit |
|---|---|---|
| Daily run, desk steps (`fno/desk/daily_run.py`, O1 R2) | none in the run; a failed `exits` or `trade_marks` is retried by the routine's one immediate rerun (CLAUDE.md step 2b); `fills` is final (owner, 24 Oct) | the run's own day only |
| Daily run, command steps (`fno/daily/steps.py` `CommandStep`, `Alerted`) | none: a failure is recorded and alerted once, the run goes on | `COMMAND_LIMIT_SECONDS` 600 s per command |
| 3 pm, indices and `v4` quote parts (A4, A4c, A4e; `fno/quotes/recorder.py`) | the recorder's own loop: an incomplete capture is retried with a 60 s gap until its window ends | 15:10 (3 pm), 15:13 (indices), 14:40 (`v4`) |
| E3's pack (`DailyRun._pack`) | rebuilt every 30 s while the canonical snapshot is missing | `pack_wait_until` 15:10 |
| Execution snapshot (`DeskSteps.take_snapshot`) | one common retry for all books | inside 15:15-`fills_by` |
| Groww sign-in (GW1a, `fno/providers/groww_sign_in.py`) | +5 then +10 minutes, at most 3 tries per process and day, one alert | Groww's 150 sign-ins per 24 h |
| Groww 429 (GW1a, `groww_rate_guard.py`) | every call paused for 60 s after a 429 | per process |
| NSE and its archives (`fno/http_pacing.py`) | 1 s spacing per host; two refusals (403/429) pause the host 15 minutes | per process |
| A16, A22, the editions, the librarian | each command's own windows; no retry of the whole command | their windows (section 4) |

So there are already four retry loops with their own limits, and no shared rule for a whole failed command.

## 3. The design (reasoning only; one interface, its strategies, wired in composition roots)

- **`RetryPolicy`** (`fno/retry/policy.py`, new package): `next_wait(attempt, now, deadline) -> timedelta | None`.
  None means stop. The one strategy now is `ExponentialBackoff(base, factor=2, cap, retries=5, jitter)`: wait
  `min(cap, base * 2**(attempt-1))`, then multiply by a jitter drawn from [0.8, 1.2]. The jitter source is injected, so
  tests are exact. A second strategy (for example a fixed gap) is added only when a caller needs it (CLAUDE.md: no
  pattern without a second use).
- **The deadline rule.** A retry is made only if `now + wait + the step's expected run time` is at or before the
  step's deadline. If not, the policy stops at once and escalates ("would pass its deadline"). This is never a sixth
  try, and never a late one.
- **`CircuitBreaker`** (`fno/retry/circuit.py`): one per outside source (Groww, NSE, Drive, Slack), shared by every
  caller in the process. An error the source's own guard raises opens the circuit; an open circuit makes the policy
  stop and escalate rather than wait blindly (section 5).
- **`RetryRunner`** (`fno/retry/runner.py`) runs one attempt at a time:
  - it classifies the outcome as done, retryable, final, or circuit open;
  - it waits through the run's `Waiter`, so the 3 pm parts are still serviced while it waits (O1 criterion 4a);
  - it records each attempt, and escalates once.
- **Classification is the step's own, never guessed.** Each caller declares which error classes are retryable.
  Default: a timeout, a connection error or a 5xx is retryable. A refusal ("nothing written", a cutoff passed), an
  `AccountWriteRefused`, a `CommitFailed` or `GitFailed` (decision 44's run stop) and any error of the run's own
  rules are final.
- **Wiring:** the policy settings live in `config.yaml` under `retry`. Each composition root (`fno/daily/wiring.py`,
  `fno/intraday/feed_wiring.py`, the pre-open, editions and librarian wiring) builds its `RetryRunner` with the
  step's deadline from the step's own timetable, never a copy.

**The numbers (reasoning only; the judges and the owner may change them):** base 30 s, factor 2, cap 8 minutes, 5
retries, jitter ±20%. The waits are 30 s, 1, 2, 4 and 8 minutes, at most 15.5 minutes plus the jitter. A step with less
time before its deadline gets fewer retries, by the deadline rule. The pre-open and A16 windows are minutes long, so
they use base 5 s and cap 30 s (5, 10, 20, 30, 30 s).

## 4. Every caller, its deadline and how it plugs in

| Caller | Deadline (its own source) | Plugs in |
|---|---|---|
| Daily run command steps (`weather`, `forecasts_v4`, `v4_release`, `forecasts_v4_pack`, `book1`, `reviews`, `card`, `price_distribution`, `premium_ranges`, `recommend`, the score steps, `candles`, `close_read`, `close_recheck`, `v4_deadline`) | each step's own: 14:30 for the weather and v4 forecasts (CLAUDE.md), 14:45 for the release, 15:10 for the v4 pack rows, 15:30 for `premium_ranges`, the end of the run otherwise | `CommandStep` runs its command through the runner. Only steps marked safe to repeat (section 6) are retried |
| Daily run desk steps (O1 R2's `_run_step`) | the run itself for `exits` and `trade_marks`; `fills_by` for `fills` (owner question 1) | `_run_step` calls the runner for the steps in `RETRIED_ON_RERUN`. The same-day rerun then finds them done, and CLAUDE.md step 2b is removed when O14 is live |
| 3 pm, indices and `v4` quote parts (A4, A4c, A4e) | 15:10, 15:13, 14:40 | not wrapped: the recorder's own 60 s loop already retries until its window ends, and an outer retry would start a second capture. O14 only counts its attempts in the escalation line |
| E3's pack and execution snapshot | 15:10; `fills_by` | not wrapped: each has its own retry inside its window (section 2) |
| The school (MS-P1j) | never after 15:25 (`SLOT_LAST_START`) | owner question 2 |
| A16's intraday marks (`fno/intraday/`) | each mark's 120 s window (A16 story, "Slots") | the mark's call through the runner with the short policy; past the window the slot is `missed`, never taken late |
| A22's pre-open capture | GIFT Nifty 08:40-08:44:59, the F&O list 09:08:30-09:10:59, the candle 09:10:00-09:10:59 (CLAUDE.md "Pre-open capture") | each read through the runner with the short policy, inside its own window |
| The editions (FL1-1d `lab open`, `lab close`) and the evening's librarian commands | `lab open` before 09:15 (it posts nothing at or after 09:15); `lab close` before the next morning's edition | each command's entry point calls the runner. The routine's CLAUDE.md lines are unchanged: the retry is inside the command |
| GitHub workflows (`.github/workflows/*.yml`) | each job's own | out of scope: Actions has its own reruns, and none of them is a routine command |

## 5. The circuit breaker and Groww's limits

- **A refusing or rate-limited source is never retried blindly.**
  - `GrowwRateLimited` or `GrowwRateLimitPaused` (GW1a rule 4) opens Groww's circuit for at least the 60 s pause. The
    next wait is the larger of the backoff and the pause.
  - `SourceCoolingOff` (NSE, `http_pacing.py`) opens NSE's circuit for the 15-minute cool-off. A step whose deadline
    falls inside the cool-off escalates at once.
  - `GrowwSignInPaused` and a failed sign-in open Groww's circuit for the rest of the process's day: no retry may
    start a new sign-in (GW1a rule 1).
- **No extra Groww load (the budget, from GW1a's worst case).** GW1a's worst case is 38 processes x 3 sign-ins = 114,
  under Groww's 150 a day. That headroom is 36 sign-ins, so 12 more processes at 3 each.
  - A retry runs in the same process wherever it can, so it reuses that process's signed-in client and its sign-in
    budget. That holds for every caller in section 4 except the daily run's Groww command steps, whose commands run
    as child processes.
  - For those, a retry counts against a day budget of **at most 12 extra Groww child processes**, kept in the run
    log. When it is spent, the policy escalates.
  - A Groww sign-in failure is never retried by O14 (GW1a's own back-off handles it).
- **Rate limits.** A retry adds no call beyond what the step's first attempt would have made. A4's paced loop and
  GW1a's pause stay the only Groww pacing. O14 never shortens a wait a guard imposes.

## 6. Retries are safe

- **Completed work is skipped.** The run log's `done` (O1 R2) decides which steps run, so a step that finished is never
  retried, and a refused step is final.
- **Each retried step's own records are write-once** (its existing guard: "already recorded", `PackStore`'s same-bytes
  rule, the fill and event IDs of O1 R2's table). A step without such a guard is marked not safe and is never retried.
  The table of every step, safe or not, is built with the code and checked by the judges.
- **The day lock holds** (O1-day-lock). Retries happen inside the living run, never as a second run, so "another daily
  run of <day> is running" still applies.
- **Today's step-2b rerun becomes this policy.** The exits and marks retries move into the run. The routine's step 2b
  line ("a rerun today retries it") is removed, a rule-document change in the same lane-1 change. A human rerun by hand
  stays possible after an escalation.
- **The card's posting** (T1) writes one delivery record per attempt (`fno/cards/deliveries.py`). It is not shown
  here that a second attempt cannot post a second card, so `card` starts as **not safe**. It becomes safe only once
  the safe-steps table shows a test that a retry posts once.

## 7. Escalation

- After the last allowed retry, or when the deadline rule or an open circuit stops early: **one** #fno-desk alert:
  "F&O <command> <day>: FAILED after <n> attempts (<last error class>); needs a human: <why it stopped>". The reason
  is one of "5 retries used", "the next wait would pass its deadline <HH:MM>", "<source> refusing (circuit open)" or
  "the day's Groww retry budget is spent". It never carries an error message's text, a value or a secret. An "alert
  NOT sent" line is printed, as for every alert (`ReportedAlerts`).
- **The run log records the attempts.** For each: start time and the error class, in the public log (class names
  only, O1-status-only) and the private full log. The run's last line names the escalated steps.
- **The card's warning** (owner, 24 Oct, T1e) shows an escalated step as a failed step. Unchanged.

## 8. Owner questions (the builder's recommendation for each; the orchestrator asks the owner)

1. **The fills step.** Owner, 24 Oct: "never retried", "no new trades that day". The reason was a person choosing a
   rerun after the price moved (judges 569.2 and 570.2). An automatic retry inside the run has no person in it, and
   it prices at the same 15:15 snapshot. But the room is small: the fills start at about 15:18 on real days, and
   `fills_by` is 15:20. **Recommendation: keep fills never retried** (some evidence: about 2 minutes leave at most 2
   retries; a failed fills step may have written some trades already, as O1 R2's `StepInterrupted` shows, and the
   gain is rare).
2. **The school step.** Never retried, never started after 15:25. **Recommendation: keep it** (reasoning only: its
   15:25 cutoff exists for law 6's 15:30 fills refusal, and a retried school run that seals late is refused anyway).
3. **Exits and marks.** Owner, 24 Oct: one immediate rerun ("once only"). Under O14 they would be retried in the run,
   up to 5 times, with backoff, then escalated. Each retry uses the same 15:15 snapshot, so there is no hindsight.
   **Recommendation: yes, O14 replaces "once only" for these two** (some evidence: O1 R2 and its follow-up show both
   steps write nothing twice on a retry after 15:20; tests `test_late_retries.py`). A due stop-loss exit then waits
   minutes, not a day.

## 9. Acceptance criteria (each with good, bad, boundary and empty cases, and a named plant)

1. **The policy.** The waits are 30 s, 1, 2, 4, 8 minutes ±20%, with a seeded jitter (G). Never a sixth retry (B: a
   sixth attempt is refused). The cap holds (Bd: attempt 5 waits 8, not 16 minutes). Zero retries configured means one
   attempt, then escalate (E). Plants: no cap; a sixth retry; jitter outside ±20%.
2. **The deadline rule.** A wait that would pass the deadline stops and escalates with that reason (B). A wait that
   ends exactly at the deadline minus the expected run time is allowed (Bd). Plant: the check dropped.
3. **The circuit.**
   - A Groww 429 waits at least 60 s (G).
   - A sign-in failure is never retried (B).
   - NSE's cool-off inside the deadline escalates at once (Bd).
   - A source with no errors stays closed (E).
   - Plants: 429 retried at the backoff; sign-in retried.
4. **The Groww budget.** The 13th extra Groww child process in a day is refused and escalated (Bd: 12 run). A retry in
   the same process starts no sign-in (G: the guard's try count is unchanged). Plant: a retry as a new process
   uncounted.
5. **Safe retries.**
   - A finished or refused step is never retried (B).
   - A step marked not safe is never retried (B).
   - A retried safe step writes nothing twice, shown for one safe command step and for `exits` (G).
   - The day lock is held across a retry (Bd: a second run during a wait does nothing).
   - Plant: `done` ignored.
6. **Escalation.**
   - One alert per escalated step, with the command, the attempts, the class and "needs a human" (G).
   - No error text or value in the alert or the public log (B).
   - An alert Slack refuses prints "alert NOT sent" (Bd).
   - A step that succeeds on its first try sends nothing (E).
   - Plants: a second alert; the error text carried.
7. **The callers.** Each row of section 4 marked "plugs in" goes through the runner (a test per caller). The rows
   marked "not wrapped" make no outer retry (a test that a failing quote part is not started twice). Plant: the 3 pm
   part wrapped.
8. **Step 2b retired.** CLAUDE.md step 2b is removed in the same change, and the run's last line no longer says "a
   rerun today retries it". Test: the line's text.
9. **Gates.** The full suite with the Slack token kept, ruff, ruff format, `check_imports`, `check_records`,
   `check_numbers` on `main`, no file over 350 lines. A rehearsal (REH1) day with one planted timeout per kind of
   caller, in a dry run, is the real output sample.

## 10. Gap list

- **The owner's words:**
  - exponential backoff (sections 3 and 9, criterion 1);
  - at most 5 retries (criterion 1);
  - escalate to a human after them (section 7, criterion 6);
  - circuit-breaker behaviour (section 5, criterion 3);
  - "always a maximum number of retries before we stop" (criteria 1, 2 and 4).
- **The orchestrator's points:**
  - 1, scope and plug-in: section 4, criterion 7;
  - 2, the policy and the deadlines: sections 3-4, criteria 1-2;
  - 3, GW1a's caps, the 429 pause and the rate limits: section 5, criteria 3-4;
  - 4, safety, completed work skipped, the day lock, step 2b: section 6, criteria 5 and 8;
  - 5, escalation and the run log: section 7, criterion 6;
  - 6, the owner questions: section 8.
- **Out of scope, with why:**
  - **GitHub workflows** have their own reruns, and none is a routine command.
  - **A4's recorder loop is not rebuilt** on the new policy: its 60 s gap and windows are tested and live. A
    later story may move it onto `RetryPolicy` once a judge has compared both.
  - **The orchestrator's "fills_by 15:23"** is GW1 parts 5-6, waiting for the owner. O14 reads `fills_by` from the
    timetable, so either value works.
  - **The worst-case count of processes** (GW1a's 38) is GW1a's estimate. If GW1 parts 5-6 change it, the 12-process
    budget is recomputed from the same 150-a-day limit.
  - **Retrying a whole Claude routine session** (the 14:05, 08:36, 08:38 or 19:53 routine failing to start) is the
    platform's, not a command's. A routine that never starts is caught by O10's capture health and A4's overdue
    alerts.

**Depends:** O1, O1-day-lock, O1 R2, GW1a, A4, A16, A22, FL1-1d, MS-P1j, T1 · **Size:** M (a new package and one
plug-in per caller)
