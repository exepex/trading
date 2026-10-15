# Story O1: one daily run (weather, v4 forecasts, quotes, data checks, desk, card)

**Repository:** trading · **Lane:** 1 (a schedule, a routine prompt, fills and Slack) · **Size:** M ·
**Replaces:** the old O1 text in `docs/stories/O-operations.md` (REPLAN line 61: "**change**, slice B: one daily run:
data checks, forecasts, weather, desk, card; fired from Actions as O6 does").

**Description:** As the owner, I want one command, started once a day by one schedule, to run the whole desk day in
order and leave one log of what each step did, so that the desk runs every session without me, and a step that fails
is seen, never silently skipped, and never stops the exits.

## Context and why (each fact marked)

- **Nothing runs the desk today** (strong evidence: no workflow or routine calls `fno desk run`; `grep` of
  `.github/workflows/` and CLAUDE.md). E3's `DailyRun` (`fno/desk/daily_run.py`) is built and wired
  (`fno/desk/daily_wiring.py`); Book 1's command adds the orders (`fno/books/book1_cli.py`, `add_run_command`).
- **Nothing runs the weather or the v4 forecasts live** (strong evidence: no caller of `fno weather capture` or
  `fno forecast-v4 capture`). Both refuse after their cutoff (`fno/forecast_v4_rules/capture.py` `cutoff`, 15:00 today,
  14:30 after G10) and refuse "stale closes" when the previous session's close is not in yet (`fno/weather/capture.py`).
- **The card is built, not scheduled** (strong evidence: T1 Scope "Out: scheduling (the owner decides later)").
- **The data checks already run inside the desk** (strong evidence: `DataGate` in `daily_wiring.py`, C3/C4 before every
  fill). O1 adds no second check; "data checks" in REPLAN is E3's gate.
- **GitHub's cron lost the 3 pm on both days it ran** (strong evidence: `conversations/2026-10-15.md` line 618; NSE
  canonicals for 14 and 15 Oct are `none`, started about 5 hours late), while the owner's Claude routine recorded Groww
  on both days (`nifty_20261014_145500`, `nifty_20261015_150225`).
- **The owner, 15 Oct** (`conversations/2026-10-15.md` line 628): "let's move the logic from github action to claude
  routine because timing matters here ... change them to claude routines for which timing is critical". The handover's
  agreed rule (O8 text): time-critical work runs on Claude routines; GitHub cron is a fallback or runs evening jobs.
- **The conflict, said plainly:** REPLAN line 61 says "fired from Actions as O6 does"; the owner's later words say the
  opposite for time-critical work, and the desk day is the most time-critical job (15:10 deadline, 15:15 snapshot).
  This text proposes **option A** below and needs the orchestrator's (and, through it, the owner's) choice before the
  judge's check. Recommendation: A (strong evidence for the cron's lateness; reasoning only that a Claude routine stays
  on time beyond the two days seen).
- **G10's timeline** (branch `story/g10-v4-timeline`): routine at 14:05, pack captured 14:30-14:40, one 15:10 deadline,
  the 15:15 common snapshot (A16's 15:15 mark). O1 takes its times from their owners (`desk.timetable`, the recorder's
  window, `terms`), never types them again, so G10's go-live changes nothing in O1's code.

## How it starts

**Option A (recommended): the owner's existing 3 pm Claude routine runs the day.** Its stored prompt becomes: (1)
`sh tools/routine_setup.sh --groww`; (2) `python -m fno daily run`; (3) if the command printed "alert NOT sent", post
its lines with the Slack connector; note any result other than "day done" in `conversations/<date>.md`, commit and push.
The routine is **updated, not created** (O1 never creates a scheduled task; the owner pastes the prompt). Groww, Drive
and Slack settings are already in that routine's environment, so no broker key goes into GitHub (O6's rule). One
schedule means no two schedules race (the old O1's reason).

**Option B: a GitHub Actions workflow as O6 does.** Started by the push of the day's canonical (seconds, as
`forecast-capture.yml` does), the cron as fallback. Costs, all strong evidence from the files: weather and v4 capture
must run **before** the canonical exists (cutoff 15:00, 14:30 after G10), so they would depend on the cron (lost on
14 and 15 Oct); the 15:15 snapshot needs Groww in GitHub or A16's mark in Drive (A16 is not live: work register).

The rest of this text is the same for A and B; only the routine prompt and the workflow file differ.

## Scope

In:
- **`python -m fno daily run [--day YYYY-MM-DD]`** (new package `fno/daily/`): on a recorded session (A7), the steps in
  this order, each recorded in E3's run log `journal/runs/<date>.json` (one log per day, the one O8 reads):

  | Step | Runs | Does (existing code, unchanged) |
  |---|---|---|
  | `weather` | at once | M1's `capture_weather` (refused after the cutoff or on stale closes: recorded, never retried) |
  | `forecasts_v4` | at once | G7's capture (same rules) |
  | `quotes` | the recorder's own window | A4's `record_today` (with A4c and the NSE recorder when those land), then commits `research/data/quotes/` at once, so E3's pack and `forecast-capture.yml`'s push trigger see the canonical |
  | `versions` ... `exits` | E3's timetable | E3's `DailyRun` steps, untouched |
  | `card` | after `exits` | T1's `card daily --post` |

- **A step that fails never stops the next** (design 9): an exception or refusal in `weather`, `forecasts_v4`, `quotes`
  or `card` is recorded with `status` and `reason`, alerted once to #fno-desk, and the run goes on. E3's own rule is kept:
  a failed **commit** stops the run with one alert naming the missed exits (decision 44, judged in E3; O1 does not
  reopen it).
- **Not live yet:** `config.yaml` `daily.live_from` per O1 step (`weather`, `forecasts_v4`, `card`); before its date the
  step is recorded `not_live` and does nothing. Reason: a first live weather record ends M1's back-fill and v4 rows
  before the G6 freeze would mix with the freeze (strong evidence: `fno/weather/capture.py` docstring "before the first
  live record"); the dates are set by the owner or the freeze, not by O1.
- **The run-log contract for O8** (to agree with O8's builder; O8's text today says "all six steps present"):
  - the file's shape is E3's, unchanged: `{"day", "kind": "daily_run", "steps": {name: {started_at, finished_at,
    inputs, result}}}`;
  - the expected step names are one tuple, `DAILY_RUN_STEPS` in `fno/constants.py`, which O8 imports (no count typed);
  - every O1 step's `result` carries `status` (`ok`, `failed`, `refused`, `not_live`) and `reason`;
  - lateness stays O8's rule: `decisions.finished_at` against `desk.timetable.decision_deadline`;
  - a closed day keeps E3's single `skipped` step.
- **The prompt text lives once:** CLAUDE.md section "Daily desk routine" replaces the "3 pm quote recorder" section
  (steps 1-4 keep their rules: never edit a recorded attempt, never `--no-verify`, alert paths). A test checks that the
  section holds the command lines (option A) or the workflow does (option B).
- The command ends on one line: `day done` or `day done with problems: <steps>` or E3's `RunStopped` line.

Out: any change to the steps' own code (E3, A4, A4c, M1, G7, T1, G10); the routine's schedule time (the owner's, 14:05
at G10's go-live); E3's snapshot source moving to A16's 15:15 mark (G10's row "E3 / S1 desk"); the health check (O8);
O2's end-to-end failure suite.

## Acceptance criteria

1. **Order and days.** With fakes: on a regular session every step runs once, in the table's order; a closed day and a
   muhurat-only day record only `skipped`; a special session runs as A4 and E3 already decide.
2. **A failure never stops the next step.** For each O1 step a planted exception and a planted refusal give that step
   `failed` / `refused` with its reason, one alert, and every later step still runs, `exits` and `card` included. A
   planted failed commit in an E3 step keeps E3's stop and its one alert (unchanged test still passes).
3. **Restart.** A rerun the same day skips every recorded step (E3's rule, now for O1's steps too); a `weather` step
   refused at 14:31 is not retried; a rerun after the deadline leaves E3's late rule as it is.
4. **The quotes step is A4's.** Its files are identical to `fno quotes record`'s on the same fixture (A4's baseline
   tests pass); the canonical is committed and pushed inside the step, before `pack` waits for it.
5. **The card is T1's.** It runs after `exits`, posts once, and still posts naming any earlier step that failed.
6. **Not live.** A step before its `live_from` is `not_live` and calls nothing (fake proves no call).
7. **O8's contract.** `DAILY_RUN_STEPS` holds every step name the run can write; a test fails if the run writes a name
   not in it. Whichever of O1 and O8 merges second adds the test that O8 reads this tuple.
8. **One prompt.** The CLAUDE.md section (A) or the workflow (B) is the only place the start is written; a test checks
   it names `python -m fno daily run` and `routine_setup.sh`; after the owner pastes it, the stored prompt is read back
   and matched once (conversation log).
9. **Real day.** One live day before S1 counts any day: every step recorded, every record committed, the card in
   #fno-desk; the log and commit list in the claims file.
10. **Engineering.** Each O1 step behind one `DayStep` interface; wired only in `fno/daily/wiring.py` (added to
    CLAUDE.md's composition roots); no file or class over 350 lines; no secret in any file or output (record scan);
    never orders.

## Gap list

| Requirement (source) | Criterion or reason out |
|---|---|
| One daily run: data checks, forecasts, weather, desk, card (REPLAN 61) | 1 (data checks = E3's gate) |
| Fired from Actions as O6 does (REPLAN 61) | option B; A recommended (owner, 15 Oct; cron lost 14-15 Oct) |
| Failure alerts and exits still run (old O1 criterion 3, design 9) | 2 |
| Same quote format as A4 (old O1 criterion 2) | 4 |
| Stored prompt matches CLAUDE.md (old O1 criterion 4) | 8 |
| Dry run commits every record (old O1 criterion 1) | 9 |
| Across containers: pull, lock, commit, push (old O1, E1) | E3's `GitAccountSync`; E2c moves accounts to Drive (code waits for it) |
| G10 times (14:05, 14:30-14:40, 15:10, 15:15) | read from their owners; nothing typed in O1 |
| O8 checks what O1 produces | 7 and the contract above |

## Known limits (one line each)

- If the routine's session dies mid-day nothing restarts it; O8's 17:51 check reports it, and a rerun resumes (late).
- Weather and v4 capture refuse when the previous close came late (`index-closes.yml`, 11:41 retry): seen on the card.
- A Claude routine's start time is measured on two days only (some evidence).
- A GitHub push delay near 15:10 counts as late (G10's rule).

## Test plan

`tests/daily/` with a fake calendar, fake steps, fake committer and fake alert sender, never the network; one test per
criterion with good, failing and empty cases; every criterion broken once on purpose.

**Judge verifies:** reads the run order and one planted failure per step; reads the routine prompt (or workflow) for
secrets and order-placing; checks the real day's log and commits.

**Depends:** E3 (merged), E2c (accounts to Drive, not merged), T1, M1, G7, A4/A7; G10 for the go-live times ·
**Status:** story text, waits for the orchestrator's A/B choice, then the judge (`reviews/claude/response_165_o1-daily-run.md`)
