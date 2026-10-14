# Response 89: A12 follow-up, a file NSE itself serves truncated (builder's claims for the judge)

Story: A12, judge 51 addendum 5. Builder: Claude, 14 Oct 2026. Branch `story/a12-nse-gaps`, from `main` after the
`2c9be68` merge. Research data only: read-only toward NSE; nothing in Drive is deleted.

## (a) The defect: accepted, fixed

**Checked.** In `FilingsLibrarian._filing`, `NotXbrl` from `archive.save` went to `report.failed`. That company is
never finished, so it was fetched and failed on every run, and its step could never complete. The judge's diagnosis is
right.

**One risk the fix had to avoid.** "Malformed twice" alone cannot mean a gap: an error or block page (HTML) is served
identically twice too. That is NSE refusing us, not a data gap; the existing test
`test_a_file_that_is_not_xbrl_is_never_saved_and_fails_the_run` holds that.

**Fix (minimal):**
- `fno/filings/xbrl.py`: a new `TruncatedXbrl(NotXbrl)`. It is raised when the bytes are not well-formed XML **and**
  the XBRL instance namespace appears in their first 4,096 bytes, as in a cut-off XBRL file such as LAURUSLABS's
  (`<?xml …><xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" …`). An error page never carries that
  namespace, so it stays a `NotXbrl` failure.
- `fno/filings/librarian.py`: on `TruncatedXbrl`, the file is downloaded once more.
  - **Identical bytes** mean NSE's own copy is cut off. It is recorded as a gap: "NSE serves a truncated or malformed
    file for the <period> filing, the same twice (<size> bytes, SHA-256 <hash>): <parser error>". The company
    finishes.
  - **Different bytes, or a failed second download**, mean a download fault. That is a failure, retried next run.
  - The file is never stored either way.
  - A file with no manifest row is fetched again on every run, so a fixed copy NSE publishes later is saved by the
    next run. The gap's SHA-256 shows whether NSE's copy changed.
- The three failure paths now share one `_fail` helper (no duplicated lines).

**Tests** (`tests/filings/test_filings_truncated.py`):
- served twice cut off → a gap with size and SHA-256; the company is finished; nothing is stored; exactly two
  downloads;
- a second download that differs, or fails (HTTP error) → a failure;
- an error page → still a failure, and downloaded only once;
- a fixed copy → saved by the next run;
- `read_facts` → `TruncatedXbrl` only for a cut-off XBRL instance, plain `NotXbrl` for a malformed HTML page.

**Mutations: 7 of 7 caught** (python -B, caches cleared, Slack token unset):
- truncation never detected;
- every malformed file treated as truncated;
- no comparison of the second download;
- the gap without its SHA-256;
- the gap without its size;
- truncation kept as a failure;
- the second download's error escaping.

## (b) "Exit 0 when only the deadline ended": already the behaviour, pushed back with evidence

**Checked in the code, not changed:**
- `_archive` returns `1 if problem else 0`.
- `problem_of` returns "" when the run only stopped at its deadline:
  `if report.stopped and not report.stopped.startswith("deadline")`. The existing test
  `test_filings_manifest_and_runs.py` (`problem_of(stopped, …) == ""`) holds it.
- The second step, `day-lists`, exits 1 only for damaged, rejected or unpublished files. `FillReport.complete` ignores
  how far the deadline let it reach.

**So the daily red runs came from (a):** LAURUSLABS's failure put a line in `report.failures`, and `problem_of`
returned it.

**New test.** `test_a_run_stopped_only_by_its_deadline_with_such_a_gap_needs_nothing_from_the_owner` ties the two
together: a run stopped by its deadline, with LAURUSLABS's truncated file now a gap, gives `problem_of` = "", so exit
0.

**Not built.** An extra "incomplete, resumes" line: the run already prints "result: INCOMPLETE: deadline reached after
N companies; the next run resumes".

## Gates

- On the branch: full suite with `FNO_SLACK_BOT_TOKEN` unset.
- `ruff check fno tests tools`, `ruff format --check`, `python tools/check_imports.py`.
- The numbers are in the message to the orchestrator.

## Judge 51: PASS, with one follow-up (recorded, not built)

- The judge accepted the push-back on (b).
- **Follow-up, accepted in part (my check of the code):** a truncation gap marks the company finished for its step, and `remaining()` skips finished companies, so backfill steps never return to it. A daily run reads the lists for the last `DAILY_LOOKBACK` = 400 days (`FilingsProgress.since`). It downloads every filing in them that is not saved, the gapped one included, so a fixed copy within 400 days is saved by the next daily run. Only gaps on filings older than 400 days (from the backfill steps) are never looked at again, and their rows stay in `gaps.csv` for good.
- **Needed:** a periodic re-check of recorded truncation gaps. It would re-download each such older gap and compare the bytes with the recorded SHA-256. A different, well-formed file is saved and the gap is cleared. The same bytes keep the gap.
- Not built in this story, by the orchestrator's instruction; it is a new story to schedule.
