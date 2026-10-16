# Response 270: A20a, NSE's daily F&O ban list and market lots kept point in time (builder's claims)

**Story:** `docs/stories/A20-rules-and-dates.md` (part a) · **Branch:** `story/a20a-fo-masters` (built on the text
branch `story/a20-rules-and-dates`) · **Builder:** session_013u1Ac2N9eRQ8XCYPjwpaat · **Lane:** 1 (NSE, Drive, Slack,
a workflow)

## What it does

`python -m fno fo-masters [--day D]` (workflow `fo-masters.yml`, 07:45 IST, retry 11:15 IST). On a trading day of
NSE's session calendar (`regular` or `special`; a muhurat-only day, weekend or holiday prints "not a trading day",
takes nothing, exits 0):
1. **ban list** `fo_secban.csv` → Drive `raw/nse/derivatives/fo-ban-list/YYYY/MM/DD/` of the trade date its first line
   names (`CurrentSessionTaker`). A copy for an earlier session is refused as **stale**; a later one as from the
   future. Nothing is written in either case.
2. **market lots** `fo_mktlots.csv` → `raw/nse/derivatives/fo-lot-sizes/YYYY/MM/DD/` of today (`SnapshotTaker`).
Each saved file gets its SHA-256 manifest row, committed and pushed by the job. Each step prints one line. Any failed
step (NSE refusal or 404, a damaged or stale copy, Drive, manifest rows not committed) makes ONE #fno-desk alert
naming every failure, and the run exits 1. The alert goes through `StepOutputAlerts`, so the workflow's own failure
line speaks only when the job could not post (a crash). O10's watcher writes the error row for the failed run
(story Design 4; A20 writes no error file).

**Contract master: out (decision with evidence).** NSE serves it dated (`NSE_FO_contract_DDMMYYYY.csv.gz`: 200 for
15 Oct 2026, 1 Sep 2026, 1 Oct 2025), so it is not lost daily. Adding it as a dated dataset would require a year of
committed manifest rows (`tests/test_fingerprints.py`), i.e. a 450 MB live back-fill for no daily loss. Recorded in
`docs/DATA_SOURCES.md` and the story text (3044b66d).

## Claims and evidence

| # | Claim | Evidence |
|---|---|---|
| 1 | Readers accept today's real layouts and refuse damaged ones whole | `fno/research_data/fo_masters.py`; `tests/fo_masters/test_readers.py` (fixtures cut from NSE's files of 16 Oct) |
| 2 | Ban list filed under its trade date; stale and future copies refused, nothing written | `fno/storage/session_filed_taker.py` (`CurrentSessionTaker`, `StaleCopy`); `tests/fo_masters/test_job.py`, first three tests |
| 3 | Non-trading day: nothing taken, no commit, exit 0 | `FoMastersJob.run`; `test_a_non_trading_day_takes_nothing_and_succeeds` |
| 4 | Every step runs after a failure; one alert names every failure; exit 1; rows of what was taken still committed | `test_every_step_runs_and_one_alert_names_every_failure` |
| 5 | A 404 ("NSE does not serve it now") is a failure, never "ok" | `taken`; `test_a_file_nse_does_not_serve_is_a_failure_not_news` |
| 6 | Manifest rows not committed is a failure | `test_manifest_rows_not_committed_is_a_failure` |
| 7 | Moving the source tuples is not a behaviour change (`wiring.py` 348 → 299 lines) | `fno/storage/source_lists.py`; the names stay importable from `wiring.py`; full suite |
| 8 | Live read-only check, 16 Oct 16:41 IST (real NSE fetch through the new source classes and content checks, nothing stored): ban list 74 bytes, trade date 16 Oct, AMBUJACEM, KAYNES, SAIL; lots 47,736 bytes, 219 symbols, NIFTY 65 | this session's log (script not committed) |
| 9 | Gates on the unshallow clone (head after the run_location change): 7429 passed; ruff check and format clean; `check_imports.py` clean; `check_records.py` clean | this session's log |

Test changes outside A20a's files, each because a count or set grew by A20a's sources: `tests/nse_retry/test_policy.py`
(22 → 24 NSE source classes, both new classes are covered by the policy test).

## Honest limits

- **First live run is Monday 19 Oct** (17 and 18 Oct are not sessions); `first_day` of both lists is 19 Oct. Until a
  run's lines and manifest rows exist, the Drive and commit path is proven only by the shared code it reuses
  (`SnapshotTaker`, `SessionFiledTaker`, `GitManifestRecorder`).
- **An empty ban list's exact layout is unseen.** The reader accepts the header line alone; if NSE writes something
  else (e.g. "NIL"), the check refuses it and the job alerts: loud, never silent. Fix with the real file then.
- **Timing:** NSE writes the next session's ban list about 18:12 IST. A run GitHub starts after that would refuse
  tomorrow's list (alerted). Both slots plus GitHub's usual 4-5 h delay end before then.
- First-seen time is the day folder plus the manifest commit time (git), not a stored timestamp: these are daily rules.
- O10's `capture-watch.yml` must list `fo-masters` for the error row (asked of O10's builder via the orchestrator).
- `fno/alerts/run_location.py` is shared with A20b (the same file, byte for byte, on both branches).
