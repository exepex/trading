# Story REH1: rehearsal mode, a recorded day replayed through every real step

Owner: the O1/O2 builder (session_014zYLf18PgCzR7YoHs1X5Dp). Lane 1 (Drive, Slack and git): two judges, as the
orchestrator set. Ordered by the orchestrator on 24 Oct 2026 from the owner's direct ask:

> "Once all issues are fixed. Then run dry-run again. I want dry-run to be run successfully and generate all type of
> data and reports ... and send to slack for review."

The owner's two choices (through the orchestrator, 24 Oct):

1. Rehearsal data goes to a separate Drive folder, `dryrun/`, which the real system never reads.
2. Reports go to the normal channels: the card and alerts to #fno-desk, the forecast editions to #fno-forecast and the
   intraday lines to #fno-intraday. Every post's first line is bold: "DRY RUN, <day> replay, not a real trading day".

## Why (strong evidence: `docs/dryruns/DRY1_2026-10-23.md`)

DRY1 could check 23 Oct only by re-reading outputs. It could not run the day, for three reasons:
- `daily run` has no dry-run mode (W2);
- every time window is on the wall clock (W1);
- every writer writes the real record (W6).

Its 56 rows are verifications, not a run. REH1 makes "run the day again" one command that is safe by construction, not
by a guard bolted on afterwards.

## The commands

```
python -m fno daily run --rehearse --day 2026-10-23
python -m fno rehearse preopen --day 2026-10-23     # A22's two commands, as the 08:36 routine runs them
python -m fno rehearse morning --day 2026-10-23     # FL1-1d's morning steps (1b and 2)
python -m fno rehearse evening --day 2026-10-23     # FL1-1d's evening steps (1c and 2)
```

Each prints a run id first: `rehearsal <day> <run_id>`, with run_id = UTC time plus 6 hex characters. A rehearsal of
a day that is not a session refuses with one line, as the real run's calendar rule would.

## Design: one rehearsal composition, nothing spread through the steps

**The rule (design for change):**
- Every difference from a real run is an adapter chosen in the composition roots, at the seams O2's end-to-end suite
  already names (`tests/e2e/harness.py`, `OUTSIDE_SEAMS`): the clock, Slack, the owner's Drive, the shared Drive,
  NSE's archive, Groww's capture, the child commands, and the quote store.
- No step, rule or record code asks "am I rehearsing?". A `grep` test pins it: the rehearsal module's name appears only
  in the composition roots and `fno/rehearsal/`.

**How the mode reaches child processes.** `daily run` starts most steps as `python -m fno <command>` children. The
mode is one environment variable, `FNO_REHEARSAL` (name in `fno/constants.py`), set by the rehearsing parent and
inherited by every child. It holds the day, the run id and the replay clock's file. Each composition root that builds
an outside service reads it through one function, `fno/rehearsal/mode.py`'s `rehearsal()`, which returns None in a
real run.

### 1. The replay clock

- **One clock per rehearsal.** It is the real time plus an offset, kept in one file that every process of the
  rehearsal reads (the parent and its children). The offset is set so that the run starts at the routine's time on the
  day: 14:05 IST for the daily run, 08:36 for the pre-open, 08:38 for the morning and 19:53 for the evening.
- **Accelerated waits (reasoning only; owner question Q1).** When the parent waits (the `AnnouncedWaiter`'s waits) and
  no child is inside a capture window, it moves the offset forward instead of sleeping. Every process sees the jump
  together. So a day that takes 14:05-16:05 in real time runs in minutes. Inside a window (14:38-15:13 for the 3 pm
  parts, the 15-minute marks, the pre-open reads) time runs at real speed, so each window behaves as on the day.
- **The seam.** `fno.models.now_ist` gains one injectable clock, set once at process start by the rehearsal wiring.
  This is the single shared change outside the composition roots, and it is a tested, one-line hook. Today's
  `datetime.now(IST)` stays the default.

### 2. Inputs only from the day's recorded, receipted data

- **Drive reads come only from the real root, through a point-in-time reader.** A file is served only if its receipt
  on `main` (O9) was committed before the replay clock's "now".
  - So at 14:05 the rehearsal cannot see the 23 Oct close recorded at 15:40.
  - With no receipt, or a receipt that is too late, the file is "not recorded by <time>", never fetched.
  - The commit times come from git, as O8's push evidence reads them (strong evidence that they exist: O8 and G13b use
    them).
- **Groww's 3 pm and 15:15 captures, NSE's chain, A22's pre-open answers and the 15-minute candles are served by
  recorded-source adapters.** Each implements the same port the live source does (`Provider`, the pre-open sources,
  the candle source) and answers from that day's receipted Drive files. Each answers with the times recorded on the
  day.
- **No live source is reachable.**
  - The rehearsal wiring never builds a Groww, NSE or global-cue HTTP client.
  - A guard adapter on the HTTP layer the sources share refuses any outbound call that is not to Google's Drive read
    or token endpoints, or to Slack's post endpoint.
- **A step whose input was never recorded says so.** It reports `refused` with the code `rehearsal:NOT_RECORDED`
  (O1-status-only's registry), naming the input. It never fetches.

### 3. Every write under `dryrun/<run_id>/`, and git only on a rehearsal branch

**Drive:**
- The rehearsal's owner-Drive store has two parts:
  - a write-once store rooted at `dryrun/<run_id>/`, for every put and every index replace;
  - the point-in-time reader of section 2, for reads of the real record.
- A read checks the rehearsal's own `dryrun/<run_id>/` first, so a step reads what an earlier step of the same
  rehearsal wrote.
- The real root is wrapped read-only: `put` and `replace_contents` raise `RehearsalWriteRefused` before any request is
  made.
- The real system never reads `dryrun/`. A test pins that no real wiring names it.

**Receipts:** receipts are written in the rehearsal checkout, so they go only to the rehearsal branch, never main.

**Git (corrected while building REH1a; reasoning only, for the judges).**
- The rehearsal runs in its own local clone of the checkout, under `~/.fno/rehearsals/<run_id>/`. Its `origin` is a
  local bare repository made from the clone's start, not GitHub.
- So every committer of every step pushes `HEAD:main` exactly as in a real run, but that `main` is the local bare
  one. No committer, and no `Git.target`, needs a rehearsal branch. This replaces the earlier plan of an injectable
  target in four committers: less code, and safe by structure rather than by each committer's care.
- The rehearse command makes the only push to GitHub, at the end: the bare `main` to
  `refs/heads/rehearsal/<day>-<run_id>`. That refspec is built from the rehearsal's own name and checked to start with
  `refs/heads/rehearsal/` before git runs (addition 2).
- **Code as now, data as of the routine's start.** The clone holds today's code. Its data folders (`journal/`,
  `receipts/`, `research/data/`, `research/forecasts/`, `research/ops/`) are restored, with `git restore --source`, to
  the last commit on `main` before the routine's start time on the day. They are committed once in the clone as
  "Rehearsal <day> <run_id>: data as of <time>". So the day's real run outputs are absent and the run starts as it
  did, without reverting commits one by one.
- **The record scan** runs on every rehearsal commit. The clone's `core.hooksPath` is `.githooks`, set and checked
  before the first step, and a commit without `--no-verify` is the only kind any committer makes (O5).
- **The point-in-time reader (section 2)** reads the receipts of the checkout the rehearsal was started from (the real
  record), not the clone's restored ones. So a file the real day recorded at 15:40 is visible to the rehearsal from
  15:40 on.

### 4. Every Slack post labelled

- One decorator per Slack port puts "*DRY RUN, <day> replay, not a real trading day*" as the bold first line of every
  post:
  - `AlertSender` (#fno-desk alerts);
  - `CardPoster` (T1's card);
  - `ReportPoster` (the lab's editions in #fno-forecast);
  - the intraday lines' poster (#fno-intraday).
- Each decorator is a small class in `fno/rehearsal/`, chosen in that port's builder (`build_alert_sender`,
  `build_card_poster`, `build_forecast_poster`, and the intraday builder).

### 5. The guard (acceptance 1-3), in code and in a test

- `fno/rehearsal/guard.py` builds every outside service through the real composition roots with `FNO_REHEARSAL` set,
  and checks four things:
  - every Drive store it gets is the dryrun store, with the real root read-only;
  - every git committer's target starts `rehearsal/`;
  - every Slack sender is a labelled decorator;
  - no live HTTP source was built.
- `daily run --rehearse` and the three `rehearse` commands call the guard before the first step. Any failure stops
  the rehearsal with one line, before anything is written.
- The test plants each of the four breaks and shows the guard catches it.

## What it does not do (said plainly)

- **It cannot replay a source that was never recorded.** For 23 Oct, DRY1 lists these:
  - A22's 09:09 candles (Groww has none);
  - three of A16's marks (the recorder was down 14:15-14:45);
  - Taiex in the global cues.

  Those steps report `rehearsal:NOT_RECORDED`. That is the honest outcome.
- **It does not prove timing under real load.** The accelerated clock skips the waits.
- **It does not test GitHub's push-time checks (W3),** because the rehearsal never pushes to main.
- **It does not replace O11.** O11 is the test suite's replay with fakes, in `tests/e2e_acceptance/`, and it stays.
  REH1 is the production command on the day's real recorded data (split below).

## Split with O11 (one builder per function, to be agreed with session_01FWkBH4zNAEFSEpjUzVEgnd)

- **O11 keeps:**
  - `tests/e2e_acceptance/`: a test-only replay with planted fakes and strict xfails per unbuilt stage;
  - the acceptance list of what is not implemented.
- **REH1 owns:**
  - `fno/rehearsal/`: the mode, the clock, the point-in-time reader, the recorded sources, the label decorators and
    the guard;
  - the composition roots' one-line choices;
  - the `--rehearse` and `rehearse` commands.
- **Shared later, if O11 wants them:** REH1's recorded sources live in `fno/`, so O11's replay can use them in place of
  its own fakes. That is O11's call; REH1 will not edit `tests/e2e_acceptance/`.

## The forecast lab's editions: one composer (agreed with O11's and FL1's owner, 24 Oct)

- `rehearse morning|evening` builds each edition through `fno/forecast_lab/wiring.py`'s `build_composer`, the composer
  the real edition and `lab preview` (FL1-1f) use. REH1 adds no second lab wiring; its label decorator wraps the
  lab's `ReportPoster`.
- So a rehearsal, a preview and the real edition cannot drift apart.
- If REH1 comes to cover all of `lab preview`, the preview can become a thin call into REH1. That needs the FL1
  owner's say first; until then both stay.

## Dependencies

- **O9's read-only index-close fix (DRY1 problem 3)** must land first. Without it, `lab preview` and the lab's close
  source archive a missing file on read. In a rehearsal that write would be refused (section 3) and fail the step,
  rather than write; so REH1's acceptance run waits for that fix.
  - The same holds for the lab's `IndexFileCloses` and `VixSection`, which fetch from NSE and archive a missing file
    (the FL1 owner's note).
  - In a rehearsal both are stopped twice: the HTTP guard refuses the NSE fetch before it is made, and the real
    root's read-only wrapper would refuse the archive write. Nothing is ever written outside `dryrun/`.
  - On a day whose file is not archived, the step reports refused until O9's fix lands.
- **DR1's staging model** does not block REH1. Rehearsal writes go to `dryrun/<run_id>/` and never reach staging or
  the record.

## Owner answers (through the orchestrator, 24 Oct 2026)

- **Q1.** Accelerated clock, as recommended; the windows run at real speed.
- **Q2.** 23 Oct first (the owner's own label).
- **Q3.** Keep the `dryrun/` folders and the `rehearsal/` branches, so the owner can inspect them.

## The orchestrator's three additions (24 Oct)

1. **The AI books.**
   - Book 2 and Book 3 are fired as routines through GitHub Actions, and their answers are sealed through the AI
     transport. Rehearsal never fires a real routine.
   - The HTTP guard refuses every call to Anthropic and to GitHub's trigger and dispatch API.
   - The day's sealed answers are replayed from their receipts by a recorded-source adapter behind the books' fire and
     collect ports. With no sealed answer for the day, the step reports `rehearsal:NOT_RECORDED`.
   - The guard checks that no real routine trigger was built, and a test plants one.
2. **Pushes only under `rehearsal/`.**
   - The rehearsal branch is pushed to origin only as `refs/heads/rehearsal/<day>-<run_id>`.
   - A test shows that no rehearsal path can push any other ref (`main`, another branch, a tag).
   - A check shows that the record scan runs on every rehearsal commit (the hooks path is set, never `--no-verify`).
3. **Something for the owner earlier.** The first labelled rehearsal of the daily run alone (the desk, the card, the
   price ranges and the closes) is posted right after REH1a and REH1b pass. The pre-open, morning and evening routines
   follow with REH1c. Every rehearsal post names the parts not yet in rehearsal.

## Parts and estimate (reasoning only)

- **REH1a, the safe frame:** the mode, the clock, the dryrun Drive store with the read-only real root, the git target,
  the four label decorators, the guard and its test, and `daily run --rehearse` for the steps that read only Drive and
  git (the pack, Book 1, decisions, the G13 family, the card). About 2 days of building, then the judges.
- **REH1b, recorded sources:** Groww's and NSE's 3 pm and 15:15 captures, the candles and the closes, so the quote
  parts, the snapshot, fills, exits and A4h's reads run on the day's data. About 2 days.
- **REH1c, the other routines:** `rehearse preopen`, `morning` and `evening`, with A22's and A17e's recorded sources.
  About 1.5 days.
- **After REH1a and REH1b pass:** the first labelled rehearsal of 23 Oct's daily run alone, posted (addition 3).
- **REH1d:** the first full rehearsal of 23 Oct with every routine, posted to Slack, with a report beside DRY1's
  comparing it row by row. About half a day.

Each part has its own judge rounds. The total is about 6 working days of building, plus judging.

## Acceptance

1. **No real-root Drive write.** With `FNO_REHEARSAL` set, the real root's `put` and `replace_contents` raise before
   any request. Every write lands under `dryrun/<run_id>/`, write-once. Test: a full rehearsal over a fake Drive shows
   the real root's file set unchanged.
2. **No main push.** Every committer's target is `rehearsal/<day>-<run_id>`, and the guard refuses a target of `main`.
   Test: a rehearsal over a local origin leaves `main` unchanged and makes the rehearsal branch.
3. **No unlabelled post.** Every post through each of the four ports starts with the bold label. Test: each port, with
   a planted unlabelled sender, is refused by the guard.
4. **No live source and no real routine.**
   - The rehearsal builds no Groww, NSE or cue HTTP client and no AI routine trigger.
   - The HTTP guard refuses every host but Google's Drive read and token endpoints and Slack's post endpoint
     (Anthropic and GitHub's API included).
   - Test: each planted live call raises, and a planted routine trigger is caught by the guard.
4b. **Pushes only under `rehearsal/`, and the record scan always runs.** Test: a push of `main`, of another branch or of
   a tag from a rehearsal path is refused, and every rehearsal commit ran the hooks.
5. **No look-ahead.** A Drive file whose receipt was committed after the replay clock's now is not served. Test: at
   14:05 the 23 Oct close is "not recorded by 14:05"; at 15:41 it is served.
6. **The recorded day runs.** Over O2's fixture day as a recorded day, `daily run --rehearse` ends `day done` with every
   step that has recorded input, and `rehearsal:NOT_RECORDED` for the rest.
7. **The real run is unchanged.** Without `FNO_REHEARSAL`, every composition root builds what it builds today. The full
   suite passes untouched, and the grep test shows no step reads the mode.
8. **REH1d:** 23 Oct's rehearsal, its Slack posts and its report.

## Claims

### REH1a: the safe frame (for its two judges)

**What is built** (`fno/rehearsal/`; each file has one job, so each builder's import closure holds only its own
service):
- `mode.py`: the rehearsal's day, run id, clock folder and record checkout. It travels in `FNO_REHEARSAL` (a
  non-credential, `tests/live_credentials.py`). It names the branch, the Drive root and the label, whose second line
  lists the parts not yet in rehearsal.
- `clock.py`: the replay clock, one offset file shared by every process. It only moves forward, and each write is
  atomic.
- **One clock for the package.** `fno.models` gains `install_clock`, `now_utc` and `today_local`. The 31 direct
  `datetime.now` / `date.today` reads in 25 modules now go through it, each giving the same value as before in a real
  run. A test forbids a direct read anywhere else (`tests/rehearsal/test_one_clock.py`).
- `process.py`: at `python -m fno`'s start, a rehearsing process installs the replay clock and the HTTP guard. A real
  run does nothing.
- `http_guard.py`: refuses every call but Google's Drive and token endpoints and Slack's posting calls. That covers
  Groww, NSE, the global cues, Anthropic and GitHub's API (addition 1).
  - It checks at `requests`' session (the URL) and at `http.client`'s connect (the host).
  - A refusal is a `RuntimeError`, never an `OSError`. A first version used `PermissionError`, and `urllib` wrapped
    it into an ordinary `URLError`, which callers may retry. The test caught it.
- `drive.py`, `visibility.py`, `drive_wiring.py`: the dryrun store and its point-in-time reader, chosen by
  `build_owner_drive`, the one place an owner Drive store is built.
- `alert_label.py`, `card_label.py`, `report_label.py`: the three Slack ports' label decorators, each chosen by its
  port's builder. The #fno-intraday poster does not exist yet; when it is built, it joins the guard's list.
- `waits.py`: the accelerated waits, chosen in the daily run's composition root.
  - A skip never passes the 3 pm parts' next start, and a running recorder means real speed.
  - If this process's clock is not the replay clock, a wait falls back to a real wait and never spins.
  - `QuoteParts` gains two read-only queries for this: `recording()` and `next_start()`.
- `checkout.py`: the rehearsal's clone, its data as of the routine's start, and the local bare origin. It makes the
  one guarded push of `refs/heads/rehearsal/<day>-<run_id>`.
- `guard.py`: the four builders, plus live-call probes, checked before the first step. It runs in a child with the
  mode set, exactly as a step's process would.
- `daily.py` and `daily run --rehearse`: the calendar check, the checkout, the clock started at 14:05 IST, the guard,
  the unchanged `daily run` in the clone as a child, and the publish.

**Tests** (`tests/rehearsal/`, 26). Each acceptance has a test, and each check of the guard has a planted break:
- acceptance 1: `test_drive.py` and `test_rehearsed_day.py`. The latter runs O2's whole fixture day through the real
  wiring: every Drive write lands under `dryrun/<run_id>/` and the real record is byte-identical;
- acceptance 2 and 4b: `test_checkout.py`, on real repositories. Today's code, the morning's data and no real run in
  the clone. A step's `HEAD:main` lands in the local bare origin. "GitHub" gets only `refs/heads/rehearsal/...`, with
  `main` unchanged. `main`, another branch, a tag and a `..` ref are refused. A guard problem stops before any step
  and publishes nothing;
- acceptance 3 and 4: `test_labels_and_waits.py`, `test_guard.py`, and `test_http_guard.py`, run in a fresh process;
- acceptance 5: `test_drive.py`. The 23 Oct close is not visible at 14:05 and is visible at 15:41;
- acceptance 7: the full suite passes untouched. Without the mode every builder gives what it gives today, and only
  the composition roots know the mode.

**Gates** (branch story/reh1-rehearsal, on main): 14853 passed, 1 skipped, 16 xfailed (pytest -n auto,
FNO_SLACK_BOT_TOKEN unset). ruff check, ruff format --check, check_imports, check_records and check_numbers are all
clean.

**Not in REH1a (said plainly):**
- There are no recorded sources yet. The quote parts, the snapshot, A4h's reads and the candles would reach a live
  source, which the guard refuses. The step then fails loudly and never fetches. REH1b serves them from the day's
  receipted files, with `rehearsal:NOT_RECORDED` where a source was never recorded.
- The shared Drive's raw NSE files (read through the service account, already read-only) are not yet filtered point
  in time. REH1b.
- The AI books' sealed answers are not replayed. In REH1a they are never fired (the HTTP guard), and the daily run
  has no AI step.
- No rehearsal of the real 23 Oct has run yet. It waits for REH1b and O9's read-only index-close fix.

#### REH1a round 2 (judge 557, judge B: FAIL on SF1 and one note; both accepted, checked against the code)

- **SF1, accepted.** Nothing tested that a rehearsing process really installs the replay clock and the HTTP guard.
  Both plants in `process.py` survived, because the guard's probes only asked `allowed()`.
  - Fixed: `python -m fno rehearse check` (`fno/rehearsal/cli.py`, `process_checks.py`) runs inside a process started
    through the package's real entry point with the mode set.
  - It reports a problem unless the process's clock is the replay clock, at the replay time, and a live call is
    refused by `RehearsalCallRefused`. It then adds the builders' checks.
  - `daily run --rehearse` now runs this command, in the rehearsal's checkout, before the first step.
  - Test: `tests/rehearsal/test_process.py` starts that child on 23 Oct's replay clock and expects no problem. Each of
    the two plants fails it (mutation run: `install_clock` → `pass`, and `http_guard.install()` → `pass`).
- **Note, closed in this round (the orchestrator's ask).** The clock test missed `datetime.today()`, `time.time()` and
  aliased imports.
  - It is now an AST check: imports are resolved to their dotted names (`import datetime as d`,
    `from datetime import datetime as dt`, `from time import time as epoch`).
  - It forbids `datetime.now/today/utcnow`, `date.today` and `time.time/time_ns/localtime/gmtime/ctime/asctime`
    anywhere but `fno/models.py`.
  - A planted module with all six forms is caught, while `time.monotonic` and `time.sleep` are not reads.
  - The package has none today.
- Gates on the branch: 14863 passed; ruff, format, imports, records and numbers clean.
- **Judge 560 (judge E), round 1: FAIL on three plants nothing caught; all three accepted, each pinned:**
  - **F1, the HTTP guard installed in a step process.** The same gap as judge 557's SF1, pinned by
    `tests/rehearsal/test_process.py` (above).
  - **F2, `--no-verify` on the clone's data commit.** `check_hooks` proved only the config. Now
    `test_the_clone_s_data_commit_runs_the_record_scan_hook` gives the source a hook that leaves a mark when it runs.
    The clone's data commit must leave it. Plant: `--no-verify` on that commit fails the test.
  - **F3, a crashed guard read as clean.** `_guard` stopped the rehearsal on a non-zero exit only when nothing was
    printed. Now any non-zero exit stops it, whatever was printed: only a clean exit with nothing printed is safe.
    `test_a_guard_that_crashes_or_exits_non_zero_stops_the_rehearsal_whatever_it_printed` covers a crash, a silent
    exit 3 and a clean pass. Plant: ignoring the exit code fails the test.
  - **Minor (for REH1b/c, judge E):** `urllib3` used directly, or raw sockets, would bypass the HTTP guard. Nothing in
    the daily run uses them today. A `urllib3` backstop comes in REH1b's follow-up; raw sockets stay a stated limit.


### REH1b: the recorded sources (for its two judges)

Branch `story/reh1b-sources`, stacked on REH1a (b2e5337d) so REH1a's judges' fixes stay apart. The live sources each
daily step reaches were mapped first, read-only (a search over every step's composition root). Each one now has its
rehearsal form, chosen in the builder that builds it:

| Live source | Step(s) | Rehearsal form | Chosen in |
|---|---|---|---|
| A4's capture: Groww / NSE chain, NSE levels | quotes (3 parts), snapshot | `RecordedRecorder`: the day's recorded attempts, republished byte for byte at their own `finished_at`, with the day's canonical marker; Groww's files from the real Drive checked against their sidecars' SHA-256 | `composition._quote_recorder`, `quotes/index_wiring`, `quotes/window_wiring` |
| NSE's archive (a file missing from Drive) | book1, exits, the recorder's fallback, the index closes | the source's session never sends: `RawSourceUnavailable` "rehearsal:NOT_RECORDED ... (not sent)", no retry, no wait, nothing archived | `storage/wiring.build_nse_source` |
| NSE's index list | close_read, close_recheck | `RecordedCloseList`: the day's raw answer saved at or just after now (15:40 the first, 16:00 the recheck), once the replay clock reaches its save time | `close_read/wiring` |
| Groww's candles | candles | `RecordedCandles`: the day's archived answer for the same window, checked against its manifest row | `intraday/backfill_wiring` |
| GitHub's activity log (push receipts) | premium_ranges, price_ranges, price_range_scores (seals); also the AI collector, v4 packs, health, the card | `LocalPushReceipts`: the rehearsal origin's `post-receive` hook logs each push to main with the replay time | the five `GitHubActivityReceipts` builders |
| Git's commit dates (the wall clock) | every commit: D3's late rule, the seals | a `git` shim first on the rehearsal's `PATH` dates every commit by the replay clock | `rehearsal/daily.py` |

**Also:**
- The guard checks the 3 pm recorder and NSE's session, and probes NSE's archive and GitHub's activity log.
- The run log's registry names `rehearsal:NOT_RECORDED`.
- The label's pending line now names only REH1c.
- The composition-root test uses the repository's own rule: a root is any `wiring.py` or `<part>_wiring.py`.

**Two of my mistakes, said plainly:**
- I committed part 1 (38f9d5ab) with one test red, because a pipe to `tail` hid pytest's exit code. That test is the
  composition-root list, fixed in the next commit. The gates now run through a script that exits with their own
  status.
- The replay clock was started after the checkout, so the origin's first push (the data commit) was logged with no
  offset. It now starts first.

**Tests:**
- `tests/rehearsal/test_recorded_quotes.py` (5): the 3 pm record at its own time with its marker, the 15:15 capture,
  a day with no attempt ending "none", the record never written, and a Groww file whose bytes differ from its sidecar
  refused.
- `test_recorded_closes.py` (3) and `test_recorded_candles.py` (2).
- `test_nse_archive.py` (2): never sent, no retry, no wait.
- `test_git_dates.py` (1): a commit through the shim carries the replay time.
- `test_checkout.py`, push receipts on real repositories.
- `test_guard.py`, with five planted breaks.
- `tests/intraday_backfill/test_read_only.py` still passes: the back-fill's import closure names no trading call.

**Gates** (on main): 14905 passed, 1 skipped, 16 xfailed. ruff, format, imports, records and numbers are all clean.

**Not in REH1b (said plainly):**
- There is no end-to-end rehearsal of a recorded day with these sources yet. O2's fixture harness replaces the same
  seams with its own fakes, so it cannot exercise them. The first whole run is the 23 Oct rehearsal itself, after the
  judges and O9's read-only fix.
- The card does not run. Its `daily.live_from` is null (config.yaml), on 23 Oct and today, so a rehearsal posts no
  card, as the real day posted none.
- The shared Drive's raw NSE files are read as they are now, not point in time. They are published files of past
  sessions, and no step asks for one of the replayed day before NSE publishes it (reasoning only).

#### REH1b follow-up (judge 559, judge B: PASS with notes; judge 560's minor point)

- **REH1a's round 2 merged in:** judges 557 and 560.
- **Note 1, accepted.** Dropping `finished_at >= now` in `RecordedRecorder._next` survived every test. Now
  `test_a_late_execution_capture_is_never_served_an_earlier_attempt` asks for a capture at 15:20 and must get "window
  closed": the 15:15:40 attempt is never passed off as a 15:20 one. Plant: dropping the rule fails the test.
- **Note 2, accepted.** With no Drive set up, `candle_wiring` raised an `AttributeError`. It now says which settings
  to set. `quote_wiring` already returned None, which A4b's store reports with the settings' names.
- **Judge 560's minor point, accepted for `urllib3`.**
  - `urllib3` overrides `http.client`'s connect, and its HTTPS connection has a connect of its own, so `urllib3` used
    directly bypassed the guard. Probed: a `PoolManager` request to NSE was *reached*.
  - The guard now wraps the connect of `http.client.HTTPConnection`, `urllib3.connection.HTTPConnection` and
    `urllib3.connection.HTTPSConnection`.
  - `tests/rehearsal/test_http_guard.py` probes a direct `urllib3` call, which is now refused.
  - Raw sockets stay a stated limit: nothing in the package opens one.

### REH1c: every report, and the other three routines (for its two judges)

Branch `story/reh1c-routines`, stacked on REH1b's c317d9e7.

**1. Every report runs in a rehearsal** (the orchestrator's ruling for the owner, 24 Oct: "all type of data and reports
... send to slack for review").
- A daily-run step that is not live on the replayed day in real runs runs in the rehearsal. Each of its posts carries
  one more line: "not live in real runs yet (live_from unset)", or "not live in real runs on <day> (live from
  <date>)".
- It is chosen in the daily run's composition root (`rehearsed_live`, `rehearsed_not_live`, `fno/rehearsal/
  live_wiring.py`). `config.yaml` and real runs are untouched.
- The line reaches the step's own process and its children through `FNO_REHEARSAL_NOT_LIVE`, only while the step
  runs; the label decorators read it.
- E8's owner-timing fills keep their real date: they change the desk's fills and are not a report.
- On 23 Oct this makes the card, `margin_check` and `premium_range_scores` run. `margin_check`'s command does not
  exist yet (DRY1 row a4), so in a rehearsal it fails and says so: an honest result, not hidden.
- The rehearsal's two variable names move to `fno/constants_operations.py`: one more line put `constants.py` over the
  350-line limit, and the size test caught it.

**2. The other three routines: `python -m fno rehearse preopen|morning|evening --day D`.**
- One runner (`fno/rehearsal/rehearse.py`, formerly `daily.py`) rehearses every routine: the checkout, the clock at the
  routine's start, the guard, the routine's commands, its receipts, and the publish.
- The routines are data (`routines.py`): their start time (14:05, 08:36, 08:38 and 19:53 IST), their commands in
  CLAUDE.md's order (A17e's `global-cues preopen` in the background, as CLAUDE.md's step 3 orders it), and the
  receipts each routine's session commits by hand.
- `test_routines.py` holds every command's name and every receipt path to its routine's own CLAUDE.md section. The
  doc wraps its lines, so the match allows any whitespace.
- One command's failure never stops the next, as in the routines. The receipts are committed through the rehearsal's
  git (dated by the replay clock) with the record scan's hook, then pushed to the rehearsal's origin.

**3. Their recorded sources**, each chosen in its own builder. Each serves the answer the day saved at or just after
now, once the replay clock reaches that time, read from the real record:
- **A22's four parts** (GIFT Nifty, NSE's F&O pre-open list, Groww's NIFTY and BANKNIFTY candles): `RecordedPreopenPart`
  serves `preopen/raw/<day>/<part>_<HHMMSS>.json`, read by the live part's own reader. It is chosen in
  `fno/preopen/wiring.py`.
- **A17e's Yahoo reads:** `RecordedCueSession` serves the copy the day archived, from the record's snapshot logs,
  checked against each row's SHA-256. It is chosen in the cue jobs' one session builder.
- **A16's clock check:** a replay clock is not checked against GitHub's and Slack's servers (it would always read as a
  skew), and the check says so in its warning line. It is chosen in `build_clock_check`.
- **The morning's and evening's NSE archive reads** and A4h's close reads were already covered by REH1b. The lab's
  editions go through FL1's own `build_composer`, with REH1a's labelled poster (agreed with FL1's owner).
- **Lazy Drive.** The recorded sources sign in to Drive at their first read (`record_drive.RecordFiles`), so they are
  built, and the guard checks them, without Drive. A read with no Drive settings names the missing ones.
- **The guard** checks the clock check too.

**Tests:**
- `test_not_live_reports.py` (3): the live dates and the lines, a real run unchanged, and the line present only while
  its step runs.
- `test_routines.py` (3): the commands held to CLAUDE.md; the order, the background command and a failure carried on;
  the receipts committed through the hooks with the routine's paths only.
- `test_recorded_preopen.py` (3), `test_recorded_cues.py` (2) and `test_routine_wiring.py` (3).
- `test_rehearsed_day.py` now pins that O2's fixture day under the mode fails only in the steps not live in real runs
  (the fixture's child commands do not script them), with every Drive write still under `dryrun/`.

**Gates** (on main, 3c7e87ae): 14958 passed, 1 skipped, 16 xfailed. ruff, format, imports, records and numbers are all clean.

**Not in REH1c (said plainly):**
- No routine has been rehearsed against the real record yet. That is REH1d, after the judges and O9's read-only fix,
  on the orchestrator's go.
- The evening's `data-snapshot fii-dii-cash-by-session` reads NSE live, and has no recorded form yet, so in a
  rehearsal it is refused by the HTTP guard: a loud failure, never a fetch.
- The paper accounts are read as they are now (the stated limit from REH1a).
