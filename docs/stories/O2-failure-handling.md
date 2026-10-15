# Story O2: failure handling, end to end

**Repository:** trading · **Lane:** 1 (fills, exits, alerts, outside services) · **Size:** M ·
**Replaces:** the old O2 text in `docs/stories/O-operations.md`. REPLAN line 62: "keep, change, slice B: adds the
monitor heartbeat and 'alert NOT sent' paths". The owner chose to start it on 16 Oct 2026 (`docs/DESK_DECISIONS.md`):
text now, code after O1 merges.

**Description:** As the risk manager, I want every real way the daily run can fail tested end to end, in the real run
with fakes only at the outside services. Whatever breaks, the result must be the same: no new risk, the exits still
run (or are held with an alert), every alert reaches the owner (or is printed for the connector), and one book's
failure never changes another book's records.

## Context and why (each fact marked)

- **What exists, built and judged story by story (strong evidence: the code on `main` and O1's branch):**
  - C3's data gate refuses stale or missing data;
  - C4 refuses an order over a limit or past the drawdown brake;
  - E3 stops on a failed commit, and its rerun repeats nothing (E2b's `PendingCommitter`);
  - E2c's Drive download stops the run (`PrivateFilesUnavailable`), and the next session blocks new entries for the
    books whose exits were not reviewed (`DailyRun._unreviewed`);
  - O1 runs every step in one thread, with one alert path. `ReportedAlerts` prints each unsent alert, and every
    child's "alert NOT sent" lines are relayed;
  - O8 reports a session with no run log as "never ran".
- **What nobody has proven:** that these hold together on a bad day, when one outage hits several steps at once. No
  test drives the whole day through a real outage (strong evidence: `tests/timetable` and `tests/daily` test one part
  each, with fakes for the rest).
- **The heartbeat (said plainly):**
  - REPLAN's "monitor heartbeat" is the live monitor's (layer 7, design 4.2 and 6.5: "monitor silent" after 30
    minutes). That belongs to LM1 (`REPLAN_new_stories.md`, "LM1 Position monitor ... heartbeat and 'monitor silent'
    checker"), which is not built.
  - Under one builder per function, O2 builds no second heartbeat. Its suite gains the monitor-silent case when LM1
    lands (Known limits).
  - The daily routine's own "never started" signal already exists: no run log, then O8's "never ran" that evening,
    then the next session's block on new entries. O2 proves that chain.
- **Design 9's rows** (`docs/DESK_DESIGN.md` section 9), and where each stands today:
  - data missing or stale: C3, tested here;
  - a limit hit, or the drawdown brake hit: C4, tested here;
  - a broken protection: E4c (merged, 4d2dc961), tested here;
  - "a role fails to report", "judge or AI unavailable": these need the AI books' trading (F5/F6, slice E), which is
    not built. They are out until then (Known limits);
  - "paper results outside the plan": E6's scorecard pauses, outside the daily run.
- **No new alert class** (orchestrator, 16 Oct): every alert is one the code already sends, in design 6.5's classes.

## Scope

In: one end-to-end suite, `tests/e2e/`, that drives O1's real `DayRunner` (E3's `DailyRun` and every O1 step) over
fixture days. Only the outside services are fakes, each behind its existing interface: the Drive store, the Slack
sender, the quote sources (the child commands' scripts), git's remote, and the clock. It has one module per failure
family:

| Family | The day's injected failure | What must happen (from the code that owns it) |
|---|---|---|
| Drive outage | (a) at the run's download; (b) at an account write during fills; (c) the recorder's raw quote file not saved | (a) the run stops with E3's one alert, no step runs, and the next session blocks new entries for every book while its exits run; (b) that write's entries fail closed with an alert, while other books and every exit go on; (c) the canonical is `none`, so there is no pack, no new trade and the exits are held with C3's alert |
| Slack outage | the sender refuses every post (token missing, HTTP error) | nothing changes in the records. Every alert of the day (the run's own and each child's) is printed once as "alert NOT sent ... \| text", and their count equals the alerts the same day sends with Slack up |
| Groww or NSE failure | the NIFTY part exits 1; NSE exits 1; the 15:15 capture fails twice | NIFTY: no pack, every book "no decision (late)", exits held with an alert. NSE: the desk is unchanged (NSE is recorded only). Capture: "no valid execution snapshot", no fills, exits held with an alert |
| Routine never starts | session D has no run log | O8's desk check gives D `missed (never ran)`; the run on D+1 blocks new entries for every book (`NO_LOG`), runs its exits, and alerts |
| Partial run and rerun | the process is killed after each step k in turn (every step of `DAILY_RUN_STEPS`, 13 today), then rerun at the same clock | the final run log, the committed files and the private records are byte-identical (SHA-256) to an uninterrupted day. A rerun after the 15:12 deadline follows E3's late rule (every book late) and nothing else |
| Data and limits (design 9) | a stale snapshot; an order over a C4 limit; the drawdown brake hit | no new trade for that order or book, stale prices never used as a fill, the alert names the check, and open trades go on under their own exits |
| Broken protection (E4c) | at the entry snapshot: a protective leg cannot be bought; a protective leg can be bought but not sold back; a short leg cannot be sold | nothing fills and the trade is `not_opened` with E4c's reason code (`protection_not_buyable`, `protection_not_sellable`, `short_leg_not_sellable`), one desk event, no fill or ledger row, the account unchanged, and E4c's one alert ("... not opened: <reason code> (<contract>, <units> units): information, no action"). The position is never half-hedged. Neither the record nor the alert holds a quote figure |
| One book's failure | Book 2's orders refused; its account write refused; its exit review raising | Book 1's decision, fills, exits and private records are byte-identical to a no-failure day |

Every case also checks: each alert is named and sent once (or printed once when unsent); every due exit is reviewed
or held with an alert, never silently skipped; and the run ends on its one line (`day done with problems: ...`, or
E3's stop line plus "no card today").

Out:
- new failure behaviour, unless a case shows that a judged rule is not met. Each such gap is fixed in the story that
  owns the code and named in the claims, not patched in O2;
- LM1's heartbeat (it waits for LM1);
- the AI books' cases (F5/F6, slice E);
- design 6.5's first-line rule (a separate story, below).

## Acceptance criteria

1. **Each family's outcome is exactly the owner code's rule.** One test per row and case above; each asserts the
   records, the alert text and the end line.
2. **Exits always run or are held with an alert.** In every case, each exit due that day is in the run log's `exits`
   step as reviewed, or as `waiting` with the gate's alert. When the run stopped before `exits`, the next session
   blocks new entries for that book.
3. **No alert is lost.** In every case run twice, once with Slack up and once down, the multiset of alert texts is
   the same, and every unsent one is printed exactly once.
4. **A rerun repeats nothing.** Kill after each step, then rerun: the final state is byte-identical to an uninterrupted
   day (one case per step), or follows E3's documented late rule.
5. **Books are isolated.** Book 1's records hash the same with and without each Book 2 failure.
6. **Fakes only at the edges.** The suite builds the run through `fno/daily/wiring.py`, replacing only the outside
   services: a test fails if any other part is replaced.
7. **Real failure, real fix.** Every gap the suite finds is reported in the claims, with its file and line and the
   story that owns the fix. None is hidden by a test that expects the wrong outcome.
8. **Engineering.** No file over 350 lines. The suite runs under `-n auto`, never touches the network, and finishes
   in under a minute (some evidence: today's daily tests take about 6 s).

## Gap list

| Requirement (source) | Criterion or reason out |
|---|---|
| Every design 9 row (old O2) | 1 (data, limits, brake, broken protection); the AI rows after F5/F6 |
| Exits still run (old O2 criterion 2) | 2 |
| One book never changes another (old O2 criterion 3, design 13.5) | 5 |
| "alert NOT sent" paths (REPLAN 62) | 3 |
| Monitor heartbeat (REPLAN 62) | out: LM1 owns it (one builder per function); case added with LM1 |
| Drive, Slack, Groww/NSE outages, a routine that never starts, a partial run (orchestrator, 16 Oct) | 1, 3, 4 |
| No new alert classes (orchestrator) | Scope: only existing alerts |

## Known limits (one line each)

- The routine that never starts is reported at O8's 17:51 run (cron, can be late); that session's decision is lost
  anyway.
- The monitor-silent case waits for LM1; the AI-book cases for F5/F6 (slice E).
- Design 6.5's first-line rule ("says what to do, or 'information, no action'") is not met by today's run alerts; a
  separate small story fixes it after O1 merges (orchestrator, 16 Oct), and O2's suite then checks it.
- The fakes cannot reproduce a real Groww or Drive error message; the cases use each adapter's documented exception.

## Test plan

`tests/e2e/` with the fixtures of `tests/timetable` and `tests/daily`. Every case is checked against its no-failure
twin, and each family's key assertion is broken once on purpose.

**Judge verifies:** runs the suite under `-n auto`; reads three failure transcripts (Drive at download, Slack down,
kill after `fills` and rerun); plants one regression (for example, exits skipped after a stop) and sees a test fail.

**Depends:** O1 (merge), E2c, E4c, C3, C4, E3, O8 (merged); LM1 for its case · **Status:** story text
revision 2 (orchestrator, 16 Oct: E4c in scope; the first-line rule a separate story) for judge D
(`reviews/claude/response_203_o2-failure-handling.md`)
