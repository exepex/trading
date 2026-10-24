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
- **Decided: option A** (orchestrator, 15 Oct, on the owner's two decisions): the owner's words above, and
  `docs/DESK_DECISIONS.md` row "O6 scope: timed jobs stay on Claude routines" (owner: "Timed jobs on routines
  (Recommended)", commit eeac1897; GitHub's timer starts this repository's runs 4-5 hours late and skips most slots,
  judge 52 add. 1). REPLAN line 61's "fired from Actions" is superseded for this time-critical job (the orchestrator's
  ruling; both are the owner's own words of 15 Oct and name timed jobs specifically).
- **G10's timeline** (branch `story/g10-v4-timeline`): routine at 14:05, pack captured 14:30-14:40, one 15:10 deadline,
  the 15:15 common snapshot (A16's 15:15 mark). O1 takes its times from their owners (`desk.timetable`, the recorder's
  window, `terms`), never types them again, so G10's go-live changes nothing in O1's code.

## How it starts

**Option A (decided): the owner's existing 3 pm Claude routine runs the day.** Its stored prompt becomes: (1)
`sh tools/routine_setup.sh --groww`; (2) `python -m fno daily run`; (3) if the command printed "alert NOT sent", post
its lines with the Slack connector; note any result other than "day done" in `conversations/<date>.md`, commit and push.
The routine is **updated, not created** (O1 never creates a scheduled task; the owner pastes the prompt). Groww, Drive
and Slack settings are already in that routine's environment, so no broker key goes into GitHub (O6's rule). One
schedule means no two schedules race (the old O1's reason).
The stored prompt is one sentence pointing at the section ("Run the daily desk routine in CLAUDE.md, section 'Daily
desk routine'."), so the three steps above are written only in CLAUDE.md (criterion 8; 16 Oct).

**Ownership of the prompt (orchestrator, 15 Oct):** O1 owns the routine's prompt text and the CLAUDE.md section.
A4c (other indices), G10 (14:05 start, 14:30-14:40 window) and the handover session change only the command they own
and send their prompt lines to O1 through the orchestrator; no second copy of the prompt is written anywhere.

**Lines other stories send for the prompt (through the orchestrator):** A4c (its steps 2-3b, above); G10 (14:05
start and its windows, at go-live); A14c (orchestrator, 15 Oct; owner decision in `docs/DESK_DECISIONS.md`, da0f769d):
after each applied row in `research/data/margins/stress_factor.csv`, the read-only Groww margin comparison runs
(SPAN within Rs 1, exposure within 1%; a mismatch alerts). Its line (A14c builder through the orchestrator, 15 Oct;
command name provisional until A14c's code lands): "After A14c's weekly row is `applied`: `python -m fno margins
stress-broker-check` (read-only Groww margin request for the SF 100 basket on that day's A14 row; never places an
order). A mismatch posts its own #fno-desk line; the factor stays applied." The weekly row lands on Sunday, when the
day's run records only `skipped`, so it is an O1 step, `margin_check`, run every session right after the quote parts
start (they wait for 14:55 themselves) and done long before the 14:55 capture on the same Groww key. Agreed with the A14c builder (15 Oct; A14c text at
`story/a14c-stress-recompute` f2192b2f): the command checks the latest `applied` row once, prints "nothing to check"
otherwise (exit 0), exits 1 on a Groww or read failure (one O1 alert; the next session retries), and appends only
`research/data/margins/stress_broker_check.csv`, the one path the step commits. It stays `not_live`
(`daily.live_from.margin_check`) until A14c's code lands.

**E8's step (agreed with the E8 builder, 15 Oct; E8 rule 11 at `story/e8-owner-timing-fills` fd3a0344):**
`owner_timing_fills` joins `DAILY_RUN_STEPS` right after `quotes`, as E8's own `DayStep` listed with one line in
`fno/daily/wiring.py`; a failure fails closed for new entries through E2c's `_unreviewed` block, exits still run. E8
builds it on `main` after O1 merges; O1 adds nothing for it now.

**M2's step (agreed with the M2 builder, 15 Oct):** `weather_alert` joins `DAILY_RUN_STEPS` right after
`weather`: one `CommandStep` (`python -m fno weather-alert --day <d>`, gated by `daily.live_from.weather`, committing
only `research/alerts/weather/`); with no live weather record it prints one line and exits 0 (O1 has already alerted
the weather step's failure once). M2 builds it on `main` after O1 merges.

**The whole git history first (asked by E8, judge 203 should-fix 1; agreed with the orchestrator):** a cloud
checkout is shallow, and commit times date E8's availability seals and E3's committed decisions. So before the first
step, the run fetches the full history (`Git.unshallow`) when `git rev-parse --is-shallow-repository` says true. A
failed fetch, or one stopped at its hard 120 s limit (6.7 s measured on a fresh clone, judge 178 addendum 10), is
one alert and the day goes on; and the quote parts start before it, so a hung fetch can never delay the 3 pm capture: E8's step refuses in a shallow checkout by itself (entries fail closed,
exits run), and stopping the whole day would lose the quotes and exits too.

**The quote parts start before the run's Drive download (judge D, orchestrator, 16 Oct):** E2c's download is the
desk run's first act, and a Drive outage there stops the run before any step. So `DayRunner` starts the quote parts
first; the `quotes` step then records them. A Drive outage at the download loses the desk's day but never the NSE
record (which needs no Drive); after the stop the runner waits for the parts, at least until `desk.timetable.fills_by`,
and commits their own files. A rerun whose log already holds `quotes` starts no part (judge 178 note 4). On a closed
day each recorder's own calendar rule records nothing. Chosen over "skip only the steps that need Drive" because it
stays inside O1 and leaves E2c's judged stop rule as it is (reasoning only).

**E6's pauses run every session (judge 214, orchestrator, 16 Oct):** no step ran E6's scorecard or its safety pauses,
so a catastrophic loss would never pause its version. The `reviews` step runs E6's real `ScorecardRun` with
`pause=True` after the exits, marked at the day's execution snapshot, through the run's one alert sender, and commits
`playbook/`. A pause changes the version's status that day, so the next decision cannot trade it; exits still run.
Without a valid snapshot the step is refused only when some book holds an open position (it cannot be marked, so its
loss rules were not judged); with none open it is ok, "no open position to mark" (judge 178 addendum 13). Closed
losses pause either way. A failed or refused step, or one that never ran after the exits, blocks every book's new entries
at the next session (`DailyRun._unscored`); exits still run.

**Option B (not chosen): a GitHub Actions workflow.** Kept as the record of why: weather and v4 capture run before the
canonical exists, so they would depend on GitHub's late timer, and the 15:15 snapshot would need Groww in GitHub.

## Scope

In:
- **`python -m fno daily run [--day YYYY-MM-DD]`** (new package `fno/daily/`): on a recorded session (A7), the steps in
  this order, each recorded in E3's run log `journal/runs/<date>.json` (one log per day, the one O8 reads):

  | Step | Runs | Does (existing code, unchanged) |
  |---|---|---|
  | `quotes` | starts the three quote parts in the background (below), records that they started, and goes on | A4c's routine steps 2-3b, unchanged |
  | `margin_check` | at once | A14c's `margins stress-broker-check` (read-only Groww; commits only its own file) |
  | `weather` | at once | M1's `capture_weather` (refused after the cutoff or on stale closes: recorded, never retried) |
  | `forecasts_v4` | at once | G7's capture (same rules) |
  | `versions`, `pack` | E3's timetable, in the foreground | E3's `DailyRun` steps, untouched |
  | `book1` | right after `pack` | E5's `desk book1 --day <d>` (Book 1's decision, committed by itself) |
  | `decisions` ... `exits` | E3's timetable, in the foreground | E3's `DailyRun` steps, untouched |
  | `reviews` | after `exits` | E6's scorecards and automatic pauses (catastrophic and cumulative loss), marked at the day's execution snapshot; commits the playbook's status changes (judge 214); LR3's drift monitor joins it later |
  | `quotes_done` | after `exits`: waits for the parts still running, records each part's result line and commit | |
  | `card` | after `quotes_done`, only if E3 did not stop | T1's `card daily --post`; always after `decisions` (final at 15:12) and `snapshot` (C3 final at 15:15), so a card never posts before what it shows is final (T2 builder, 15 Oct) |

- **The quote parts are A4c's passed steps 2-3b** (judge 151 addendum 2 text, judge 160 code; branch
  `story/a4c-all-indices` until it merges after judge D's 16 Oct check), run by O1 as child processes beside E3's
  steps so that neither waits for the other:
  - `nifty`: `python -m fno quotes record` (Groww) and `nse`: `python -m fno quotes record --source nse` start together
    at the run's start; each keeps its own window (14:55-15:10 today, 14:30-14:40 after G10);
  - `indices`: `python -m fno quotes record-indices` starts right after NIFTY's push, in its own window (15:01-15:13
    today, 14:41-14:58 after G10), beside NSE if NSE is still running;
  - each part commits and pushes only its own files, NIFTY first, as soon as its result line is printed, with A4c's
    paths and never `research/data/quotes/` as a whole: NIFTY `':(glob)research/data/quotes/groww/**/nifty_*'`; NSE
    `research/data/quotes/nse/`; the indices `':(glob)research/data/quotes/groww/**/banknifty_*'`
    `':(glob)research/data/quotes/groww/**/finnifty_*'` `':(glob)research/data/quotes/groww/**/midcpnifty_*'`. The
    paths are one constant in code; A4c's test (`tests/quotes/test_routine_commit_paths.py`) checks that CLAUDE.md
    gives the same ones;
  - E3's `pack` already waits for NIFTY's committed canonical (it retries until `pack_wait_until`), so NIFTY's push
    inside the run is what releases it; `forecast-capture.yml`'s push trigger still starts on that push.
- **One git at a time:** every git command of the run (the parts' commits, E3's commits and its pack's pull) runs in
  the run's one thread, so a commit (pull, add, commit, push) is always whole (code round: the "lock" is that single
  thread; the parts are child processes that never run git, and the run commits each one only between the desk's
  steps or while it waits, `ServicingWaiter`), so two commits never interleave in the one
  checkout (reasoning only that git's own `index.lock` would otherwise fail one of them at random; the test below
  proves the order). The parts' commits go through E3's own `GitCommitter` (its record-scan guard, pull and push
  attempts), never a second git path, and each commits by pathspec (`git commit -- <paths>`), so files staged by a
  refused E3 commit are never swept into a part's commit (judge 169 addendum 1, notes 1-2). Why not leave the parts to the routine's prompt, as today: the routine's git commands and the run's
  own commits would then share the checkout with no common lock, and a collision inside E3 stops the desk (decision 44).

- **No command holds the day:** each O1 command (`margin_check`, `weather`, `forecasts_v4`, `book1`, `card`) is
  stopped and recorded `failed` after 10 minutes (`COMMAND_LIMIT_SECONDS`); the quote parts start before any of them,
  so a hung Groww call can never delay the 3 pm capture (judge 178 addendum 1 note 6; orchestrator: required). A
  stopped command's whole process group is killed (a git call it started dies with it). Said plainly (judge 178
  addendum 3 note 7): the limit does not protect the 15:12 deadline for `book1`, which can start at about 15:10 when
  the pack comes late; E3's late rule then records Book 1 as late and the exits still run.
- **A step that fails never stops the next** (design 9): an exception or refusal in `weather`, `forecasts_v4`, a quote
  part or `card` is recorded with `status` and `reason`, alerted once to #fno-desk, and the run goes on. A quote part's
  own alerts (the recorder's three, the record scan's) are its own, as A4c says; O1 adds none for them.
- **After E3's commit-failure stop** (decision 44, judged in E3; O1 does not reopen it): E3's one alert stands alone.
  The `card` does **not** run, because nothing more may be committed after the stop and T1's `--post` writes delivery
  metadata. The quote parts already running are waited for and keep A4c's own commit rule for their own paths (they are
  the recorder's data, not the desk's records; a commit they cannot make is alerted by them). `quotes_done` and `card`
  are then not recorded (the run log's commit is the desk's, and it stopped), so O8 shows them missed, beside E3's
  alert. A rerun after the fix records them (criterion 3). The command ends on E3's `RunStopped` line plus "no card
  today". **What the owner loses that day (said plainly):** the card's forecast block
  and its Slack issuance witness; the forecasts themselves stay committed by their own job with GitHub's push receipt,
  and the stop alert names the cause and the hand fix.
- **Not live yet:** `config.yaml` `daily.live_from` per O1 step (`weather`, `forecasts_v4`, `card`); before its date the
  step is recorded `not_live` and does nothing. Reason: a first live weather record ends M1's back-fill and v4 rows
  before the G6 freeze would mix with the freeze (strong evidence: `fno/weather/capture.py` docstring "before the first
  live record"); the dates are set by the owner or the freeze, not by O1.
- **The run-log contract for O8** (to agree with O8's builder; O8's text today says "all six steps present"):
  - the file's shape is E3's, unchanged: `{"day", "kind": "daily_run", "steps": {name: {started_at, finished_at,
    inputs, result}}}`;
  - the expected step names are one tuple, `DAILY_RUN_STEPS` in `fno/constants.py`, which O8 imports (no count typed),
    and **the tuple the run itself loops over**, never a parallel copy (agreed with O8's builder, 15 Oct): O8's private
    `DESK_RUN_STEPS` and its source-parsing test are replaced by it. `fno/constants.py` is at 337 of 350 lines (343 on
    O8's branch): the tuple takes at most two lines, and whoever passes 350 splits out a cohesive block, never squeezes;
  - every O1 step's `result` carries `status` (`ok`, `failed`, `refused`, `not_live`) and `reason`; O8 reads `failed`
    and `refused` as a problem with its reason, `not_live` as present but neither missed nor a problem, and an absent
    step as missed (as now);
  - lateness stays O8's rule: `decisions.finished_at` against `desk.timetable.decision_deadline`;
  - a closed day keeps E3's single `skipped` step.
- **The prompt text lives once:** CLAUDE.md section "Daily desk routine" replaces the "3 pm quote recorder" section.
  It keeps A4c's steps 2-4 word for word as what the run does for each part, including the per-part `git add` lines,
  which are also the hand fix if a part's commit failed, and its rules: never edit a recorded attempt, never
  `--no-verify`, the alert paths. A test checks that the section holds the command lines.
- The command ends on one line: `day done`, `day done with problems: <steps>`, or E3's `RunStopped` line plus "no card
  today".

Out: any change to the steps' own code (E3, A4, A4c, M1, G7, T1, G10); the routine's schedule time (the owner's, 14:05
at G10's go-live); E3's snapshot source moving to A16's 15:15 mark (a dependency, not O1's: see Depends); the health check (O8);
O2's end-to-end failure suite.

**Code-round amendment (for judge D):** Book 1's decision (`fno desk book1`, E5) had no caller either: its own
docstring said "No routine starts them yet". Without the `book1` step, E3's `decisions` step would record "no decision
(late)" for Book 1 every day. It runs right after `pack` (it needs the pack) and before the 15:12 deadline, as its own
command, which commits its own decision; its pathspecs are none, so the run sweeps up nothing for it.

## Acceptance criteria

1. **Order and days.** With fakes: on a regular session every step runs once, in the table's order; a closed day and a
   muhurat-only day record only `skipped`; a special session runs as A4 and E3 already decide.
2. **A failure never stops the next step.** For each O1 step and each quote part a planted exception and a planted
   refusal give it `failed` / `refused` with its reason, one alert (none of O1's for a quote part), and every later step
   still runs, `exits` and `card` included. A planted failed commit in an E3 step keeps E3's stop and its one alert
   (unchanged test still passes) **and the card does not run** (fake card proves no call, no post, no write); the quote
   parts still running are waited for and commit their own paths; the last line names "no card today".
3. **Restart.** A rerun the same day skips every recorded step (E3's rule, now for O1's steps too); a `weather` step
   refused at 14:31 is not retried; a rerun after the deadline leaves E3's late rule as it is.
4. **The quote parts are A4c's.** Each part runs its own command unchanged (A4's and A4c's tests pass). With fake parts
   and a fake git: NIFTY and NSE start together at the run's start; the indices start only after NIFTY's push; each
   commit stages exactly that part's paths (the files planted by A4c's test fixture: NIFTY's commit holds no NSE or
   index file, never a Groww quote file), NIFTY's commit is the first; E3's steps run while a part is still running (a
   part that runs to 15:13 does not move `decisions` or `snapshot`); a planted NIFTY failure leaves NSE, the indices'
   skip and E3's "no pack" path as their own stories decide.
4a. **One git at a time.** Two commits asked for at the same moment (a part's and an E3 step's) run one after the other,
    never interleaved (fake git records each command with its holder); a part's commit with another file already
    staged commits only the part's paths.
5. **The card is T1's.** It runs after `quotes_done`, posts once, and still posts naming any earlier O1 step or quote
   part that failed; it never runs after E3's stop (criterion 2).
6. **Not live.** A step before its `live_from` is `not_live` and calls nothing (fake proves no call).
7. **O8's contract.** The run's plan is built from `DAILY_RUN_STEPS` (a test: the steps a full fake day writes are
   exactly the tuple, in its order; renaming one step in the tuple renames it in the log). Whichever of O1 and O8 merges
   second makes O8 import the tuple, deletes `DESK_RUN_STEPS` and its source-parsing test, and adds a test that O8's
   desk check reads the tuple.
8. **One prompt.** The CLAUDE.md section is the only place the start is written; a test checks
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
| Fired from Actions as O6 does (REPLAN 61) | superseded: timed jobs stay on Claude routines (owner, DESK_DECISIONS 15 Oct) |
| Failure alerts and exits still run (old O1 criterion 3, design 9) | 2 |
| Same quote format as A4 (old O1 criterion 2) | 4 (the parts' own commands, unchanged) |
| A4c's passed routine: NIFTY and NSE in parallel, indices after NIFTY's push, per-part paths (judge 169) | 4, 4a and the CLAUDE.md section |
| The card after E3's stop (judge 169) | 2, 5: it does not run |
| Stored prompt matches CLAUDE.md (old O1 criterion 4) | 8 |
| Dry run commits every record (old O1 criterion 1) | 9 |
| Across containers: pull, lock, commit, push (old O1, E1) | E3's `GitAccountSync`; E2c moves accounts to Drive (code waits for it) |
| G10 times (14:05, 14:30-14:40, 15:10, 15:15) | read from their owners; nothing typed in O1 |
| O8 checks what O1 produces | 7 and the contract above |

## Fix after the merge: the 3 pm parts' earliest start (16 Oct, branch `story/o1-part-start`)

- **The gap (strong evidence, found by O2's end-to-end day):** A4's recorder returns "too early" and records nothing
  when started more than `MAX_EARLY_WAIT_SECONDS` (20 min) before its 14:55 window (`fno/quotes/recorder.py` 137-140).
  O1 started NIFTY's and NSE's parts at the run's start, so a run starting before 14:35 (the routine starts at 14:33,
  14:05 after G10) loses both records.
- **The fix:** each part has `not_before`, `EARLIEST_START` = 14:55 - 20 min + 3 min = 14:38, from A4's constants.
  `QuoteParts.start` opens the day and starts only the parts that are due. `start_due` (no git) starts the others
  from any wait of the run: the desk's `ServicingWaiter`, and every command's poll loop (`waiting` in
  `fno/daily/wiring.py`). Commits stay between the steps. A run stopped early still starts them, in `finish`.

## Fix after the merge: a rerun resumes the 3 pm parts (21 Oct, branch `story/o1-part-lock`; judge 412 add. 2)

- **The gap F1 (strong evidence, O2's kill-and-rerun day):** when the routine's container dies before the parts
  recorded, the parts die with it. The rerun's log already holds `quotes`, so it starts none, although the window is
  open until 15:10 (indices 15:13). The day then has no NIFTY or NSE record, no pack and no decision. A rerun after a
  stop also called parts that the stopped run had committed "not in this run".
- **The rule (judge D's design, 412 add. 2 and 3):** each part's recorder process holds an exclusive `fcntl.flock`, not a pid
  lease (pids are reused), on a git-ignored file,
  `journal/runs/.parts/<date>_<part>.lock`. The run takes the lock when it starts the part and hands the open file to
  the child (`pass_fds`), then closes its own copy. The child holds the lock for its whole life without knowing it,
  so A4's commands are unchanged, and the kernel frees it when the child dies. On a rerun whose log holds `quotes`,
  each part is resumed:
  - **lock held** (a part of the crashed run still alive in this container): **adopted**. A second recorder is never
    started. The run waits for the lock to free inside `finish`'s existing bound (`FINISH_LIMIT`, and not before the
    timetable's `fills_by`), serviced like its own parts, while the desk's steps go on (judge 417):
    - when the lock frees, the part's status comes from its canonical markers, because its output and exit code are
      gone: `ok` with "recorded earlier (commit <sha>)" when every marker exists, otherwise `failed`. Its files are
      then committed under its own pathspecs;
    - past the bound the part is `failed`, "still running after <minutes> minutes, held by an earlier run's
      recorder", with one alert and no commit of its files. The alert gives the hand fix, because the run cannot stop
      a process it did not start: "a 3 pm recorder of an earlier run still holds <lock>: stop it, then rerun";
  - **every canonical marker of the part present:** `ok`, "recorded earlier (commit <sha>)", read from the commit that
    holds the marker, with no alert. That holds also after a stopped run, whose parts were committed by its finish
    (judge 412 add. 3). Any of its files still uncommitted are committed;
  - **otherwise, while the part's window is open** (`WINDOW_END` 15:10; the indices' `INDEX_WINDOW_END` 15:13, from
    A4's constants): **restarted**, with its own `not_before` and `starts_after` (the indices after NIFTY);
  - **otherwise:** `failed`, `NOT_IN_THIS_RUN`, with one alert. This is the only case left for it.
- **A `none` marker is not a record (21 Oct, found reviewing A4f; orchestrator: fix before go-live):** A4's recorder
  writes the canonical marker as `none` when the window ends without a complete attempt. A part taken from an earlier
  run whose markers include `none` is `failed`, "the day ended none, no complete attempt (recorded earlier, commit
  <sha>)", never `ok` (O10: no ok without data). It is alerted once more, because the rerun cannot know whether the
  killed run sent its alert, and a duplicate is better than a silent day.
- **NIFTY first**, whatever each part's `how`: no other part commits before NIFTY's commit was made or tried, and the
  indices start only after NIFTY has ended (A4c).
- **The log names it:** each part's result carries `how` (`started`, `restarted`, `adopted`, `earlier run`) and its
  start time. `quotes`' reason names the start time, "nifty, nse from 14:38" (judge 178 add. 19).
- **Tests:**
  - a kill before 14:55 with a rerun in a new run: the end state is the twin's bytes;
  - a crashed run with a live part: adopted, one recorder; and one still holding its lock past the bound: failed
    with the hand-fix alert, its files not committed;
  - a rerun after 15:10: `NOT_IN_THIS_RUN` with one alert;
  - the same for the indices part;
  - F1's strict xfail in `tests/e2e/test_kill_rerun.py` becomes the real assertion.

## Fix after the merge: a quote part's unpushed commit never stops the desk (21 Oct, `story/o1-own-commits`; judge 412 add. 3)

- **The gap G4 (strong evidence, O2's hang day, `tests/e2e/test_hangs.py`):** a quote part's commit whose push was
  rejected three times, or stopped at the 120 s limit, stays local and unpushed. The desk's next commit refuses it as
  "an unpushed commit the run did not make" (`GitCommitter._refuse_stray`, decision 51). So the desk stops at its next
  step, the exits are not reviewed, and the next session blocks every book.
- **The rule (judge D's ruling, kept simple):**
  1. one `GitCommitter` per run, shared by the quote parts and the desk's `PendingCommitter` (`fno/daily/wiring.py`
     builds a second one for the parts today). It remembers each commit it made and could not push as an
     `OwnCommit` (message and each file's SHA-256), and `_refuse_stray` accepts any of them, still checked by content.
     A stranger's commit is still refused;
  2. the list is also kept in a git-ignored file (`journal/runs/.own/unpushed.json`: its own folder, since the readers
     of `journal/runs/*.json` take every file there for a run log), so a rerun in the same container still accepts
     them by content. A new container has none, because its clone holds only what origin holds;
  3. no reset of the local commit (rejected: after a pull's merge it can leave origin's changes staged);
  4. the part's alert says "committed, NOT pushed (the next push carries it)", not the "NOT committed" hand fix.
- **Tests:**
  - a refused and a hung part push: the next desk push carries the commit, with one alert, and the desk goes on;
  - a stranger's unpushed commit is still refused;
  - a rerun accepts the run's own commit by content, and refuses it if its files were changed;
  - G4's strict xfail in `tests/e2e/test_hangs.py` becomes the real assertion.

## Fix after DRY2: the indices' own early limit and one failed step never ends the day (24 Oct, `story/o1-r1r2-step-safety`)

DRY2's daily-run rehearsal (docs/dryruns/DRY2_2026-10-23.md, rows d8 and d11) found two risks for a real day. The
orchestrator put both before Monday 26 Oct 14:05 IST, lane 1 (judges B and E).

**R1. The indices part started "too early" when NIFTY's part ended early.**
- **Before:** the indices part started the moment NIFTY's part ended. A NIFTY part that died at 14:38 started A4c's
  index recorder at once, more than 20 minutes before 15:01. It returned "too early" and recorded nothing, and the run
  never started it again: the day's indices were lost.
- **Note:** no "none" marker is written: "too early" skips `close_day`. A4c's alert still says "canonical none",
  which is A4c's wording, a finding for A4c's owner, unchanged here.
- **Fix:** `QuotePart.not_before` now also holds for a part that waits for another. The indices part gets
  `INDEX_EARLIEST_START`, A4c's own early limit (15:01 less 20 minutes, plus the 3-minute margin: 14:44).
  - `start_due` starts a waiting part once its part ended and its time has come; `service` calls it.
  - `next_start` counts a waiting part once its part ended, so a rehearsal's skipped wait never passes it.
  - On a normal day nothing changes: NIFTY commits at about 14:57, after 14:44.
- **Tests** (`tests/daily/test_index_part_window.py`):
  - the limit is 14:44, inside A4c's 20 minutes;
  - a NIFTY part dead at 14:38 starts the indices only at 14:44, from any wait, without git;
  - a normal day still starts them right after NIFTY's commit.
- **Plants:** the indices' `not_before` dropped fails the test; `not_before` ignored for a waiting part fails it.

**R2. One unexpected error ended the whole daily run.**
- **Before:** `DailyRun._guarded` handled only `CommitFailed` and `GitFailed`. In the rehearsal a `NotImplementedError`
  in the 15:15 snapshot ended the run with a traceback: no fills, exits, reviews, card, scores, candles or close reads.
- **Fix:** `DailyRun._run_step` catches any other `Exception` from a step's action.
  - The step is logged `{"status": "failed", "reason": "<type>: <first line>"}`. #fno-desk gets "F&O paper desk <day>:
    step <name> FAILED (<reason>); the run goes on, the steps that need it are refused". The run goes on.
  - A failed commit or git read still stops the run, as decision 44 says (unchanged).
  - `NEEDS` names the steps that read another step's logged result. Only `fills` does: it reads the snapshot's
    `valid` and the decisions. So `fills` is refused when either failed ("needs snapshot, which failed today"). Every
    other step reads its own inputs. The exits and the marks check the snapshot through the gate themselves, so the
    risk-reducing exits always run (design 9).
  - The next session's `_unreviewed` reads a failed exits step as "no book's exits were reviewed". Before, it would
    have read the failure's own fields as books.
- **Tests** (`tests/timetable/test_step_error_run.py`):
  - a planted `NotImplementedError` in the snapshot capture fails that step only, with its type and first line, and
    alerts; `fills` is refused; the exits and the marks run;
  - a failed exits step leaves every book unreviewed for the next session.
- **Plants:** the catch narrowed, the refusal dropped, and the exits rule dropped: each fails a test.

**Contracts changed** (for the judges):
- (1) `QuotePart.not_before` now applies to parts with `starts_after`.
- (2) `QuoteParts.next_start` includes such a part once its part has ended.
- (3) `DailyRun` no longer lets a non-git, non-commit exception out of a step. A step's result may now be
  `failed`/`refused` with a reason where the run used to raise.
- (4) `_unreviewed` for a failed exits step.

**Round 2 (the orchestrator and judge 567): fail closed, one table, every reader.**

*Which step needs which.* This is read from `DailyRun`'s real step inputs: `_plan` and each step's own reads.

| Step | Reads another step's logged result | If that step has not run | If that step failed |
|---|---|---|---|
| fills | snapshot (`valid`), decisions (the collected runs) | refused: "needs snapshot, which has not run today" | refused: "needs snapshot, which failed today" |
| every other desk and O1 step | none: each reads its own inputs (files, the gate, Drive) | runs | runs |

The exits and the marks check the snapshot through the gate themselves, so risk-reducing exits always run (design
9). Book 1's decision (an O1 command) reads the pack from disk and refuses itself without it ("no common pack").

*Every reader of a failed or refused step's committed result* (`{"status", "reason"}`, nothing else):
- **Desk:**
  - `daily_run` fills: refused (the table).
  - `daily_run._unreviewed`: a failed exits step means every book is unreviewed.
  - `_unfilled` and `_unscored` already read `status`.
- **The run's last line** (`runner.py`): names the failed and refused steps through `run_log.problem_steps`, the one
  rule (agreed with T1 for T1d's card).
- **Scoreboard** (`scoreboard/committed_runs.py`, guarded here): reads the decisions and the exits through
  `run_log.book_results`, which gives {} for a failed step.
  - `runs()`: no run.
  - `uncollected()`: no others. Before, it raised AttributeError on the failure's string.
  - `missed_runs`: a missed decision and a missed exit review.
  - `snapshot_ids`: no valid snapshot.
- **Card** (T1, `cards/rule_checks.py`):
  - The snapshot verdict reads "no valid execution snapshot (<reason>)", `data_check_failed`. Correct already.
  - The decisions' late books would list "status" and "reason" (judge 567). T1d's change uses `book_results`, and the
    orchestrator merges R2 together with T1d.
- **E6 reviews** (`daily/reviews.py`): no valid snapshot, so a day with open positions is refused. Correct already.
- **O8 health** (`health/desk_checks.py`): `_problems` names the step; `_collected_late` keeps only per-book dicts.
  Correct already.
- **E8 opening runs** (`books/opening_runs.py`): no `run_id`, so "no log". Correct already.
- **A16's feed gate:** reads only the candles step, an O1 command whose shape is unchanged.
- **Tests** (`tests/timetable/test_failed_step_readers.py`): the two helpers; the scoreboard on a failed decisions,
  snapshot and exits day; a missing input refused.
- **Plants** (the scoreboard without `book_results`; the missing check dropped): each fails.

*A frozen day (the desk freeze, held for the owner's v4 sign-off, unmerged).* The freeze records the desk's steps
`frozen` and runs none of them. `frozen` is neither failed nor missing, so `NEEDS` would not refuse the fills. The
freeze's own rule must decide first: when the freeze merges, its check goes before `_refused` in `_step`, so a frozen
day's fills are `frozen`, never refused or run. Both are O1's own code; the freeze branch carries the test.

**Round 2, judge 569 SF1 (the orchestrator's ruling): a failed step is retried by a same-day rerun when that is
safe.**
- **The rule:** a step failed by an unexpected error is logged `{"status": "failed", "reason", "retry": true|false}`.
  The run loop now asks `RunLog.finished` (done and not retryable), so a rerun runs a retryable step again, and
  `record` replaces its entry.
  - A finished step is never repeated.
  - A `refused` step whose failed inputs are all retryable is retryable too: the rerun retries the snapshot, then the
    fills it refused. A step refused for a missing input is final.
- **The alert says which:** "a same-day rerun (`fno daily run`) retries it", or "final today: <why>".
- **The public run log keeps `retry`.** Checked: O1-status-only's `PublicResult` keeps the boolean leaf and codes the
  reason as `raised:<Type>`.

| Step | Retry after an unexpected error | Why it is safe (from the code) |
|---|---|---|
| versions | yes | D6 refuses a second version on the same day (`book_versions.keep`) |
| pack | yes | write-once pack files: the same bytes are kept, others refused |
| decisions | yes | a retry after the deadline's grace marks every book late (`collect_decisions`, fail closed) |
| snapshot | yes | the gate takes only a capture between `execution_snapshot` and `fills_by` (15:15-15:20); a later one is invalid, so no fills |
| fills | yes | E1's cash ledger and the desk's fill rows are idempotent by fill ID (`DeskJournal.record_fill`); an entered trade returns its recorded outcome (`EntryDesk.enter`) |
| exits | yes | idempotent by fill ID; a closed position is no longer open; each book's error is already caught inside |
| trade_marks | yes | `write_trade_marks` and the equity row replace that session's own rows |
| every O1 step (commands, quote parts, card, reviews) | no, final | a command's child may have posted or written before the error; their own failures already alert |

**Judge 570, fills partly written.** `DeskSteps.fill` re-raises an unexpected error as `FillsInterrupted(written,
cause)`: commit and git failures still pass through untouched (decision 44). The step's reason is the cause, and the
alert adds "N trade(s) written before the error stay in the account, a retry never doubles them (idempotent by fill
ID)".

**Tests** (`tests/timetable/test_step_error_run.py`, now 6):
- a rerun retries a failed snapshot, then the fills it had refused, and repeats no finished step;
- a fills error after one trade says "1 trade(s) written"; the retry enters the rest, and no fill ID appears twice;
- failed decisions refuse the fills naming decisions, with no fill (SF2, judge 570's pin);
- an O1 step's failure is final, says so, and is not rerun.

**Plants:**
- `finished` back to `done`: 2 fail.
- fills out of `RETRY_SAFE`: 1 fails.
- `NEEDS` without decisions: 1 fails.
- The pass-through for commit and git failures dropped: caught by `test_commit_failure_run.py` (7 fail).

**T1's self-review finding, recorded and not changed here.** `problem_steps` reads `status` only, so three desk
outcomes that alert but carry no `status` are not named on the last line or the card:
- an exits book's `error`;
- `trade_marks` `{"marked": False}`;
- `pack` `{"built": False}`.
Naming them is a small follow-up for T1d or O1, to agree.

## Status at handover (24 Oct, the owner's usage limit; builder session_014zYLf18PgCzR7YoHs1X5Dp)

- **R1/R2:** on `story/o1-r1r2-step-safety`; round 2 is the head commit of this push.
  - Judge E's 570 passed e8dc9498d. Judge B's 569 failed e8dc9498d on SF1 and SF2.
  - The head commit carries SF1, SF2 and both of judge E's minors. It is for judge B's round 2, the last allowed, and
    judge E's delta.
  - Merge only together with T1d (story/t1d-failed-steps), which must drop its own copy of `problem_steps` and
    `book_results` for these.
- **A4c's shared early limit:** agreed with session_01MKtUHByHsR9cNwaP5KhFYH. When A4c-2 merges, `earliest_start`
  becomes `earliest_waiting_start(w) + START_MARGIN`, and the tests pin 14:38 and 14:44.
- **Next for the O1 owner:** answer the round-2 verdicts; the desk freeze's check goes before `_refused` when it
  merges.

**Not changed, said plainly:**
- The card's own text (T1's) does not list failed steps. The run's last line already names them ("day done with
  problems: snapshot, fills"), and each failed step is alerted.
- A `BaseException` (a kill, `KeyboardInterrupt`) still ends the run, as it should.

## Known limits (one line each)

- If the routine's session dies mid-day nothing restarts it; O8's 17:51 check reports it, and a rerun resumes (late).
- Weather and v4 capture refuse when the previous close came late (`index-closes.yml`, 11:41 retry): seen on the card.
- A Claude routine's start time is measured on two days only (some evidence).
- A GitHub push delay near 15:10 counts as late (G10's rule).
- The indices part and E3's 15:15 snapshot share Groww's key; A4c's window ends at 15:13, so they do not overlap (some
  evidence: the two windows; G10 moves both).
- A part whose push fails every time leaves an unpushed commit, so E3's `GitCommitter` refuses the desk's next commit
  (decision 51) and the desk stops with E3's alert; the hand fix is the alert's.
- A rerun after a dead run does not commit the dead run's quote part files (`quotes_done` says so): a killed recorder may
  have left a half-written file, and only the recorder can tell a complete attempt (judge 178 note 4, declined).
- After E3's stop the owner gets no card that day (the stop alert stands alone; the forecasts stay committed).

## Test plan

`tests/daily/` with a fake calendar, fake steps, fake committer and fake alert sender, never the network; one test per
criterion with good, failing and empty cases; every criterion broken once on purpose.

**Judge verifies:** reads the run order and one planted failure per step; reads the routine prompt for
secrets and order-placing; checks the real day's log and commits.

**Depends:** E3 (merged), E2c (accounts to Drive, not merged), A4c (code PASS, judge 160), T1, M1, G7, A4/A7; G10
for the go-live times; E3's snapshot moving to A16's 15:15 mark (assigned by the orchestrator after G10 merges) ·
**Status:** story text PASS (judge 169 addendum 1, 9f150096; its notes 1-2 added); code waits for E2c and the go (`reviews/claude/response_165_o1-daily-run.md`)
