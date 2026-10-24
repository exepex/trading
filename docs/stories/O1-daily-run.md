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
- (5) Round 2: a step's failure from `_run_step` carries `retry`. `RunLog.done` is false for a retry-failed entry, and
  `record` replaces it. `DeskSteps.fill` raises `StepInterrupted` after N trades are written.

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

**Round 2 (judges 569 and 570): SF1, SF2 and judge E's minors** (24 Oct; builder session_01Mt6dcBU5kp2htdPN2KmiZH,
which took over from the first builder)

*SF1, under the orchestrator's ruling (24 Oct 06:24).* A desk step failed by an unexpected error (`_run_step`) is
recorded `{"status": "failed", "reason", "retry": true|false}`. `retry` is true only for the steps in
`RETRIED_ON_RERUN` (`fno/desk/daily_run.py`).
- `RunLog.done(step)` is false for an entry that failed with `retry: true`, so a rerun runs that step again. `record`
  replaces that entry, and only that one. A finished step, a refused one, a step failed for good, an O1 command step's
  failure (no `retry` key) and a `retry` key on a step that did not fail all raise "a run never repeats a step". The
  new entry goes last in the log, in the order the steps ran.
- A failed step is retried on its own IST day only. `daily run --day <past day>` never retries it, because the next
  session's `_unreviewed` has already read that log.
- The alert ends "a rerun today retries it (nothing it wrote is done twice)" or "a rerun today will not retry it:
  <why>".
- `_refused` calls an input still waiting for its retry "failed", not "not run". The O8 health check lists it as
  failed, not as missing.

*Which desk step a rerun retries, and why* (read from the code):

| Step | What its retry would write again | Retried | Why |
|---|---|---|---|
| versions | a D6 row (`Book1Versions.keep`; a second same-day version is refused by D6) | no | It must land before the day's decision (judge 80). A rerun comes after Book 1 decided and after the decisions step ran, and a version committed after the decision cannot count for it (D6). Its only reader has already run. |
| pack | the common and private packs, written once (`PackStore`: the same bytes are accepted, a different pack is `PackError`, so the step returns built false) | no | Book 1's decision, the decisions step and the snapshot's checks have already run without it. A late pack would only disagree with what they saw. |
| decisions | `no_decision.json` per book, written once | no | Collected after the deadline, every book is late (`COLLECTED_LATE`), so a retry adds nothing true. Run 1 may have written a no-decision file with another reason, and the retry would conflict on it. The fills are already refused for the day. |
| snapshot | a second capture record (`RecorderExecutionCapture`), committed at once | no | `CommittedExecutionSchedule` reads the day's latest record. A retry would move the day's one execution snapshot after the exits and marks had used the first one. The fills are already refused. |
| fills | entry fills, ledger rows and events | **yes in round 2; no from round 3** (owner, 24 Oct: see Round 3) | Fill IDs are `trade:action:contract` (`fill_id`). `apply_fill` and `IdempotentCsvLog` make the same row a no-op, and a different row under a used ID is an error, never a second row. `EntryDesk.enter` returns a trade's recorded outcome, and E8's `PendingEntries.enter` does too. The gate reads the same committed capture, and its window check is on the capture's own times, not the clock, so a retry prices at the same snapshot. A trade cut off inside its write is never pushed to Drive (`open_account_writer` pushes only on a clean exit), so the next pull discards it, or the retry completes it under the same IDs. Each completed write's daily totals were committed by `DriveAccountSync` itself. A failed commit inside is `CommitFailed` and still stops the run. |
| exits | close fills, ledger rows and events | **yes** | The same fill IDs, and event IDs per trade, outcome and snapshot or day (`ExitDesk._event`). `apply_fill` refuses a fill on a closed trade, and a closed trade is not an open position, so it is never reviewed again. Each book's own error was already caught per book before R2 (see the gap below). |
| trade_marks | `trade_marks.csv` and the equity row of the day | **yes** | Both replace the day's own rows (`write_trade_marks`, `_replace_equity_row`), and the values come from the committed snapshot, so a rerun gives the same bytes. Nothing is committed. |
| O1's day steps (quotes, owner_timing, reviews, quotes_done, the commands) | - | no | In production each is wrapped in `Alerted`, which records its failure itself, without a `retry` key, before `_run_step` sees it. They stay final, as since O1. A bare `DayStep` reaching `_run_step` (E3's tests only) gets "only the desk's own steps are retried". |

*How a partly written step commits.* A failed step commits only the run log (`outcome.paths` is empty).
- The fills and the exits: each completed account write is pushed to Drive and its daily totals are committed inside
  the step (`DriveAccountSync`). A write cut off by the error is neither pushed nor committed.
- The pack: files written before the error stay uncommitted in the checkout. The pack is not retried; the next
  session's checkout is fresh.
- The snapshot: the capture commits its own record before the gate runs.

*SF2 and judge E's minor 1.* With the decisions step failed by an unexpected error, `fills` is refused "needs
decisions, which failed today", and no fill is made, before or after a rerun. Judge B's plant
`NEEDS = {"fills": ("snapshot",)}` now fails that test.

*The orchestrator's finding (24 Oct, on c9fba7584): any problem status of an input refuses the fills.* `_refused`
counted only a `failed` input, so a `refused` input step would have let the fills run on it. That had no effect
today, because only the fills have `NEEDS` and neither input is ever refused, but it broke "never run on a missing
input". Now an input that has not run, or that has any status `problem_steps` names (failed or refused, O1's one
rule), refuses the fills: "needs snapshot, which was refused today" or "needs snapshot, which failed today".

*Judge E's minor 2.* `DeskSteps.fill` counts the trades whose account write finished (`snapshot_id` in their result).
On an unexpected error after N > 0 of them it raises `StepInterrupted(N)`, caused by the error. `CommitFailed` and
`GitFailed` (`RUN_STOPS`) still pass through unwrapped. The alert says "... FAILED (<type>: <line>) after N trades were
recorded in their accounts; those records stay there, check them; ...". With N = 0 the alert has no such clause.

*Real output sample* (the committed code in a test, fake data, public recorder):
- The committed exits entry after run 1: `{"status": "failed", "reason": "raised:TimeoutError", "retry": true}`.
- The alert: `F&O paper desk 2026-10-16: step exits FAILED (TimeoutError: planted: the Drive read timed out); the run
  goes on, the steps that need it are refused; a rerun today retries it (nothing it wrote is done twice)`.
- After the rerun: `{"book1_rules": {"reviewed": true, "results": [{"trade_id": "t1", "outcome": "closed", "reason":
  "unlisted"}]}}`, with the steps in order versions, pack, decisions, snapshot, fills, trade_marks, exits.
- The fills alert with one trade written: `F&O paper desk 2026-10-14: step fills FAILED (TimeoutError: planted: the
  Drive read timed out) after 1 trades were recorded in their accounts; those records stay there, check them; the run
  goes on, the steps that need it are refused; a rerun today retries it (nothing it wrote is done twice)`.

*Criteria, tests, cases and plants.* Each plant was put into the code, checked to fail the named test, then
restored. All 18 were caught (run on tests/timetable, health, daily, desk and scoreboard).

| Criterion (code) | Tests (good / bad / boundary / empty) | Plant, caught by |
|---|---|---|
| `done` ignores a retry-failed entry (`run_log.py`) | `test_run_log_retry.py`: retry-failed not done; finished, refused, final-failed, command-failed and retry-key-on-ok all done | P1 done counts it: the exits, fills and log tests; P4 the retry key alone reopens a step: `[result5]` |
| `record` replaces only a retry-failed entry, placed last | the same file, and failing twice then succeeding | P2 kept in place: the exits test; P3 any entry replaced: `test_a_step_is_never_recorded_twice` |
| exits retried, nothing doubled | `test_failed_step_retry.py`: written then failed, failed twice, then OK, then never again (good, boundary); failed before any write, then closed once (empty) | P5 exits not retried |
| (round 2, replaced in round 3 by `test_fills_final.py`) fills retried, no trade doubled, alert counts N | the same file, parametrized: 0 trades written (empty), 1 written (N), the rerun replays the written trade with fills and ledger rows unchanged | P6 not retried; P9 no count; P10 count not in the alert; P13 the cause's type lost |
| a failed commit inside the fills still stops the run | `test_a_failed_commit_after_a_trade_was_written_still_stops_the_run` | P15 the fills wrap `CommitFailed` |
| marks retried | `test_a_failed_marking_is_retried_once_and_nothing_else_repeats` | P14 not retried |
| not-safe steps stay failed, and their alert says so | `test_final_step_failures.py`: decisions and snapshot (the fills stay refused, no fill, no second capture), versions and pack (bad) | P7 every failed desk step retried: 4 tests |
| SF2: fills refused naming decisions | `test_a_step_not_safe_to_repeat_stays_failed_and_its_fills_stay_refused[decisions]` | P8 judge B's `NEEDS` without decisions |
| alert says whether a rerun retries | the exits, fills and final tests (`endswith`) | P11 the rerun clause dropped |
| retried on its own day only | `test_a_failed_step_is_retried_on_its_own_day_only` (boundary: the next day) | P16 dropped |
| an input awaiting its retry is "failed" | `test_a_needed_step_awaiting_its_retry_refuses_as_failed_not_as_missing` | P17 called missing |
| an input refused, or with any problem status, refuses the fills (`_refused` through `problem_steps`) | `test_an_input_step_refused_or_with_any_problem_status_refuses_the_fills`: both ok (good); snapshot refused, decisions refused (bad); one refused and one failed, one missing and one refused (boundary); nothing ran (empty) | P18 only a failed input refuses |
| O8 health names it failed, not missing | `test_the_health_check_names_a_step_awaiting_its_retry_failed_not_missing` | P12 listed as not run |

*Gap list (round 2).* Each requirement of SF1, SF2 and judge E's minors has a criterion above, except these, which
are out of scope or open, with why:
- **Open, for the orchestrator: a book's own exits error is not retried.** Judge B's example, a Drive or HTTP
  timeout inside one book's review, is caught per book by `review_exits` (since judge 84). The step finishes OK with
  that book's `error`, so under the ruling ("a step that finished OK never repeats") a rerun does not retry it. The
  next session blocks that book's entries (`_unreviewed`), and its due exits wait a day. SF1 covers only a step-level
  error, such as the pack read. Reasoning only, a fix if wanted: mark such an exits result for a retry. The per-book
  review is idempotent by the same IDs.
- **Open: a retried fills or exits step does not re-run the steps after it.** The marks, E6's reviews and the card
  ran in run 1 and are final. After a retry, a trade opened or closed in the rerun is not in today's marks or equity
  row; the next session's row is right. S2's scoreboard recomputes from the fills and is unaffected. Today's
  scorecard did not see it either.
- **Not changed: the blocked-books alert of the fills is sent again on each retry.** It is information, and the
  books are still blocked.
- **Not changed: the count of trades written is a lower bound.** A trade whose account write itself raised after
  writing locally is not counted. In production that write is never pushed to Drive, so the account does not hold it.
- **Not changed: the private full log keeps a retried step in its first position.** It is git-ignored, and nothing
  reads its order.

*Self-review* (an independent code-review agent on the uncommitted diff only, before the gates), 10 findings:
- **Fixed:**
  - `versions` and `pack` were first in the retried list. They are retried after their readers ran, so they are now
    final, with their reasons.
  - A past day could be retried with `--day`; now the retry is same-day only (P16).
  - `_refused` called an input awaiting its retry "missing" (P17).
  - The alert said "trades written" where a refused entry also counts; it now says "recorded in their accounts".
- **Listed as open above:** the steps after a retried step, and the lower-bound count.
- **Not changed, with why:**
  - The partial result of an interrupted fills step is not in the log. The alert gives the count, and the next
    session's exits read the open trade from the account.
  - The repeated blocked alert, and the full log's order: above.
  - "Literal step names": `_plan` and the readers already key the desk's steps by these literals, so the new list
    uses the same names. A constant for only some of them would be inconsistent.

**Not changed, said plainly:**
- The card's own text (T1's) does not list failed steps. The run's last line already names them ("day done with
  problems: snapshot, fills"), and each failed step is alerted.
- A `BaseException` (a kill, `KeyboardInterrupt`) still ends the run, as it should.

**Round 3 (the owner's ruling, 24 Oct; judges 569.2 SF3 and 570.2 finding 1)** (builder
session_016CU8KFuEEtWAM7ZNnFcKxv, on story/o1-r1r2-step-safety-b)

Both judges found that a fills retry, chosen by a person after 15:15, could open trades hours after `fills_by` with
hindsight. The owner ruled (DESK_DECISIONS, 24 Oct, "1 - A" and "2 - yes"):

*(A) A failed fills step is final for the day* (`fno/desk/daily_run.py`).
- `fills` left `RETRIED_ON_RERUN`, which is now exits and trade_marks only. A failed fills step is logged
  `"retry": false`, so it is done, and a rerun never runs it again. Its alert ends "a rerun today will not retry it:
  failed fills are final for the day: no other new desk trade opens today (fail closed)".
- The exits and the marks still run in the same run after a failed fills step. They review any trade written before
  the error.

*(A, the stopped run, judge 570.2's point 3).* After a stop (decision 47), the fills step has no log entry, so a rerun
runs it. `_too_late` refuses it when two things hold: the run did not record the day's snapshot itself
(`DailyRun.ran_here`), and the clock is past `fills_by`. The limit is 15:20:00 itself: a start at 15:20:00 fills, and
15:20:01 is refused.
- The refusal is logged `refused` (done for the day; even a clock set back never runs the fills). One alert:
  "step fills REFUSED: it is HH:MM:SS, past fills_by 15:20, in a run that did not take the day's snapshot: no fills by
  this run (fail closed); trades recorded before the stop stay in their accounts, check them".
- The public log's code is `desk:FILLS_LATE` (`reason_codes.py`). Round 2's `NEEDS_*` reasons get codes too. Before,
  they showed "unlisted".
- **Why only a run that did not take the snapshot** (the self-review's finding, accepted). Only a person's rerun
  reaches the fills without taking the snapshot itself, and the hindsight risk is that person's choice. The run that
  took the snapshot fills at its prices with no choice in between, even when its own commit ends past 15:20 (on 22 Oct
  the snapshot step ended at 15:21:23). A wall-clock limit on that run would lose a valid day to a slow push.
  - On real days fills started at 15:17:51 to 15:18:12 (19, 21 and 23 Oct, `journal/runs`).
  - A valid snapshot must itself finish by 15:20:00 (`SnapshotInWindow`).
- **The limit is on the step's start.** Its account writes may end a few seconds later, at the snapshot's prices.

*(B) The immediate rerun* (`fno/daily/runner.py`, `CLAUDE.md` step 2b). A Slack alert that was sent is never printed,
so the routine could not see "a rerun today retries it" in the alert. The run's last line now ends "; a rerun today
retries it: <steps>" when a step is marked for a retry, on the run's own day only. CLAUDE.md "Daily desk routine"
step 2b: on that line, run `python -m fno daily run` once more at once, once only, never a rerun chosen later. A
failed fills step is never retried. The routine's time is unchanged (14:05). This is a rule-document change, checked
with the code.

*Judge 570.2's minors.*
- J6: `test_the_written_count_leaves_out_a_blocked_book` has three books: book 1 blocked, book 2 written, and book 3
  failing. The alert counts 1, so `written = len(result)` (which counts 2) fails it.
- **Exit review of a trade opened in a retry: none can be opened.** No retry runs the fills (A). A rerun after a stop
  that does fill (by 15:20:00) runs the fills before the exits in the same rerun (`DAILY_RUN_STEPS` order: fills,
  exits, trade_marks), and the exits never ran in the stopped run. So that trade's exits are reviewed that day.

*Stated limits* (the builder's open points, as both judges asked).
- **A book's own exits error is not retried.** `review_exits` catches it per book and the step finishes OK. That book
  is blocked the next session (`_unreviewed`), and its due exits wait a day. This has been so since judge 84. A fix
  would mark such a result for a retry, and is the orchestrator's call.
- **The marks, E6's reviews and the card are not rerun after a retried exits step.** Today's equity row and the
  card's "exits (failed)" line stay as run 1 left them. The next session's rows are right, and S2 recomputes from the
  fills.
- **The scratchpad restore** (round 2, a shared scratchpad). Round 3's plants ran in their own worktree. Each plant
  was restored with `git checkout --`, then `git status` was clean.
- **A joined refusal reason gets one code.** "needs snapshot, which failed today; needs decisions, which was refused
  today" matches only `desk:NEEDS_REFUSED`. The full text is in the alert and the private log.
- **The late refusal's alert is sent before its commit.** If that commit fails, the run stops, and the next rerun sends
  the alert again.
- **A stop's own alert does not say that a rerun after 15:20 fills nothing.** The refusal's alert says it when it
  happens.
- **The hindsight left open is at most 15:20:00 less the snapshot.** A person who reruns after a stop has seen up to
  about 5 minutes of prices after the 15:15 snapshot. The owner's limit is `fills_by`.

*Criteria, tests and plants (round 3): 15 planted, 15 caught after the code test was added.* Each plant was put in a separate worktree, run on tests/timetable, daily,
desk, scoreboard and health, then restored with `git checkout --`.

| Criterion (code) | Tests (good / bad / boundary / empty) | Plant, caught by |
|---|---|---|
| failed fills final, no trade on a rerun (`RETRIED_ON_RERUN`) | `test_a_failed_fills_step_is_final_and_a_rerun_opens_no_trade`: 0 written (empty), 1 written; the rerun opens nothing, fills and ledger unchanged | K1 fills back in the list: 2 tests |
| its alert says final, no new trade (`NOT_RETRIED`) | the same (`endswith`) | K9 the reason dropped: collection fails |
| rerun after a stop: limit at 15:20:00 (`_too_late`) | `..._at_fills_by_fills_the_rest_once` (good, boundary 15:20:00, replayed and never doubled); `..._past_fills_by_is_refused...` at +1 s, +1 min and 23:50 (bad) | K2 no check; K3 2 minutes of grace; K12 a minute of grace (`<` + 1 min); K11 checked only for a logged step |
| refusal alerted, done for the day, written trades stated | the same: the alert in `alerts.sent`, a clock set back still refused, "stay in their accounts" | K10 no alert |
| the run that took the snapshot is never cut off | `test_the_run_that_took_the_snapshot_fills_even_when_its_commit_ends_past_fills_by` | K13 `ran_here` ignored; K14 `ran_here` never reset between runs: 3 tests |
| the late and `NEEDS_*` reasons have public codes (`reason_codes.py`) | `tests/daily/test_fills_reason_codes.py`: each code, and a joined reason (boundary) | K15 `desk:FILLS_LATE` dropped (it survived the first set; this test was added for it) |
| J6 count | `test_the_written_count_leaves_out_a_blocked_book` | K5 `len(result)` |
| last line names the retried steps, own day only (`runner.py`, `retried_steps`) | `test_rerun_line.py`: exits failed (good), its rerun (boundary), a later day (no line), fills failed (bad: no line, never retried) | K6 no suffix; K7 any day; K8 any failed step |

*Real output sample* (the committed code in a test, fake data):
- Fills failed after one trade: `F&O paper desk 2026-10-14: step fills FAILED (TimeoutError: planted: the Drive read
  timed out) after 1 trades were recorded in their accounts; those records stay there, check them; the run goes on,
  the steps that need it are refused; a rerun today will not retry it: failed fills are final for the day: no other new
  desk trade opens today (fail closed)`. Logged: `{"status": "failed", "reason": "TimeoutError: planted: the Drive
  read timed out", "retry": false}`.
- A rerun after a stop at 15:21:00: `F&O paper desk 2026-10-14: step fills REFUSED: it is 15:21:00, past fills_by
  15:20, in a run that did not take the day's snapshot: no fills by this run (fail closed); trades recorded before the
  stop stay in their accounts, check them`. Public code `desk:FILLS_LATE`.
- The last line after a failed exits step: `day done with problems: exits; a rerun today retries it: exits`.

*Self-review* (an independent code-review agent, given only the diff and the requirement; 10 findings):
- **Fixed:**
  - The limit hit the first run too, so a slow snapshot commit would lose a valid day. It now applies to a run that
    did not take the snapshot, strictly at 15:20:00. That also drops the minute grace and its misleading comment.
  - "No new trades today" was untrue after a stop that had written trades. Production writes the trade before the
    failed commit. The test fake now does the same (`WrittenThenCommitFailing`), and the reason says the trades stay.
  - The late reason showed "unlisted" in the public log; it now has a code, as do `NEEDS_*`.
  - The limit applies at the step's start: now stated in the docstring.
  - Weak tests in `test_rerun_line.py`: the rerun's line is asserted, and a fills retry fails the test.
  - "No other new trade" now says "desk trade": the school's and the lab's paper fills are separate.
- **Stated as limits above:** the alert repeated after a failed commit; the stop alert's wording; the hindsight
  window up to 15:20.

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
