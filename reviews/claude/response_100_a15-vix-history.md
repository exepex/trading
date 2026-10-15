# Response 100: story A15, India VIX full history (builder's claims for the judge)

Branch `story/a15-vix-history` (from `origin/main` e3179f0). Lane 1 (new story, outside service NSE and Drive).

## Verdict first

Built and run for real. **4,019 days, 19 Jul 2010 to 30 Sep 2026**, from 195 NSE month files archived in the owner's
Drive with manifest rows, a derived table in `research/data/vix/`, and committed checks. **The 2008 crash is NOT
covered**: NSE's history serves nothing before 19 Jul 2010 (probed back to Nov 2007), and NSE Indices' own VIX page
refused this cloud session. 2011, 2013, 2016, 2020 and 2024 are covered. Against the VIX closes the repository already
held (2017 on): 0 real differences, 1,488 rounding-only differences, 1 day missing in NSE's history (2 Mar 2024).

## Per criterion (story A15, `docs/stories/A-data-foundation.md`)

| # | Criterion | Code | Test | Evidence |
|---|---|---|---|---|
| 1 | Source and terms named | `research/data/vix/README.md` "Source and terms"; URL `fno/vix_history/source.py:21`; pace `fno/http_pacing.py` (shared 1 s/host) | none (document) | some evidence: URL and pace are facts; the **terms position is reasoning only** (I did not re-read NSE's terms; stated so in the README) |
| 2 | Full range from NSE's first served day; earlier gap stated | `source.py:54` (`first_day` 1 Jul 2010), `cli.py:39-42` (months from first to last ended) | `test_committed.py:18` (first row 2010-07-19, ≥4,019 days, no day twice); `test_month_file.py:24` | strong evidence for 19 Jul 2010 being NSE's first served day from this endpoint (probes below); **the gap 2008 to Jul 2010 is real and stated**, not closed |
| 3 | Derived rows equal the raw files (recomputed) | `verify.py:31-54`, `cli.py` `verify` | `test_table.py:99` (recompute equal; planted value and wrong SHA named; missing day named); `test_committed.py:24` (every row's SHA-256 = manifest row) | strong evidence: `python -m fno vix-history verify` on Drive printed "all 4019 days equal their archived month files" (15 Oct 2026) |
| 4 | Point in time: first_seen_at, append-only, no rewrite, no hole filled, running month never fetched; revisions via A11 | `table.py:57-72`, `table_builder.py:42-64`, `cli.py:41`, `source.py:45`, `sweep.py:59-78` | `test_table.py:37,46,55,89`; `test_month_file.py:24` (last complete month); `test_sweep.py:37,46,51,63` | strong evidence (tests); real sweep: 195 months re-read, 0 new versions |
| 5 | Overlap check vs 2017+ closes, every mismatch listed, never fixed | `checks.py:79-98`, `check_files.py` | `test_checks.py:49`; `test_committed.py:32,38` | strong evidence: `checks/overlap_index_close.csv` 1,489 rows: 1,488 `rounded` (max 0.005), 1 `only_in_index_close` (2024-03-02), 0 `differs` |
| 6 | Gaps recorded, never filled; doubtful levels kept and listed | `checks.py:36-77`, `month_file.py:85` (keeps 0 as published) | `test_checks.py:17,25,37`; `test_month_file.py:44` | strong evidence: `gaps.csv` gap 1, unverified 90, weekend_row 9; `level_flags.csv` 3 rows |
| 7 | Missing/failed download writes nothing and is named; stored file never replaced; resumable | `librarian.py:70-108`, `month_file.py:48-70` | `test_librarian.py:39,48,56,66,74`; `test_month_file.py:63` (9 bad shapes incl. HTML page, cut answer) | strong evidence (tests); real rerun: "195 already archived and checked, 0 uploaded" |
| 8 | No frozen file changes; gates | new package only; `fno/cli.py` +2 lines; `CLAUDE.md` +1 line; `fno/storage/README.md` +1 row | full suite | strong evidence: `git diff --stat origin/main` touches none of the FREEZE-listed files (`fno/constants.py`, `fno/composition.py`, `fno/research_data/*`... all untouched); 3,232 passed; ruff and imports clean |
| - | Behind interfaces, wired only in a composition root | `VixMonthReader` (`month_file.py:40`) and the existing `RawFileSource`, `RawFileStore`; the librarian, builder, verifier and sweep take them as arguments; concrete stores, the NSE session and `NseVixJsonReader` are chosen only in `fno/vix_history/wiring.py` (`cli.py` imports `NseVixHistorySource` only for its first month) | `test_librarian.py`, `test_table.py`, `test_sweep.py` run on fakes and local stores | strong evidence (tests and imports) |

## Real-data evidence (15 Oct 2026, this session)

- Probes of `https://www.nseindia.com/api/historicalOR/vixhistory?from=..&to=..`: windows Nov 2007-Mar 2008, Mar-Apr 2008,
  Aug-Nov 2008, Oct 2008, 2008 (year), 2009 (year), Mar-Jun 2009, Jan-Apr 2010 answer `{"data":[]}`; May-Jul 2010
  answers 10 rows starting 19-JUL-2010. Jul-Dec 2010 answers exactly 70 rows (19 Jul to 25 Oct): **NSE cuts answers at
  70 rows silently**, so the code asks one month at a time and refuses an answer of 70 rows or more. A window of about
  two years answers an HTML "Service Temporarily Unavailable" page with HTTP 200 (refused by the reader). The old path
  `/api/historical/vixhistory` answers the same HTML page.
- The same month read twice: identical SHA-256 (`5dcd17db...` for Mar 2020, a CDN copy), so a later different SHA is a
  real rewrite, not noise.
- NSE Indices (`niftyindices.com/BackPage/BindHistoricalIndiaVixData`, the endpoint its history page calls) answered
  HTTP 302 to an error page for 2008 and for 2024 windows, with and without the page's cookies: blocked or changed;
  not usable from here.
- `ind_close_all_02012013.csv` has no India VIX row; `ind_close_all_04012016.csv` has one. Not a substitute before 2017.
- Drive: `python -m fno vix-history fill` uploaded 195 files (2.4 MB in total); manifest
  `research/data/manifests/india-vix-history.csv` (195 rows; `url` is the exact request).

## Findings for the desk (not bugs in this story)

1. **Statistician / data engineer:** `warmup_closes.csv`'s India VIX (read by F2, the forecasts' resolution and the
   weather) is **rounded to 0.01 on 1,488 days from 2017 to 20 Feb 2025**; NSE's history has the unrounded value
   (VIX moves in 0.0025 steps). Largest error 0.005 points: negligible for levels, but a feature on daily VIX
   *changes* sees rounding noise up to 0.01. Strong evidence (the overlap file). No change made (frozen inputs).
2. **Volatility trader:** NSE's VIX `open` equals the previous close on 3,519 of 3,584 days before 2025 (98%); from
   2025 it is a real open. Any overnight-gap or open-to-close VIX study before 2025 would be measuring nothing. Strong
   evidence (the table).
3. **Risk manager:** VIX peaks in the history: 2011-10-04 close 37.19; 2013-09-03 32.49; 2016-02-11 25.965;
   2020-03-24 83.6075 (high 86.635); 2024-06-04 26.7475. Five stress episodes for calibration instead of one; 2008
   (VIX reportedly near 85-90) is still missing.
4. **Data:** NSE published open, high and low of 0 on 12 Feb and 30 Mar 2021 (close present), and a close below the
   low on 22 Aug 2013. Kept as published, listed in `checks/level_flags.csv`.

## Known limits (said plainly)

- **No VIX before 19 Jul 2010.** To close the 2008 gap the owner (or a laptop session) could try niftyindices.com's
  historical VIX page in a browser and save its CSV; that would be a second source needing its own dataset and check.
  I did not try any third-party copy (not official; would need a decision).
- **Not scheduled.** Ended months are added by running `python -m fno vix-history fill` (I was told not to create
  schedules). Days after 30 Sep 2026 are only in `warmup_closes.csv` (close only) until someone runs it in November.
- **`data-coverage` does not list this dataset** (its coverage is per session; this dataset is per month). Coverage for
  it is `vix-history fill`'s own report and `vix-history verify`.
- **`first_seen_at` is the fill time (15 Oct 2026) for all history**, i.e. when our archive got the rows, not when NSE
  published them. Correct for live point-in-time cutoffs; for backtests a day's value is taken as known at its close.
- **Terms:** not re-read (reasoning only that personal research use is fine).
- A11's `RevisionArchive` looks up the original's SHA-256 by archive file name, but this dataset's manifest rows are
  keyed by NSE's URL (an API query, no file name), so A11 falls back to reading the original from Drive. The sweep
  avoids that by checking the manifest SHA-256 first (`sweep.py`, `fingerprints`); behaviour is the same, only faster.
- The manifest is not committed by the command itself (A9's librarian auto-commits); the CLI prints a reminder. I
  committed it with this story.

## What the judge should test hardest

1. Run `python -m fno vix-history verify` with the Drive settings (recomputes all 4,019 rows; read-only).
2. Probe NSE yourself for a window before 19 Jul 2010 and for a 3-month window (expect the 70-row cut).
3. Plant: change one committed row's close. `vix-history verify` must name the day. `vix-history fill` re-reads only the
   table's last month, so a change in September 2026 prints "table REFUSED (nothing rewritten)" and exits 1; a change
   in an older month is caught by `verify`, not by `fill`.
4. Check 2 Mar 2024 (special session): absent from NSE's history, present in the index-close file (14.99).
5. Confirm the 12 Feb 2021 zero open against NSE directly.
6. Confirm no FREEZE-listed file changed: `git diff --name-only origin/main...story/a15-vix-history`.

---

## Addendum 1: judge 100 findings, the self-review and the quality rules (15 Oct 2026)

Judge 100 (FAIL at 514d43b, 3 should-fix, 3 minor). All three should-fixes are correct; I checked each in the code and
reproduced it with a test before fixing it.

### Should-fixes

| # | Judge's finding | Accepted? | Fix (code) | Proof (test) |
|---|---|---|---|---|
| 1 | `verify` misses rows that are missing | Yes: `verify.py` walked only months the table held | `verify.py` `problems`: walks every month the table holds or the manifest lists, so each archived day the table lacks is named; it also names a day held twice and rows out of order | `test_table.py::test_verify_names_every_day_of_a_month_the_table_lacks_and_a_table_cut_short` (a whole month removed, the end cut, an empty table) and `::test_verify_names_a_day_held_twice_and_rows_out_of_order` |
| 2 | "A month still running is never fetched" has no test | Yes: the judge's M5 survived | `cli.py` `months_to_fetch(start, end, today)`: a pure function used by `fill` and `sweep` | `tests/vix_history/test_cli_months.py`: mid-month, `--to` the running month, the month's last day, the 1st of the next month, an earlier end, a start after the end. The judge's M5 now fails `test_mid_month_the_running_month_is_left_out` |
| 3 | No known-at rule and no session labels in the README | Yes. Response 100's "known at its close" was wrong for a 15:00 decision | README: new sections "When a day's value was known" (after the 15:30 close; a 15:00 decision on d uses d-1 at the latest; `first_seen_at` is archive time, never a known-at time) and "Which sessions the rows are" (9 muhurat, 5 special, 9 pre-2017 weekend rows; select `regular` through the A7 calendar). `checks.py` labels `muhurat_session` and `special_session` in `gaps.csv` | `test_checks.py::test_muhurat_and_special_session_rows_are_labelled`. Committed `gaps.csv`: muhurat 9 (2017-10-19 to 2025-10-21), special 5 (2020-02-01, 2024-01-20, 2024-05-18, 2025-02-01, 2026-02-01) |

### Minors

1. **Sweep silent on a missing original: fixed.** The sweep now names it and exits 1 (`sweep.py` `not_archived`).
   Test: `test_sweep.py::test_a_missing_original_is_named_not_passed_over`.
2. **A11's file-name lookup: left as is.** It is A11's design (`Fingerprint.filename` is the URL's tail); the result
   is correct, as you showed. The sweep's manifest pre-check avoids most Drive reads. This belongs in its own A11 change.
3. **Not scheduled: unchanged.** The README now says every monthly `fill` commit is lane 1 until it is scheduled (your
   point (f)).

### Story text

A15 now has a gap list (quality rule 2). The acceptance criteria name the judge's points:
- criterion 3: missing days are named;
- criterion 4: the known-at rule and the month-range tests;
- criterion 6: session labels, and a sweep that finds a missing original.

### Builder self-review (quality rule 3)

Two independent review agents ran on the diff: one for correctness, one for silent failures.

**Fixed:**
- **A revision against a damaged or missing original crashed the sweep mid-run** (both agents). Now it is kept,
  named and the sweep continues: `sweep.py` `_changes`; test
  `test_a_revision_against_a_damaged_original_is_kept_and_named_and_the_sweep_goes_on`.
- **The table builder never checked a file's SHA-256 against its manifest**, so a month `fill` reported as damaged
  could still enter the append-only table. Now it stops at that month, as it does for a month without a manifest row:
  `table_builder.py` `_add`; test `test_a_month_whose_bytes_differ_from_its_manifest_row_stops_the_table`.
- **A manifest conflict after Drive accepted the bytes** escaped as a traceback. It is now reported as damaged:
  `librarian.py`; test `test_a_manifest_conflict_after_the_save_is_named_not_a_crash`.
- **NSE's 403, 429 and 5xx answers** are raised by the shared `NseArchiveSource._response` as `requests.HTTPError`,
  not `RawSourceUnavailable`, and are not retried. The same goes for Drive sign-in, missing settings, conflicts,
  calendar errors and missing files: all were tracebacks. Now every action stops with one `STOPPED (<error>): ...`
  line and exits 1 (`cli.py` `STOPPING_FAILURES`), and the sweep treats an HTTP refusal as no answer. Tests:
  `test_a_drive_or_setup_failure_stops_with_a_named_line_and_exit_1`, `test_an_http_refusal_is_no_answer_not_a_crash`.
  - **Not fixed here:** the shared A9 code itself (`raw_source.py:123`) affects every dataset. I report it for an A9
    change rather than widen this story.
- **A year after the calendar's last year was called `unverified`.** It is now `calendar_lacks_year` ("add NSE's
  circular"); test `test_after_the_calendars_last_year_a_missing_year_is_named_not_unverified`.
- **The overlap summary said "none" even when nothing was compared.** It now prints the days compared and their range,
  or "NOTHING compared".
- **Smaller fixes:**
  - an empty table file now gets its header, and a file without a final new line is refused rather than glued
    (test);
  - `--from` before Jul 2010 is moved to Jul 2010 (test);
  - an empty month range and an empty table exit 1;
  - `verify` says "no manifest row" rather than "SHA-256 differs" when a row is missing.

**Not changed:**
- the month-name locale (`%b`, fine in the C and English locales of every runner here);
- `first_seen_at` is not recomputable from the files and `verify` does not check it, by design.

### Broken-code proof (quality rule 4)

`mutate.py`, kept in my scratchpad and not committed, plants one mutation at a time and runs `tests/vix_history` with
bytecode writing off. A first run with bytecode on gave false results: the restored file had the same size and mtime
second, so a stale `.pyc` was used.

**25 of 25 caught**, each by the named test:

| Criterion | Mutation | Caught by |
|---|---|---|
| C2 | first month moved to Aug 2010 | `test_without_a_start_it_begins_at_nses_first_month` |
| C3 | `verify` walks only the table's months | `test_verify_names_every_day_of_a_month_the_table_lacks...` |
| C3 | `verify` ignores value differences | `test_recomputing_from_the_archive...` |
| C3 | `verify` ignores the manifest SHA | `test_recomputing_from_the_archive...` |
| C3 | `verify` ignores a day held twice | `test_verify_names_a_day_held_twice...` |
| C3 | the builder ignores the manifest SHA | `test_a_month_whose_bytes_differ...` |
| C4 | a held day may be rewritten | `test_a_day_present_is_never_rewritten` |
| C4 | a hole may be filled from behind | `test_a_hole_is_never_filled_from_behind` |
| C4 | the running month is fetched | `test_mid_month_the_running_month_is_left_out` |
| C4 | a start before NSE's first month is kept | `test_a_start_before_nses_first_month_is_moved_to_it` |
| C4 | appending to a file without a final new line | `test_an_empty_table_file...` |
| C4 | the sweep keeps an error page as a version | `test_an_error_page_is_listed...` |
| C5 | every difference is called rounding | `test_every_disagreement...` |
| C6 | a missing session is not listed | `test_a_session_without_a_row...` |
| C6 | muhurat rows are not labelled | `test_muhurat_and_special_session_rows_are_labelled` |
| C6 | a missing calendar year is called unverified | `test_after_the_calendars_last_year...` |
| C6 | a zero level is not flagged | `test_a_zero_level...` |
| C6 | a missing original is passed over | `test_a_missing_original_is_named_not_passed_over` |
| C6 | the sweep crashes on a damaged original | `test_a_revision_against_a_damaged_original...` |
| C7 | a 70-row answer is accepted | `test_a_file_that_is_not_a_whole_clean_month_is_refused[at the cap]` |
| C7 | a rejected answer is saved | `test_an_answer_that_fails_the_check_is_not_saved` |
| C7 | a damaged stored file is counted as present | `test_a_stored_file_differing_from_its_manifest...` (tightened: `present == []`) |
| C7 | a rerun refetches present months | `test_a_rerun_fetches_only_what_is_missing` |
| C7 | a manifest conflict escapes | `test_a_manifest_conflict_after_the_save...` |
| C7 | the CLI lets a setup failure escape | `test_a_drive_or_setup_failure_stops...` |

### Cases per criterion (quality rule 5)

| Criterion | Good | Bad | Boundary | Empty |
|---|---|---|---|---|
| 3 | recompute equals | changed value, wrong SHA | a cut end | empty table, no manifest row |
| 4 | months asked | a running month asked for | last day of the month, 1st of the next | a start after the end |
| 6 | regular days | gap, closed-day row | muhurat and special sessions, first year after the calendar | no rows |
| 7 | a valid month | HTML, cut answer, conflict | exactly 70 rows | `{"data":[]}` |

### Real output (quality rule 6)

Made by the committed code on 15 Oct 2026, read-only commands, on real data.

`python -m fno vix-history check` (no network):
```
gaps (gaps.csv): gap 1, muhurat_session 9, special_session 5, unverified 90, weekend_row 9
doubtful levels, kept as published (level_flags.csv): not_positive 2, outside_low_high 1
against the index-close VIX closes (overlap_index_close.csv): 2415 days compared (2017-01-02 to 2026-09-30): only_in_index_close 1, rounded 1488
```

`python -m fno vix-history verify` against Drive, with the stricter walk over every manifest month:
```
India VIX table: all 4019 days equal their archived month files
```
(exit 0)

### Gates at the pushed commit

- full suite: 3,251 passed (57 in `tests/vix_history`);
- `ruff check` and `ruff format --check` clean;
- `check_imports` clean;
- record scan on.

The table, the manifest and Drive are unchanged; only `checks/gaps.csv` gained the 14 session-label rows.
