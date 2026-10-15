# Response 108: story A16, 15-minute quote recorder (Groww)

**Branch:** `story/a16-groww-15min` · **Lane:** 1 (new story; Groww, Drive, Slack alerts) · **Story text:**
`docs/stories/A16-intraday-quote-recorder.md` · **Builder:** a builder session for the orchestrator.

## Part 1: story text for the judge's check (quality rule 1)

This commit holds the story text alone (scope, definitions, 15 acceptance criteria, gap list, test plan, the routine
prompt proposal) and step 0's feasibility results. No code is in this commit.

**Step 0, what was measured (live, read-only, 15 Oct 2026, pre-market 07:01-07:07 IST):** strong evidence for what it
covers (direct reads), some evidence for timings (one morning, books empty before the open).
- Groww has NIFTY 50 15-minute candles from 1 Jan 2020 (none earlier; 1,685 of 1,686 calendar sessions to 14 Oct 2026;
  10 Oct 2025 missing; four short days besides muhurat, two of them Groww's own holes on 26 Sep 2025 and 29 Sep 2026).
- A full snapshot is: index quote, near future quote, two chains (1.0-1.1 s each, 108 contracts within 6% per expiry),
  then 216 contract quotes. Sequential quotes take 0.79 s each (170 s in all); Groww started failing near 10 requests a
  second, so the recorder paces at 5 a second with 4 workers: about 45-50 s a snapshot.
- The index quote's `last_trade_time` was empty before the open. Whether Groww fills it during the session decides how
  staleness is measured. **This is the one open feasibility question**; the in-session check after 09:15 IST will be
  added to the story as an amendment, and if Groww gives no index time, the story will say what replaces it (a
  candidate measured then: the latest 1-minute index candle's time) before any criterion depends on it.

**Points the judge may want to weigh (my own doubts, stated plainly):**
1. Scheduled tasks here have a minimum interval of about one hour, so the routine proposal is an hourly routine running
   a 55-minute loop (seven fires a session-day), not 26 fires. Untested as a routine: reasoning only.
2. The heartbeat checker is not truly independent: it can only run as another Claude routine (same platform). Said in
   the story; a real second host is a later decision.
3. The near future's symbol form (`NIFTY26OCTFUT`) was checked for October 2026 only.
4. `fno/storage/wiring.py` is at 345 of 350 lines, so A16's store is built in its own composition root from
   `build_owner_drive` instead of in the storage root that design 2.1 names.
5. The candle back-fill (2020-2026) is left out on purpose and proposed as A16b: a candle-close RV is a different
   measure from a quote-snapshot RV, and protocol v4 (G6) should decide whether and how to use it.
6. The CLAUDE.md gate `pip install -r requirements-groww.txt` fails in this container (the SDK's old dependencies
   `clint` and `args` do not build); I installed `growwapi` with `--no-deps` plus its other dependencies. The tests do
   not need the SDK (fakes).

## Part 1b: answer to judge 108 (FAIL on db26fd7, 5 should-fix): all five accepted, story text revised

Each point was checked against the design and the code path it names before accepting.

1. **Freshness rule undefined: accepted.** The rule is now in Definitions: Groww's index `last_trade_time` first; if
   empty, the end of the latest 1-minute index candle (one extra read-only call, minute resolution; at a mark the
   latest finished candle ends at the mark, so the age is about the call latency); neither means stale
   (`index_time_missing`). The basis used is recorded per mark (`index_time_basis`). The in-session check will be a
   short amendment saying which branch Groww's data takes. Evidence for the fallback: step 0 read 1-minute index
   candles (376 for 14 Oct, 0.87 s); whether the latest minute appears within seconds of its end is part of the
   in-session check (reasoning only until then).
2. **Repeat = stale biases the RV: accepted.** My rule voided exactly the calm intervals, biasing kept sessions upward
   and spending the 5% void budget on calm days. Now staleness is decided by source time only; a repeated level is the
   flag `index_repeated` and voids nothing.
3. **Trigger not reliable enough, prompt cannot run: accepted, with one addition.** Overlapping fires at HH:00 to
   HH+1:05; duplicates are harmless by the first-version store and the ledger's one-row rule (tested in criterion 1);
   the tested install line (the `--no-deps` workaround, as the orchestrator asked) replaces `-r
   requirements-groww.txt`; a 5-session measured trial before live (criterion 15); the consequence above 5% (new
   version, host back to the owner, alternatives listed for the owner). Addition: the routine session's maximum length
   is not documented anywhere I could read, so the trial measures it; that is stated, not guessed.
4. **Deny-list over one folder: accepted.** A `ReadOnlyGroww` allow-list wrapper is the only Groww object the source
   holds; tests cover refusal of every other SDK name, the source's only path, and a grep over the whole import
   closure. Checked now: no order, position, holdings or margin call name appears anywhere in `fno/` today.
5. **Drive failure undefined: accepted.** `failed` with `drive_write: <type>`, the document dropped (never in the
   repository or a spool in the checkout), the loop goes on, the streak rule alerts; Drive settings added to the
   routine's prerequisites.

Minor 1 (process): stated plainly. I wrote code locally before the check, and after the orchestrator's "stop" (sent
07:45 IST) I kept fixing it until about 08:03 IST, because I had not yet read that message; I read it at 08:04 and
stopped. That code was pushed only to `wip/a16-groww-15min-code` (not for review, so the session's work is not lost);
nothing there is claimed as evidence. After this text passes, the code will be changed to match it (repeats as flags,
the allow-list wrapper, the candle fallback, `drive_write`) and every proof will be re-run on the pushed code.
Minor 2: GitHub's push receipt of each heartbeat commit is now named as the off-platform witness the post-mortem
reads. Minor 3 (A16b priority) is for the orchestrator.

## Part 1c: answer to judge 108 addendum 1 (FAIL on 83f3614, should-fixes A and B): both accepted

- **A, fallback level and time from two calls: accepted.** Checked: in my rule the level came from the quote and the
  time from a separately fetched candle, so a frozen quote beside a live candle feed would pass; that is the exact
  failure the staleness rule exists for. Of the judge's two options I chose the first: in fallback the level is the
  latest finished 1-minute candle's close (`candle_1m_close`) and its time that candle's end, one record for both. Why
  not the low-high range check: a frozen quote can still sit inside a calm minute's range, so it would pass for the
  wrong reason. Candle times are IST text with no offset; parsed as naive ISO with +05:30 set explicitly, an offset or
  bad text is `index_parse`. The RV row counts marks per basis, so a mixed session is visible.
- **B, two checkouts appending one daily file: accepted.** Checked: each routine fire is its own clone, so both runs at
  HH:00 append to the same CSV and the pull conflicts every hour (or, merged, gives two rows). Now: one file per mark
  (and per RV session and per revision index row); only the run whose Drive write made the first version writes a
  taken mark's row; each run pulls before settling; a same-path race (both write one mark's `missed` row, or the
  heartbeat) is merged with GitHub's copy winning (`-X theirs`, only in this folder's committer), so the first push
  wins and no push is blocked. Criterion 1's test uses two git clones of one bare repository.

On the judge's process note: correct that I pushed work-in-progress code to `wip/a16-groww-15min-code` before the text
passed. One fact for the record: I wrote none after reading the first FAIL (that code was finished at 08:03 IST; I
read the FAIL and the orchestrator's stop at 08:04). No code has been written since, on any branch.

## Part 2: build claims (code on `story/a16-groww-15min`, story text passed at 27f7b55)

`main` merged in (3b27a0b). Code in `fno/intraday/` (22 modules, the largest 209 lines), one refactor in
`fno/providers/groww.py` (`listed_expiries`, so the expiry list is read through the read-only wrapper; the provider
uses the same function, its tests unchanged and passing), and `fno/storage/manifest_commit.py` (its own commit
message, label, a refusal without `core.hooksPath`, `merge --abort` after a failed pull, and the opt-in "first push
wins" merge for write-once folders; the manifests' behaviour and texts are unchanged and their tests pass).

### Per criterion: code, test, broken-code proof (quality rules 4-5)

Every mutation below was applied to the committed code, the named tests were run, the failure was seen, and the code
was restored (`scratchpad/mutate.py`, run with bytecode caching off; result: **39 of 39 caught**, one of them as a
hang, stated). A note on method: a first run with caching on left one stale `.pyc` behind (a mutation and its restore
had the same size within one second), which made 4 clock tests fail afterwards; caches were cleared and every proof
re-run with `python -B`, so no result rests on a stale file. Strong evidence for
what the tests cover; the live parts rest on the dry run below (some evidence).

| Criterion | Code | Tests (good, bad, boundary, empty) | Mutation caught |
|---|---|---|---|
| 1 26 marks; overlap | `slots.py:9-27`, `recorder.py:79-122` | 26 marks exactly; late start 121 s missed, 120 s taken; >15 min early nothing; already recorded; two clones racing (`test_two_clones.py`) | 26->25; 120->121; first-version writer; pull before settling; `-X theirs` (wiring test, and the two-clone test fails without it); one file per mark |
| 2 calendar | `recorder.py:83-85` | holiday, Sunday, muhurat, special Saturday, outside the calendar | session check weakened |
| 3 Drive, revisions, `drive_write` | `first_version_store.py:37-63`, `recorder.py:166-178` | same bytes no-op; different bytes to revisions with one index file; second copy writes no row; Drive raising at one mark, loop goes on | revision skipped; `drive_write` raised |
| 4 content | `groww_source.py:55-79`, `expiry_plan.py:40-55` | 6% band both ends; two chains; expiry day; late December merge; failed broker list | band 5%; second chain dropped |
| 5 gaps, statuses | `settle.py:28-60`, `status.py:46-90` | missed rows by the next run; failed never retaken; empty chain per chain; repeats only flagged; empty session 26 missed | missed rows skipped; repeat flag removed; empty-chain check removed; retake guard removed (hang) |
| Definitions: source time (+ amendment 1) | `index_reading.py:54-79`, `groww_source.py:81-97` | quote time first; frozen quote beside live candles uses the candle; forming candle's close never used; 09:15 open of the candle at the mark; a candle after the mark never the open; no candle stale; 120 s fresh / 121 s stale; offset or bad text is `index_parse`; host TZ=America/New_York still IST | candle level; forming candle; 09:15 open rule; offset accepted |
| 6 realised variance | `realised_vol.py:47-61`, `session_rv.py:34-104`, `rv_table.py:36-48` | hand computation; units 0.0001 = 1%; void per part; 25/27 levels refused; write once and conflict; void share; muhurat skipped; `rv` refuses unfinished and holiday | 25 intervals; overnight; void rule; write once; unfinished |
| 7 streak alert | `streak.py:25-62`, `settle.py:62-70` | two in a row; one alone nothing; exactly 60 min sent; held then sent after the streak ended; failed send retried | 2->3; gap 0; any alert counted |
| 8 clock | `clock.py`, `document.py:23-25`, `status.py:85-90` | 5.0 ok, 5.01 skew; unchecked; UTC strings; source ahead 5.0 / 5.001 | limit 6; non-UTC; tolerance 6 |
| 9 heartbeat | `heartbeat.py`, `recorder.py:194-202`, `cli.py:76-90` | 30 min boundary; 09:45/15:45 edges; GitHub copy fetched; unreadable copy silent; last mark kept on no-take runs | 31 min; no fetch |
| 10 read-only, secrets | `read_only.py`, `groww_source.py:112-118`, `cli.py:62-67` | every SDK name outside the list refused before sign-in; only the wrapper held; import-closure grep (31+ modules); planted secrets absent from files, rows, alerts, output | allow-list off; exception text kept; an order name in the closure |
| 11 no prices in the repository | `ledger.py:17-21` | every value of every repository file checked: no level, nothing price-sized | a level written to a row |
| 12 wiring | `wiring.py` | concrete classes built only in the root | a store built in `settle.py` |
| 13 CLI | `cli.py` | exit codes; dry run outside the repository; catch-all names the class and alerts; dry run sends nothing | exit codes; catch-all alert removed |
| 14 gates | | see below | |
| 15 trial before live | story text | (an operational criterion: no code) | |

### Self-review (quality rule 3)

Two independent review agents (correctness; silent failures and secrets) read the code before the story check. They
found 3 blocking and about 15 should-fix points; all were fixed and are in this code: a crash path that skipped the
ledger, alert and heartbeat; `rv` on an unfinished day writing a permanent void row; a failed Slack send blocking the
streak alert; a held alert dropped; an empty chain counted good; a dry run able to alert or archive NSE files; the
heartbeat check reading the host's own copy; the committer stuck mid-merge or running without hooks; late-December
single chain; timeouts on every call. My own test run then found an endless loop (a failed mark retaken forever),
fixed. Not fixed, by choice: an alert can be sent twice if the ledger write fails right after it (rare; a duplicate
alert is safer than a lost one).

### Gates (at the pushed SHA)

`git config core.hooksPath` = `.githooks`; `pip install` as in the story's install line (the `-r
requirements-groww.txt` line fails here, open item); `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q` on the tree merged with `main` (4362a94): **4059 passed**;
`ruff check fno tests tools` clean; `ruff format --check` clean; `python tools/check_imports.py` clean; no file or class
over 350 lines (largest new file 209).

### Amendment 1: what the session showed, and one rule change for the judge

The in-session check (story, Step 0 "In-session check (amendment 1)") found that Groww gives the index no time during
the session either, so the candle fallback is what runs; that the 09:30 mark is `good` through it (source age 0.7 s);
and that **the 09:15 mark cannot be fresh under the passed text** (no session candle has finished at 09:15), which
would void every session's RV. The fix is in the story (amendment 1) and the code: at a mark whose latest finished
candle ends before the mark, the open of the candle starting at the mark, timed at the mark (`candle_1m_open`).
Strong evidence that the gap is real (the 09:15 row below); reasoning only that the open is the right level (an open
is fixed by the first trade and cannot change while the candle forms). **This rule change needs the judge's check**
(quality rule 1); if the judge prefers another rule, the code is one function (`index_reading.candle_reading`).

### Real output sample (quality rule 6)

Made by the committed recorder at 059fd07 (before the 09:15 rule change) in a dry run on live Groww data:
`python -m fno intraday run --until 09:47 --dry-run /tmp/claude-0/a16-dry` started 09:13 IST (raw files under
`/tmp`, outside the repository; no Drive, no Slack, no commit). Ledger rows, times and counts only (they hold no
prices by design):

| mark_ist | status | failures | index_basis | lateness_seconds | index_age_seconds | expected / recorded / two-sided | clock | snapshot finished |
|---|---|---|---|---|---|---|---|---|
| 09:15 | stale | index_time_missing | (none) | 0.8 | (none) | 216 / 216 / 204 | clock_ok*, -0.5 s | 03:45:57 UTC (57 s) |
| 09:30 | good | (none) | candle_1m_close | 0.7 | 0.7 | 220 / 220 / 220 | clock_ok*, 0.0 s | 04:00:53 UTC (53 s) |
| 09:45 | good | (none) | candle_1m_close | 0.7 | 0.7 | 220 / 220 / 220 | clock_ok*, -0.1 s | 04:15:51 UTC (52 s) |

\* Corrected after judge 108 addendum 3: in this run `clock_ok` rested on **Slack alone**. GitHub was never checked
(the old code asked the API root, which answers 400 with no `Date` here, and treated "no answer" as nothing to
report). The figure above is the skew against Slack. Fixed in part 3.

The raw 09:15 document in the dry-run folder is 71,275 bytes (gzip). The 09:15 row is the evidence for amendment 1;
with the change, the same answer (the forming 09:15 candle, held at 09:15:01.5) gives `candle_1m_open` and `good`
(test `test_at_0915_no_session_candle_has_finished_so_the_level_is_the_open_of_the_0915_candle`).

The command's own printed output (the run ended with exit 1, correctly, because the 09:15 mark was bad):

```
09:15 stale: 216 of 216 contracts (204 two-sided), index answered 0.8 s after the mark; failures: index_time_missing
dry run: nothing pulled, committed or pushed
dry run: nothing pulled, committed or pushed
09:30 good: 220 of 220 contracts (220 two-sided), index answered 0.7 s after the mark; failures:
dry run: nothing pulled, committed or pushed
dry run: nothing pulled, committed or pushed
09:45 good: 220 of 220 contracts (220 two-sided), index answered 0.7 s after the mark; failures:
dry run: nothing pulled, committed or pushed
dry run: nothing pulled, committed or pushed
EXIT 1
```

Minor, seen in this output and not fixed in this push: an empty failures list prints as "failures: " rather than
"none" (cosmetic).

### Open items, stated plainly

1. `pip install -r requirements-groww.txt` fails in cloud containers (`clint`, `args`); the story's install line works
   around it; fixing the requirements file is its own lane-1 change.
2. The trial of criterion 15 (5 sessions through the owner's routine) is still to be run; nothing counts as recorded
   history before it.
3. The routine itself is the owner's to set up; no schedule was created.
4. Whether Groww will ever fill the index `last_trade_time` is unknown; both branches are built and tested.

## Part 3: answer to judge 108 addendum 3 (FAIL on a471f44, 2 should-fix): both accepted, as the orchestrator decided

Checked before accepting:
- **Should-fix 1 (two writers, one Drive name):** read `GoogleDriveStore._child` and `GoogleDriveUploadStore.put`:
  `put` looks the name up, then creates; two creates of one name leave two items, and `_child` then raises
  `RawFileConflict` on every read of that name. Real, and my local-folder tests could not show it.
- **Should-fix 2 (clock):** reproduced live: `HttpDateClock("github", "https://api.github.com")` gives
  `clock NOT CHECKED: host vs github (HTTP 400 from github, no Date header ...)` here; the repository path answers.
  My old code also trusted a `Date` on any status. Real.

**Fix 1, orchestrator decision 39 (run-unique names).** Every copy is saved as
`nifty_<day>_<HHMM>_<SHA-256 first 16>.json.gz`: a name unique to its bytes, so two runs never share one, without a run
id to thread through. `SnapshotFiles` (`fno/intraday/snapshot_files.py`) saves copies and resolves reads: a mark's copy
is the one its ledger row names; the next mark's settlement and the realised variance read only through the row. Rule
for a second run at the same mark: each run's row names its own copy; the row first pushed to GitHub is kept (the
committer's same-file rule); the other copy stays in Drive unused. A due mark with copies and no row gets the copy with
the smallest name (fixed). The first-version store and the revisions index are gone (nothing can be written over).
Tests: an `InterleavingDrive` fake with Drive's own look-up-then-create behaviour, where the second run's whole put
lands between the first run's look-up and create: both copies stored under two names, both rows readable, the next
mark's settlement works. **With one shared name (the a471f44 naming, planted as a mutation) that test fails**; the
two-clone test now also checks Drive holds both copies and the kept row names one.

**Fix 2, one shared clock.** `fno/cards/clock.py` moved unchanged to `fno/server_clock.py` (git rename); T1 imports it
under its old name (`fno/cards/clock.py` re-exports the names), so **T1's 63 tests are unchanged and pass**; the GitHub
URL template moved there too, and `DEFAULT_REPOSITORY` to `fno/constants.py` (same value). A16's `ClockCheck` uses
`check_server` (2xx/3xx only), asks GitHub at `api.github.com/repos/<owner>/<name>`, and adds `clock_partial` when one
server answers and the other does not, with the reason printed. Tests: an error answer (400, 404, 500) carrying a
`Date` is ignored; GitHub is asked at the repository path; the wiring's two URLs. **Live, read-only, 15 Oct 2026:**
GitHub (repository path) and Slack both answered, host within 0.0 s of each; the API root still answers 400.

**Minors:**
1. One alert send attempt per settlement (several bad marks settled at once): done, tested, mutation caught.
2. Tests for I18 (equal documents give equal bytes even when the clock moves between them; gzip's own time patched)
   and I22 (a row file is never rewritten; the ledger refuses a second row): done, both mutations caught.
3. `fno/storage/manifest_commit.py` is shared by every manifest job and now refuses to commit without
   `core.hooksPath`. Checked myself: 13 workflows, 12 commit and all 12 set it; `checks.yml` runs tests and commits
   nothing; routines set it per `CLAUDE.md`. Stated here as a change outside A16's own folder.
4. The 09:15 rule's condition is in the story text: in the trial and every weekly post-mortem, each 09:15
   `candle_1m_open` against NSE's official NIFTY 50 open (A1's index-close file), every difference over 0.05 points
   reported, a systematic one is a new version.
5. Cosmetic "failures: " line: left as it is in this push (the orchestrator asked for it only if findings came; they
   did, but it is unrelated to them; it rides the next code change).

**Proofs and gates at this push:** mutations **46 of 46 caught** (run with `python -B`; two stale patterns re-run
after updating them; the "failed mark never retaken" one is caught as a hang). One honest slip while proving: a
`git checkout` I used to undo a hand mutation restored the committed `document.py` and wiped this round's edits to it;
I re-applied them, and the intraday suite (180) and the full gates below ran after that. Full suite on the tree merged
with `main`: **4126 passed**; `ruff check`, `ruff format --check`, `check_imports` clean; largest new file 209 lines.

Open items, unchanged: the `requirements-groww.txt` fix (its own change), the owner's routine, the criterion-15 trial
(with the NSE-open comparison), the cosmetic line above, and the remote `wip/a16-groww-15min-code` branch, which this
session cannot delete (the git proxy refuses the delete).

## Part 4: A16c, the Groww install fix and one clock module (follow-up asked by the orchestrator)

Branch `story/a16c-groww-install` from `main` at 72fc707 (A16 merged). Treated as a small fix, not a new story, so the
change record (`docs/stories/A16-intraday-quote-recorder.md`, section A16c) and the code are in one push; say if the
judge wants the text checked first.

**Evidence for the root cause (strong, reproduced here):**
- `pip install --no-cache-dir --target <empty> "clint==0.5.1"` with the system pip 24.0 fails:
  `AttributeError: install_layout ... Failed to build clint args` (Debian's setuptools 68.1.2 at
  `/usr/lib/python3/dist-packages`, legacy `setup.py` build).
- The same install in a fresh virtual environment (pip 26.2.1) builds both.
- `pip install --no-cache-dir --use-pep517 --target <empty> -r requirements.txt -r requirements-groww.txt`:
  "Successfully built clint nkeys args", every package installed, `import growwapi, pyotp` works from that folder.
- `--use-pep517` inside a requirements file: "Invalid requirement: --use-pep517 / no such option", so it goes on the
  command line, and the file's header says so.

**Proofs:** removing the flag from `CLAUDE.md` makes `tests/test_groww_install_command.py` fail; putting a
`fno/cards/clock.py` back makes `tests/test_server_clock_single.py` fail. T1's 63 tests and A16's 180 pass.

**Rule 8 for A16 (already sent to the orchestrator):** fresh worktree of `main` at 72fc707, `python -m fno intraday
snapshot --dry-run <scratch>` at 11:00 IST: `11:00 good: 220 of 220 contracts (220 two-sided)`, basis
`candle_1m_close`, index age 0.8 s, `clock_ok` (worst 0.0 s, GitHub repository path and Slack), exit 0.

## Part 5: A16d, the official-open comparison moves to 09:14 (orchestrator decision 53)

Branch `story/a16d-open-comparison` from `main`. Text only (story amendment 3); no code, because nothing in the
repository computes this comparison (`grep` for the comparison over `fno/`: none; the criterion-15 trial and the weekly
post-mortem will compute it).

**Independent check first, as asked (read-only Groww 1-minute candles; NSE's index-close files read through the raw
library with no archive, so nothing was written):** 6 random regular sessions, 2 Jul to 5 Oct 2026.

| Session | 09:14 pre-open close minus official open | 09:15 open minus official open |
|---|---|---|
| 2026-07-02 | 0.00 | +10.65 |
| 2026-07-07 | 0.00 | 0.00 |
| 2026-07-29 | 0.00 | 0.00 |
| 2026-08-06 | 0.00 | -8.30 |
| 2026-08-12 | 0.00 | -2.65 |
| 2026-10-05 | 0.00 | -1.00 |

- **Agreed (strong evidence):** the 09:14 pre-open close equals NSE's official open on 6 of 6, so the comparison
  belongs there.
- **Partly agreed:** the claim "the 09:15 open differs on 40 of 40" is not reproduced. In my sample it differed on 4 of
  6 and was equal on 2 of 6. That does not change the decision: a check that compares the 09:15 open with the official
  open would report the normal auction-to-first-trade move as a fault on most days, and could not tell it from a bad
  source.
- Groww's 1-minute index candles start at 09:00 (pre-open) on every sampled day.

**Text changes:** the condition now compares the 09:14 close; the story says plainly, in Definitions and in the step-0
amendment, that the 09:15 level is the first continuous-trading value and NOT NSE's official open, and that the
overnight part therefore includes the auction-to-first-trade move (the "usual open-to-close split" wording was wrong
and is gone). The 09:15 rule itself is unchanged.

### Part 5, correction: the last pre-open candle, not a fixed 09:14 (A16b builder's recount, its 0adc455)

Checked before changing: 6 random sessions 2021-2023 (read-only, same method). Each has a single pre-open 1-minute
candle at **09:07**, none at 09:14; its close minus NSE's official open is 0.00 on 6 of 6; the 09:15 open differs on 6
of 6 (+3.65 to +9.00). With the 6 recent sessions above: 12 of 12 exact for the last pre-open close. So the condition
now reads "the close of the last pre-open 1-minute candle (before 09:15)", a session without one is reported as "no
pre-open value" (never filled from 09:15), and the text carries the recount's 114 of 114 and 67 of 74. My earlier
"4 of 6 differ, 2 of 6 equal" stands for its sample and is consistent with 67 of 74.

## Part 6: A16e story text, the committer commits only A16's own paths (orchestrator decision 63)

Text only, `docs/stories/A16-intraday-quote-recorder.md` section A16e; code follows after judge D's check.

- **Accepted:** the risk is real (strong evidence: code reading). `GitManifestRecorder.commit` runs
  `git add -- research/data/intraday` and `git commit -- research/data/intraday`, so any file in the folder,
  A16b's `rv-candle/` rows included, goes into A16's commit.
- **Partly corrected: "its manifests".** A16 writes no manifest rows. Its Drive store is the bare `AreaStore`
  (`fno/intraday/wiring.py`), not `FingerprintingStore`; each copy's name carries its SHA-256 and the ledger row names
  it. Its own paths are `slots/`, `rv/` and `heartbeat.json` (strong evidence: `ledger.py`, `rv_table.py`,
  `heartbeat.py`). Naming a manifest path would only widen what the run commits.
- **"Refuses if anything else is staged by it":** with explicit pathspecs the run can never stage anything else, so a
  check on its own staging would be dead code. The reachable case is a file someone else staged under the folder; the
  text refuses then (paths named, one alert per run, nothing lost: rows are write-once on disk and go in the next
  commit). Untracked or unstaged stray files are left alone, with no refusal (reasoning only).
- Pathspec boundary checked: `git add -n -- f/rv f/heartbeat.json` adds `f/rv/a` and `f/heartbeat.json` only, not
  `f/rv-candle/b` or `f/heartbeat.json.tmp` (strong evidence: scratch repository).
- Also fixed: the routine prompt's hand-commit line said "commit and push that folder"; it now names the three paths.
- Judge D's queued minor folded in: criterion 15 and the trial paragraph now require per session the pre-open
  comparison (the difference, or "no pre-open value").
- **Raised, not done (out of scope, stated in the text):** `git push origin HEAD` publishes any unpushed local commit
  another writer made on the same checkout (decision 51 (b)'s class). Low risk here: each routine fire is a fresh clone
  (reasoning only). A follow-up could reuse `fno/desk/git_sync.py`'s `other_work` rule; the orchestrator decides.
