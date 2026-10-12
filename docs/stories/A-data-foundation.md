# Epic A: data foundation

Roles: data and backtesting engineer (owner of the epic), quant researcher, execution specialist, macro economist.
Goal: every number the desk uses comes from complete, verified, point-in-time data. Template and shared definition of
done: `docs/IMPLEMENTATION_PLAN.md`.

---

## A1. Raw NSE archive complete and checked

**User story:** As the data engineer, I want every raw NSE file the research needs stored unchanged in the project's
Drive folder, with a command that lists what is missing or damaged, so that every later result rests on complete,
verified inputs.

**Background:** The owner downloads files on a laptop (NSE serves them freely; the cloud session cannot write to a
personal Drive) and drags them into `fno-research/raw` on Drive. On 12 Oct 2026, 683 of 689 current-format files
were there (6 missing: 1 Jan 2024, the tool started a day late; 5 weekend sessions). The tool now also fetches old-format
F&O (2019 to 5 Jul 2024) and daily index closes with India VIX.

**Scope.** In: the laptop tool (done), a coverage command, the check of the owner's upload. Out: downloading from the
cloud into Drive (impossible with a service account); stock price files (not needed for NIFTY).

**Expected design:**
- New command `python -m fno data-coverage [--from 2019-01-01] [--to today]` in `fno/cli.py`, logic in a new module
  `fno/storage/coverage.py` (under 150 lines) that depends only on `RawFileStore` and the three `NseArchiveSource`
  classes (path naming), wired through `fno/storage/wiring.py`.
- Trading days are taken as the union of days with any F&O file (current or old) plus NSE's published holiday-free
  weekdays; a weekday with no file in any dataset is listed as "no file (holiday?)" for a person to confirm.
- For each dataset and day: present / missing; zip files opened and checked with their internal checksums; CSV files
  parsed (index closes must contain "Nifty 50" and "India VIX").
- Output: a short table per dataset (days expected, present, missing, damaged) and the lists of missing and damaged
  days; exit code 0 when nothing is missing or damaged, 1 otherwise. Never writes to Drive; prints no secrets.

**Acceptance criteria:**
1. Given the laptop tool and an empty folder, when it runs for 2019-01-01 to 2019-01-04, then it saves the old-format
   F&O and index-close files for each trading day under `raw/nse/...` with NSE's original names and bytes, and asks
   no question except the folder. (Done; tested.)
2. Given files already present, when the tool runs again, then no file is downloaded or changed and days known to have
   no file are not requested again. (Done; tested.)
3. Given a Drive folder with one day's old-format file missing and one zip with a flipped byte, when
   `data-coverage` runs, then it lists exactly that missing day and that damaged file and exits 1.
4. Given the owner's complete upload, when `data-coverage` runs for 2019-01-01 to the last download day, then it
   reports 0 missing and 0 damaged for all three datasets, or names each exception with a reason (for example a day
   NSE never published).
5. The command makes only read requests to Drive (verified by a test with a fake Drive that fails on any write).

**Test plan:** unit tests with a fake `RawFileStore` (missing day, damaged zip, damaged CSV, complete set); one real
check against Drive recorded in the conversation log with the command's output.

**Judge verifies:** runs `python -m fno data-coverage` and compares its counts with an independent listing of the Drive
folder (count of files per dataset and year); opens 10 random files and compares their SHA-256 with the laptop
tool's manifest where one exists.

**Depends:** - · **Size:** S · **Status:** doing (tool done and delivered; owner downloading; coverage command next)

---

## A2. One reader for both F&O formats

**User story:** As the quant researcher, I want old-format and current-format NSE F&O files read into the same
columns, so that 2019-2026 research uses one format without converting or altering the originals.

**Background:** NSE published the old format until 5 Jul 2024 and the current UDiFF format from 1 Jan 2024. The old
format lacks the underlying price, lot size, last price, previous close and number of trades.

**Scope.** In: `fno/fo_bhavcopy.py` (`FoFileFormat` interface, `UdiffFormat`, `LegacyFormat`, `read_fo_file`,
`read_index_closes`). Out: stock underlying prices for old files (needs NSE equity files; not needed for NIFTY).

**Expected design:** records keyed by the UDiFF column names in `COLUMNS`; old instrument codes mapped (OPTIDX to IDO,
OPTSTK to STO, FUTIDX to IDF, FUTSTK to STF); dates as ISO strings read without locale; underlying of index
instruments from the same day's index close (NIFTY to "Nifty 50" and the other index names in `INDEX_NAMES`).

**Acceptance criteria:**
1. Given a current-format file, when read, then every record has exactly the `COLUMNS` keys with the file's values.
2. Given an old-format file and that day's index closes, when read, then every record has the same keys; fields the old
   format lacks are empty strings; index instruments carry the index close as underlying.
3. Given any day both formats exist, when both are read, then the set of contracts is identical and open, high, low,
   close, settlement, open interest, change in open interest and contracts traded are equal, traded value within
   Rs 1,000, and underlying equal for index instruments.
4. Given a damaged zip, a file with the wrong columns, an unknown instrument or an unknown file name, when read, then
   `BadFile` is raised and no records are returned.

**Test plan:** `tests/test_fo_bhavcopy.py` with real NSE rows from 2 Jan 2024 in both formats;
`research/2026-10-12-legacy-format/validate_overlap.py` over all overlap days.

**Judge verifies:** re-runs the overlap script and confirms `overlap.json` shows 128 of 128 days identical.

**Depends:** - · **Size:** M · **Status:** done (128 of 128 overlap days identical, 5,793,044 rows)

---

## A3. NIFTY option-chain panel

**User story:** As the quant researcher, I want one table of every NIFTY option on every trading day since 2019 (all
strikes and expiries, with the underlying and India VIX), built from the raw files, so that experiments can price any
structure, including far strikes the old extract lacked.

**Background:** Meeting 1 used an extract limited to 20-55 days to expiry, which lacked far strikes (a "data gap").
Experiment 1 needs every strike of the monthly expiries from entry to exit.

**Scope.** In: NIFTY index options (and NIFTY futures for reference), 2019-01-01 to the last available day. Out: other
underlyings (later stories), intraday data.

**Expected design:**
- Module `fno/research_data/nifty_panel.py` (new package `fno/research_data`, under 250 lines) with
  `build_nifty_panel(fo_libraries, index_library, start, end) -> Panel`, reading through `RawFileLibrary` objects built
  in `fno/storage/wiring.py` (Drive first, NSE for missing files, never writing to Drive).
- For each trading day: the current-format file when it exists, else the old-format file; index closes for that day.
- Output files under `research/data/nifty-panel/`: `options_<year>.csv.gz` with columns `date, expiry, strike, type,
  close, settle, volume, open_interest, underlying, vix, source_format`; and `manifest.json` with, per day, the source
  file name, its SHA-256 and the row count.
- Deterministic: rows sorted by date, expiry, strike, type; fixed column order; gzip written with a fixed timestamp.

**Acceptance criteria:**
1. Given the raw files for a day, when the panel is built, then the number of NIFTY option rows for that day equals the
   number of NIFTY option rows in the source file, and `manifest.json` records the source file's SHA-256.
2. Given a day in 2024 before 6 Jul, when built, then the current-format file is used (`source_format = udiff`); for
   2019-2023 the old format is used (`legacy`).
3. Given the same raw files, when the panel is built twice, then the output files are byte-identical.
4. Given a day with no F&O file, then the day is absent from the panel and listed in the manifest as "no file".
5. Every row's `underlying` equals that day's NIFTY 50 index close and `vix` that day's India VIX close; a day whose
   index file is missing is reported and its rows keep empty `underlying` and `vix`.
6. The panel's 2024-2026 NIFTY rows reproduce the existing extract's rows (same days, expiries, strikes and prices)
   for every contract the extract contains.

**Test plan:** unit tests on two fixture days (one per format); a determinism test (build twice, compare bytes); a
consistency check against `research/2026-10-12-capacity-screen/data/nifty_options.csv.gz` for 2024-2026.

**Judge verifies:** rebuilds the panel from Drive in a fresh checkout and compares SHA-256 of the outputs; spot-checks
5 random days against the raw files by hand-picked contracts.

**Depends:** A1, A2 · **Size:** M · **Status:** next

---

## A4. Daily 3 pm quote recorder

**User story:** As the execution specialist, I want real bid, ask and last prices of NIFTY monthly options near the
money recorded at about 3 pm every trading day, so that the Rs 1 fill-cost assumption can be replaced by measured
spreads and the 3 pm desk can be tested on what it would really have seen.

**Background:** Daily NSE files have no bid or ask. The desk decides at 3 pm. Only recording builds this history, so it
starts before anything else needs it.

**Scope.** In: NIFTY, the nearest two monthly expiries, strikes within 5% of spot, one snapshot a day near 15:00 IST,
storage, a spread report. Out: order placement (never), other underlyings, intraday series.

**Expected design:**
- Class `QuoteSnapshotRecorder` in `fno/live/quote_recorder.py` using the existing `Provider` interface (`chain`,
  `live_quote`); provider chosen in `fno/live/services.py` (Groww when its credentials are in the environment, else
  NSE's public chain).
- Command `python -m fno quotes record` and a scheduled run near 15:00 IST on trading days (same scheduling mechanism
  as the daily brief).
- Each snapshot saved as `raw/groww-or-nse/derivatives/quote-snapshots/<YYYY>/<MM>/nifty_<YYYYMMDD>_1500.csv` through
  a writable store (the repository folder `research/data/quotes/` while Drive is read-only), never overwritten.
- Columns: `captured_at` (IST timestamp), `provider`, `expiry`, `strike`, `type`, `bid`, `ask`, `last`, `bid_qty`,
  `ask_qty`, `spot`.
- Command `python -m fno quotes report` prints the median half-spread (ask minus bid, halved) by distance from the
  money (0-1%, 1-2%, 2-3%, 3-5%) and the share of contracts with no two-sided quote.

**Acceptance criteria:**
1. Given a trading day at 15:00 IST, when the recorder runs, then one file holds every contract of the two nearest
   monthly expiries within 5% of spot with bid, ask, last and capture time.
2. Given a contract with no bid or no ask, then the row is kept with the missing side empty (never filled from last).
3. Given an existing file for that day, when the recorder runs again, then the file is not changed and the run reports
   "already recorded".
4. Given a weekend or exchange holiday, then nothing is recorded and nothing fails.
5. The recorder never calls any order, modify or cancel function (test: the provider fake fails on any such call);
   credentials only from the environment, never written to files or logs.
6. Given 20 recorded days, when `quotes report` runs, then it prints the median half-spread per distance band and the
   count of days and contracts used.

**Test plan:** unit tests with a fake provider (normal day, missing sides, rerun, holiday, forbidden order calls);
first real snapshot attached to the conversation log.

**Judge verifies:** reads three days of snapshots, checks capture times are 14:55-15:05 IST, checks bid at most ask for
every two-sided row, recomputes one day's report by hand.

**Depends:** - · **Size:** M · **Status:** next (start early)

---

## A5. Monthly-expiry identity in the package

**User story:** As the data engineer, I want the rule that identifies NIFTY monthly expiries in the `fno` package
with its tests, so that research and the desk use one tested definition.

**Background:** `research/2026-10-12-capacity-screen/expiries.py` holds `monthly_as_of`: an expiry is monthly if it is
listed that day and was listed more than 50 days ahead on that day or before (handles the 30 Apr 2025 holiday-moved
weekly and the Sep 2025 re-dating).

**Scope.** In: moving `monthly_as_of`, `eligible_monthly` and their tests. Out: changing the rule.

**Expected design:** `fno/research_data/expiries.py`; the research scripts import it; the old file is replaced by an
import so earlier scripts still run.

**Acceptance criteria:**
1. Given the move, when meeting 1's `desk.py` and `variants.py` and the capacity screen are re-run, then their output
   files are byte-identical to the committed ones.
2. The existing expiry tests pass from their new location, including the 30 Apr 2025 and Sep 2025 cases.

**Test plan:** move tests; re-run the three scripts and compare outputs.

**Judge verifies:** `git diff` of the regenerated outputs is empty.

**Depends:** - · **Size:** S · **Status:** next

---

## A6. Events calendar

**User story:** As the macro economist, I want a dated list of RBI policy announcements, Union Budgets and
general-election results for 2019-2026, each with its official source, so that the "event inside the holding
window" condition can be tested without hindsight.

**Background:** Experiment 1's feature F3 needs scheduled events. Using only scheduled, publicly announced dates keeps
the feature knowable at the decision time; unscheduled shocks are not events for this purpose.

**Scope.** In: RBI Monetary Policy Committee decision days (including unscheduled ones, marked), Union Budget days
(including interim budgets), general-election counting days, 2019-2026. Out: state elections, US Fed, company results
(later stories).

**Expected design:** `research/data/events/events.csv` with columns `date, type (rbi_policy | budget |
election_result), scheduled (yes | no), announced_on, description, source_url`; a validator
`fno/research_data/events.py` that loads it and checks types, dates and that `announced_on` is before `date` for
scheduled events.

**Acceptance criteria:**
1. Every row has a source link to the RBI, the Ministry of Finance / India Budget site, the Election Commission or PIB.
2. The file includes 1 Feb 2020 and 1 Feb 2025 (Saturday budgets), 1 Feb 2026 (Sunday budget), 23 May 2019 and 4 Jun 2024
   (election results), and every RBI policy decision day 2019-2026, with unscheduled ones marked "no".
3. The validator rejects a row with an unknown type, a bad date or a missing source.
4. The file is committed before experiment 1's challenge run (its commit precedes the challenge results commit).

**Test plan:** validator unit tests; a count check (RBI decisions per year as published by the RBI).

**Judge verifies:** samples 10 rows and opens their source links; confirms the commit order.

**Depends:** - · **Size:** S · **Status:** next
