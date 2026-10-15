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
