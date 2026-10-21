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
| Drive outage | (a) at the run's download; (b) at an account write during fills; (c) the recorder's raw quote file not saved | (a) the 3 pm quote parts (NSE included) start before the download (O1, judge 178), so they still record, are waited for and commit their own files; the desk stops before any step with E3's one alert and no card; the next session blocks new entries for every book (`NO_LOG`) while its exits run; (b) `PrivateFilesUnavailable` is a `CommitFailed` (E2c, `fno/desk/drive_sync.py`), so the run stops at `fills`: no exits that day, E3's stop alert naming "exits not reviewed today", and the next session blocks new entries for every book (`BEFORE_EXITS`). Only `AccountWriteRefused` and `OrdersRefused` fail one book closed and let the run go on; that case is tested in the book family below. A change to this rule belongs to E2c, not O2; (c) the canonical is `none`, so there is no pack, no new trade and the exits are held with C3's alert |
| Slack outage | the sender refuses every post (token missing, HTTP error) | nothing changes in the records. Every alert of the day (the run's own and each child's) is printed once as "alert NOT sent ... \| text", and their count equals the alerts the same day sends with Slack up |
| Groww or NSE failure | the NIFTY part exits 1; NSE exits 1; the 15:15 capture fails twice | NIFTY: no pack, every book "no decision (late)", exits held with an alert. NSE: the desk is unchanged (NSE is recorded only). Capture: "no valid execution snapshot", no fills, exits held with an alert |
| Routine never starts | session D has no run log | O8's desk check gives D `missed (never ran)`; the run on D+1 blocks new entries for every book (`NO_LOG`, whose wording "stopped before any step" also covers a run that never began), runs its exits, and alerts |
| Partial run and rerun | the process is killed after each step k in turn (every step of `DAILY_RUN_STEPS`, the count read from the tuple), and also between a step's record and its commit; then rerun at the same clock | no step runs twice. Kills from `quotes` up to `exits`: the rerun records `quotes_done` failed (`NOT_IN_THIS_RUN`) and the dead run's part files stay uncommitted (O1's decision, judge 178 note 4); everything else is byte-identical (SHA-256) to an uninterrupted day. Kills after `quotes_done`: byte-identical. A kill between record and commit: the rerun commits that step's files as recorded (E2b's `PendingCommitter`, or the next commit carries the log) and repeats nothing. A rerun after the 15:12 deadline follows E3's late rule (every book late) and nothing else |
| Hung git call | a pull, commit or push that never returns, with a real git and a hanging hook: once in a desk step's commit, once in a quote part's, once in a push | every git call of the run (`Git`) runs in its own process group and is stopped at one hard limit (`GIT_CALL_LIMIT_SECONDS`, 120 s, the whole-history fetch's limit): the whole group is killed (the hook too, as `fno/daily/processes.py` does) and waited for. Then the lock files (`.git/**/*.lock`) that this stopped call created are removed: they were absent before the call, and after the kill no process of the run holds them, because the run makes one git call at a time and its child commands never run git while one is open. A lock that was already there before the call is never removed: git's own "File exists" error makes that call fail at once, as a `GitError` naming the lock and the hand fix ("no git running? remove <path>"). A stopped call is a `GitError`, so a `CommitFailed`: in a desk step, E3's stop alert naming the step (before `exits`: "exits not reviewed today", and the next session blocks new entries); in a quote part, O1's "NOT committed" alert, while the desk goes on and its next commit succeeds; a stopped push is "push not confirmed" (it may have reached the remote), marked unpushed, so E3's rerun recovery handles it. The one behaviour O2 adds (orchestrator, 16 Oct): without it a hang never reaches E3's judged rule "a failed commit stops the run with one alert", and it holds the 15:15 exits |
| Hung command | a step's child command never ends, once while it holds a git lock (Book 1's `desk book1` commits its own decision) | stopped at O1's 600 s limit with its whole process group; the lock files created while it ran are removed by the same rule as a stopped git call (absent at its start, and nothing else runs git meanwhile); the step `failed`, one alert, the day goes on and the next commit succeeds |
| Data and limits (design 9) | a stale snapshot; an order over a C4 limit; the drawdown brake hit | no new trade for that order or book, stale prices never used as a fill, the alert names the check, and open trades go on under their own exits |
| Broken protection (E4c) | at the entry snapshot: a protective leg cannot be bought; a protective leg can be bought but not sold back; a short leg cannot be sold | nothing fills and the trade is `not_opened` with E4c's reason code (`protection_not_buyable`, `protection_not_sellable`, `short_leg_not_sellable`), one desk event, no fill or ledger row, the account unchanged, and E4c's one alert ("... not opened: <reason code> (<contract>, <units> units): information, no action"). The position is never half-hedged. Neither the record nor the alert holds a quote figure |
| One account's failure (judge 204 add. 4) | the second account is Book 1's shadow (a registered research version in the fixture checkout), never a test-only book. Today's code gives a shadow decisions, records, an opened account and marks, and nothing else (no shadow order, fill or exit exists: E8 part 1b's). So, through fixture data and outside seams only: (a) the shadow's account file served corrupt by the Drive fake at the `trade_marks` step; (b) Book 1's orders refused by its own replay (`OrdersRefused`, a fixture record whose replay differs); (c) a shadow-side failure inside Book 1's decision (the shadow's account file corrupt when `desk book1` reads it) | (a) only the shadow's marking fails, with one alert; Book 1's marks, records and private files are byte-identical to the twin day; (b) Book 1 opens nothing that day, with one alert, and the shadow's records and account are byte-identical; (c) today D2 has no guard around the shadow loop (`fno/playbook/evaluate.py` 52-59), so the failure aborts Book 1's whole decision: a gap, reported to D2's owner, and the case asserts the fixed rule once that fix lands (until then it is `xfail` with the gap named, never a test that expects the wrong outcome). A refusal of only the shadow's orders cannot be produced: shadows have no orders, so that case waits for E8 part 1b, and Book 2's isolation case for F5/F6 |

Every case also checks: each alert is named and sent once (or printed once when unsent); every due exit is reviewed
or held with an alert, never silently skipped; and the run ends on its one line (`day done with problems: ...`, or
E3's stop line plus "no card today").

Out:
- new failure behaviour, unless a case shows that a judged rule is not met. Each such gap is fixed in the story that
  owns the code and named in the claims, not patched in O2. The one exception, given to O2 by the orchestrator (16 Oct):
  the hard limit on every git call (`fno/desk/git_sync.py`, `Git`), with its test row above;
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
4. **A rerun repeats nothing.** Kill after each step (and once between a record and its commit), then rerun: no step
   runs twice; the final state is byte-identical to an uninterrupted day except the named `quotes_done` outcome for
   kills from `quotes` to `exits`, or follows E3's documented late rule.
5. **Accounts are isolated, both ways.** Book 1's records and files hash the same with and without each shadow
   failure, and the shadow's with and without each Book 1 failure (the realistic risk while Book 1 trades alone).
6. **Fakes only at the edges.** The suite builds the run through `fno/daily/wiring.py`, replacing only the outside
   services: a test fails if any other part is replaced. Trades come from fixture data in the fresh checkout only (a
   `paper` fixture strategy with its committed evidence, a registered research shadow, a fixture market that fires,
   NSE's F&O file for C4's listing check served by the NSE archive fake), never from replaced code; a test proves the
   source tree's `playbook/`, `playbook/registry.csv` and `journal/versions.csv` are byte-unchanged after the suite.
7. **Real failure, real fix.** Every gap the suite finds is reported in the claims, with its file and line and the
   story that owns the fix. None is hidden by a test that expects the wrong outcome.
8. **Engineering.** No file over 350 lines. The suite runs under `-n auto`, never touches the network, and finishes
   in under two minutes on four cores (some evidence: one fixture day takes 6-7 s through the real wiring, measured
   16 Oct; revision 6 relaxes "a minute", which that measurement shows is not met by about 35 fixture days).

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

## Scope split (21 Oct, orchestrator; owner's phase-1 freeze)

- **O2, merged** (main cdd59db6, judge 412): the git limits, the e2e harness, the outages with Slack up and down,
  never-starts, and the G1 fix.
- **O2, phase 1 still:** the gaps O2 found (F1, G4, and the double-alert regression after A4) are fixed as O1 changes,
  each judged on its own. Round 4a/4b's kill-and-rerun and hang rows, on `story/o2-failure-handling`, join main with
  those fixes, their strict xfails turned into real assertions.
- **O2b, paused** (until the owner's phase-1 review; due before the first paper approval): the trade rows (exits held,
  E4c, data and limits, Drive (b), the shadow cases (a)-(c) with (c) as a strict xfail on the D2 gap) and the
  source-tree unchanged test. Revision 6's text stays their contract.


- The routine that never starts is reported at O8's 17:51 run (cron, can be late); that session's decision is lost
  anyway.
- The monitor-silent case waits for LM1; the AI-book cases for F5/F6 (slice E).
- Design 6.5's first-line rule ("says what to do, or 'information, no action'") is not met by today's run alerts; a
  separate small story fixes it after O1 merges (orchestrator, 16 Oct), and O2's suite then checks it.
- The fakes cannot reproduce a real Groww or Drive error message; the cases use each adapter's documented exception.
- A dead run's quote part files stay uncommitted on its rerun (O1's decision); the suite names it, never hides it.
- Judge 204 note B is closed: E4c's own print was removed in O1 with its owner's agreement
  (`fno/desk/daily_steps.py` 191), and `tests/timetable/test_entry_check_alert.py` asserts exactly one unsent line;
  criterion 3 checks it again over the whole day.
- Nothing trades in production today (strong evidence: `playbook/registry.csv` holds no `paper` strategy, only
  `b0-monthly-sc` v1 as `research`, dated 16 Oct; `fno playbook check` says "approved for paper: none"), so the trade
  rows test a path that is not live yet. Shadow fills and exits wait for E8 part 1b, Book 2's isolation for F5/F6.
- Steps that join `DAILY_RUN_STEPS` later (F1t's `ai_fire` and `ai_collect`, G13, A16b's catch-up, Book 2's rule
  default) are covered by the kill-and-rerun cases, which read the tuple, and by `Alerted`'s one-alert rule; each
  story's own failure cases come with it. O10 (capture-job freshness) covers only jobs outside `daily run` and sends no
  alert for a run step (agreed with its builder, 16 Oct); the run log stays the one record of each step.

## Test plan

`tests/e2e/` with the fixtures of `tests/timetable` and `tests/daily`. Every case is checked against its no-failure
twin, and each family's key assertion is broken once on purpose.

**Judge verifies:** runs the suite under `-n auto`; reads three failure transcripts (Drive at download, Slack down,
kill after `fills` and rerun); plants one regression (for example, exits skipped after a stop) and sees a test fail.

**Depends:** O1 (merged 1d01fd08), E2c, E4c, C3, C4, E3, O8 (merged); LM1 for its case · **Status:** story text
revision 6 for judge D (judge 204 add. 4: the shadow replaces `book_test`, fixture data only, isolation both ways,
the named limit; criterion 8's time measured); revision 5 passed (judge 204 add. 3): the hard git limit and the hung-command row, row (a) after O1's early quote parts, `book_test`
in criterion 5, note B closed (revision 3 passed, judge 204 addendum 1)
(`reviews/claude/response_203_o2-failure-handling.md`)
