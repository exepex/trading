# Epic A: data foundation

Roles: data and backtesting engineer (owner of the epic), quant researcher, execution specialist, macro economist.
Goal: every number the desk uses comes from complete, verified, point-in-time data (design sections 6 and 13.1
item 1). Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## A1. Raw NSE archive complete and checked

**Repository:** trading

**Description:** As the data engineer, I want every raw NSE file the research needs stored unchanged in the project's
Drive folder, with a command that lists what is missing or damaged, so that every later result rests on complete,
verified inputs.

**Context and why:** The owner downloads files on a laptop (NSE serves them freely; the cloud session cannot write to a
personal Drive) and drags them into `fno-research/raw` on Drive. On 12 Oct 2026, 683 of 689 current-format files
were there (6 missing: 1 Jan 2024, the tool started a day late; 5 weekend sessions). The tool now also fetches old-format
F&O (2019 to 5 Jul 2024) and daily index closes with India VIX.

**Scope.** In: the laptop tool (done), a coverage command, the check of the owner's upload. Out: downloading from the
cloud into Drive (impossible with a service account); stock price files (not needed for NIFTY).

**Expected design:**
- New command `python -m fno data-coverage [--from 2019-01-01] [--to today]` in `fno/cli.py`, logic in a new module
  `fno/storage/coverage.py` (under 150 lines) that depends only on `RawFileStore` and the three `NseArchiveSource`
  classes (path naming), wired through `fno/storage/wiring.py`.
- Expected trading days come from an **independent, versioned NSE session calendar**, not from the files themselves:
  `research/data/calendar/nse_sessions.csv` (`date, session (regular | special | muhurat), source_url`), built from
  NSE's published annual holiday circulars and special-session circulars (e.g. Budget Saturdays, muhurat trading),
  committed with its sources. Weekdays not in the holiday list are sessions; weekend sessions are listed explicitly.
- For each dataset and expected session: present, checksum-valid (zip internal checksums), schema-valid (required
  columns; index closes contain "Nifty 50" and "India VIX"), or a **documented exception** in
  `research/data/calendar/exceptions.csv` (`dataset, date, reason, source_url`), e.g. a session NSE never published a
  file for. Any gap without an exception fails.
- Output: a short table per dataset (days expected, present, missing, damaged) and the lists of missing and damaged
  days; exit code 0 when nothing is missing or damaged, 1 otherwise. Never writes to Drive; prints no secrets.
- **One calendar for the whole product (design 13.1 item 1):** a small `SessionCalendar` interface in
  `fno/research_data/calendar.py` (`is_session(day)`, `sessions(start, end)`, `previous_session(day)`,
  `next_session(day)`, `session_kind(day)`, `calendar_sha256()`) reads `nse_sessions.csv`; every later component
  (A3, A7, B2, C3, E3, P3) asks this interface, never `weekday()`. Adding `data-coverage` to the CLI is expected
  (the clean-slate command list is a transitional state).

**Acceptance criteria:**
1. Given the laptop tool and an empty folder, when it runs for 2019-01-01 to 2019-01-04, then it saves the old-format
   F&O and index-close files for each trading day under `raw/nse/...` with NSE's original names and bytes, and asks
   no question except the folder. (Done; tested.)
2. Given files already present, when the tool runs again, then no file is downloaded or changed and days known to have
   no file are not requested again. (Done; tested.)
3. Given a Drive folder with one day's old-format file missing and one zip with a flipped byte, when
   `data-coverage` runs, then it lists exactly that missing day and that damaged file and exits 1.
4. Given the owner's complete upload, when `data-coverage` runs for 2019-01-01 to the last download day, then every
   expected session of every dataset is present, checksum-valid and schema-valid, or has a sourced exception row; any
   unexplained gap makes it exit 1.
5. Given a file present on a day the calendar says is a holiday, it is reported as "unexpected file" for review.
6. The calendar file is validated: every holiday and special session has a source link; its commit precedes any
   coverage result that relies on it.
7. The command makes only read requests to Drive (verified by a test with a fake Drive that fails on any write).
8. `SessionCalendar` answers a weekday holiday (not a session), a special Saturday session (a session, kind
   `special`) and a muhurat session (kind `muhurat`) from the file; a day outside the file's covered range raises an
   error instead of guessing.

**Test plan:** unit tests with a fake `RawFileStore` (missing day, damaged zip, damaged CSV, complete set); one real
check against Drive recorded in the conversation log with the command's output.

**Judge verifies:** runs `python -m fno data-coverage` and compares its counts with an independent listing of the Drive
folder (count of files per dataset and year); opens 10 random files and compares their SHA-256 with the laptop
tool's manifest where one exists.

**Depends:** - · **Size:** M · **Status:** done (judge passed, `reviews/judge/judge_18_a1_calendar_coverage.md`)

---

## A2. One reader for both F&O formats

**Repository:** trading

**Description:** As the quant researcher, I want old-format and current-format NSE F&O files read into the same
columns, so that 2019-2026 research uses one format without converting or altering the originals.

**Context and why:** NSE published the old format until 5 Jul 2024 and the current UDiFF format from 1 Jan 2024. The old
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

**Repository:** trading

**Description:** As the quant researcher, I want one table of every NIFTY option on every trading day since 2019 (all
strikes and expiries, with the underlying and India VIX), built from the raw files, so that experiments can price any
structure, including far strikes the old extract lacked.

**Context and why:** Meeting 1 used an extract limited to 20-55 days to expiry, which lacked far strikes (a "data gap").
Experiment 1 needs every strike of the monthly expiries from entry to exit.

**Scope.** In: NIFTY index options (and NIFTY futures for reference), 2019-01-01 to the last available day. Out: other
underlyings (later stories), intraday data.

**Expected design:**
- Module `fno/research_data/nifty_panel.py` (new package `fno/research_data`, under 250 lines) with
  `build_nifty_panel(fo_libraries, index_library, start, end) -> Panel`, reading through `RawFileLibrary` objects built
  in `fno/storage/wiring.py` (Drive first, NSE for missing files, never writing to Drive).
- For each trading day: the current-format file when it exists, else the old-format file; index closes for that day.
- Output files under `research/data/nifty-panel/`: `options_<year>.csv.gz` with columns `date, expiry, strike, type,
  close, settle, volume, open_interest, underlying, vix, source_format, session`; `futures_<year>.csv.gz` (every
  listed NIFTY index future) with columns `date, expiry, close, settle, volume, open_interest, underlying,
  source_format, session`; and `manifest.json` with, per day, the source file name, its SHA-256 and the row counts.
  (`session` = the calendar's session kind, and the futures file, added after judge 14 by orchestrator decision,
  13 Oct 2026.) A build never drops days the existing panel holds: a narrower range is refused.
- Deterministic: rows sorted by date, expiry, strike, type; fixed column order; gzip written with a fixed timestamp.

**Acceptance criteria:**
1. Given the raw files for a day, when the panel is built, then the number of NIFTY option rows for that day equals the
   number of NIFTY option rows in the source file, and `manifest.json` records the source file's SHA-256.
2. Given a day in 2024 before 6 Jul, when built, then the current-format file is used (`source_format = udiff`); for
   2019-2023 the old format is used (`legacy`).
3. Given the same raw files, when the panel is built twice, then the output files are byte-identical.
4. Given a day with no F&O file, then the day is absent from the panel and listed in the manifest as "no file".
5. Every row's `underlying` equals that day's NIFTY 50 index close and `vix` that day's India VIX close.
6. (date, expiry, strike, type) is unique in the panel; a duplicate fails the build.
7. `manifest.json` records, per day, the SHA-256 of both the F&O source file and the index-close file used.
8. **Research-ready gate:** `build` exits with failure, naming the days, if any expected session (A1 calendar) lacks
   its F&O file, NIFTY 50 close or India VIX close, unless the day has a sourced exception; it never silently writes
   empty `underlying` or `vix`.
9. Format precedence is deterministic and tested: on a day with both formats, the current format is used and the
    choice is recorded.
10. The panel's 2024-2026 NIFTY rows reproduce the existing extract's rows (same days, expiries, strikes and prices)
   for every contract the extract contains.

**Test plan:** unit tests on two fixture days (one per format); a determinism test (build twice, compare bytes); a
consistency check against `research/2026-10-12-capacity-screen/data/nifty_options.csv.gz` for 2024-2026.

**Judge verifies:** rebuilds the panel from Drive in a fresh checkout and compares SHA-256 of the outputs; spot-checks
5 random days against the raw files by hand-picked contracts.

**Depends:** A1, A2 · **Size:** M · **Status:** done: judge 20 PASS (13 Oct 2026; claims `reviews/claude/response_38_2026-10-13-a3-nifty-panel.md`)

---

## A4. Daily 3 pm quote recorder

**Repository:** trading

**Description:** As the execution specialist, I want real bid, ask and last prices of NIFTY monthly options near the
money recorded at about 3 pm every trading day, so that the Rs 1 fill-cost assumption can be replaced by measured
spreads and the 3 pm desk can be tested on what it would really have seen.

**Context and why:** Daily NSE files have no bid or ask. The desk decides at 3 pm. Only recording builds this history, so it
starts before anything else needs it.

**Scope.** In: NIFTY, the nearest two monthly expiries, strikes within 5% of spot, one snapshot a day near 15:00 IST,
storage, a spread report. Out: order placement (never), other underlyings, intraday series.

**Expected design:**
- Class `QuoteSnapshotRecorder` in `fno/quotes/recorder.py` (moved from `fno/live/` by the clean-slate cleanup,
  output unchanged) using the `Provider` interface (`expiries`, `chain`, `quote_book`); provider chosen in
  `fno/composition.py` from its own setting `quotes.provider: auto` (Groww when its credentials are in the
  environment, else NSE's public chain).
- Command `python -m fno quotes record` and a scheduled cloud routine near 15:00 IST on weekdays.
- Each attempt saved as `groww/derivatives/quote-snapshots/<YYYY>/<MM>/nifty_<YYYYMMDD>_<HHMMSS>.csv` through a
  writable store (the repository folder `research/data/quotes/` while Drive is read-only), never overwritten.
- Columns (as built): `snapshot_id`, `request_sent_at`, `response_received_at` (IST, machine clock), `quote_time`
  (the provider's own quote timestamp; empty for Groww, which gives none), `age_basis`, `freshness_proxy`,
  `last_trade_time`, `provider`, `contract_id`, `expiry`, `strike`, `type`, `bid`, `ask`, `last`, `bid_qty`,
  `ask_qty`, `spot`, `book_source` (best-bid/offer fields or market depth), `valid`, `invalid_reason`, `raw_sha256`.
  `valid` is true only when bid > 0, ask > 0, bid <= ask, both quantities > 0 and the contract traded today; the
  quote's age is never claimed (see the clarification below). No `quote_age_seconds` column: no source gives it.
- **Attempts, not overwrites:** every run is an immutable attempt saved as
  `nifty_<YYYYMMDD>_<HHMMSS>.csv` with its own sidecar (`snapshot_id` = date and capture time). An incomplete attempt
  may be retried within the capture window (14:55-15:10 IST); no attempt is ever overwritten or deleted. The day's
  **canonical snapshot** is the first complete attempt in the window, recorded in `nifty_<YYYYMMDD>.canonical`
  (or "none" if no attempt completed).
- Each attempt has a sidecar `nifty_<YYYYMMDD>_<HHMMSS>.meta.json`: expected contract count, recorded count, failed
  requests with errors, SHA-256 of every raw provider response, and `complete` (true only if every expected contract
  was recorded).
- Command `python -m fno quotes report` prints the median half-spread (ask minus bid, halved) by distance from the
  money (0-1%, 1-2%, 2-3%, 3-5%) and the share of contracts with no two-sided quote.

**Acceptance criteria:**
1. Given a trading day at 15:00 IST, when the recorder runs, then one file holds every contract of the two nearest
   monthly expiries within 5% of spot with bid, ask, last and capture time.
2. Given a contract with no bid or no ask, a crossed quote (bid > ask), no size, or no trade in the contract today
   (Groww gives no quote timestamp; a same-day trade is the only freshness evidence), then the row is kept, marked
   `valid = false` with the reason, and never counted as executable (never filled from last). A valid row's quote age
   is still unknown and is never claimed.
3. Given a complete canonical snapshot for the day, when the recorder runs again, it records nothing and reports
   "already recorded"; given only incomplete attempts and time left in the window, it makes a new attempt, keeping
   every earlier attempt unchanged; the first complete attempt becomes canonical.
4. Given a weekend or exchange holiday, then nothing is recorded and nothing fails.
5. The recorder never calls any order, modify or cancel function (test: the provider fake fails on any such call);
   credentials only from the environment, never written to files or logs.
6. Given 20 recorded days, when `quotes report` runs, then it prints, per distance band, the median and 90th
   percentile half-spread of valid quotes, the share of invalid quotes, and the count of days and contracts used.
7. Given a partial failure (some requests failed), the snapshot is written with `complete = false` and the run exits
   with an error and alert: never a silent partial success. After the window closes, a day without a complete attempt
   has canonical "none"; it is logged, never back-filled.
8. These are quotes, not fills: the report and the files say so; fill realism is measured later (E1, E3).

**Test plan:** unit tests with a fake provider (normal day, missing sides, rerun, holiday, forbidden order calls);
first real snapshot attached to the conversation log.

**Judge verifies:** reads three days of snapshots and their sidecars, checks request and quote times (a capture
window alone is not proof of a 15:00 price), recomputes `valid` for 20 random rows, recomputes one day's report by
hand.

**Depends:** - · **Size:** M · **Status:** done: judge passed (ChatGPT reviews 15-16, 12 Oct 2026); daily recording from 13 Oct

**Implementation notes (facts found while building; rulings of ChatGPT review 15):** Groww gives each contract's last
trade time but **no quote timestamp**: `quote_time` stays empty, `age_basis` = "unknown: provider gives no quote
timestamp", and the quote's age is never claimed. Freshness proxy for validity, for every Groww book (best-bid/offer
fields or depth): the contract must have traded today (`freshness_proxy` = "same-day trade (market active; quote age
unknown)"); otherwise the row is kept but invalid. Groww's expiry list refuses future years, so when it yields fewer
than two monthlies the recorder takes the listed expiries from NSE's latest daily F&O file of the past 7 days
(`fno/quotes/expiry_listing.py`), records its file, date and SHA-256 in `expiry_source`, and asks Groww's chain by
explicit date (checked to work out to Dec 2028); no recent NSE file means incomplete (fail closed). NSE lists about
three monthlies ahead, so the January monthly appears in NSE's file well before late December.

---

## A5. Monthly-expiry identity in the package

**Repository:** trading

**Description:** As the data engineer, I want the rule that identifies NIFTY monthly expiries in the `fno` package
with its tests, so that research and the desk use one tested definition.

**Context and why:** `research/2026-10-12-capacity-screen/expiries.py` holds `monthly_as_of`: an expiry is monthly if it is
listed that day and was listed more than 50 days ahead on that day or before (handles the 30 Apr 2025 holiday-moved
weekly and the Sep 2025 re-dating).

**Scope.** In: moving `monthly_as_of`, `eligible_monthly` and their tests. Out: changing the rule.

**Expected design:** `fno/research_data/expiries.py`; the research scripts import it; the old file is replaced by an
import so earlier scripts still run.

**Acceptance criteria:**
1. Given the move, when meeting 1's `desk.py` and `variants.py` and the capacity screen are re-run, then their output
   files are byte-identical to the committed ones.
2. The existing expiry tests pass from their new location, including the 30 Apr 2025 and Sep 2025 cases.
3. The rule is point-in-time (it already only uses listings seen on or before each day): a test adds future listings
   to the input and proves no earlier day's classification changes.
4. Re-run outputs are compared both semantically (same cycles, same expiries) and as bytes; the scripts write with a
   fixed column order, so bytes must match too.

**Test plan:** move tests; re-run the three scripts and compare outputs.

**Judge verifies:** `git diff` of the regenerated outputs is empty.

**Depends:** - · **Size:** S · **Status:** done (judge passed in round 2, `reviews/judge/judge_13_a5_monthly_expiry_rejudge.md`)

---

## A6. Events calendar

**Repository:** trading

**Description:** As the macro economist, I want a dated list of RBI policy announcements, Union Budgets and
general-election results for 2019-2026, each with its official source, so that the "event inside the holding
window" condition can be tested without hindsight.

**Context and why:** Experiment 1's feature F3 needs scheduled events. Using only scheduled, publicly announced dates keeps
the feature knowable at the decision time; unscheduled shocks are not events for this purpose.

**Scope.** In: RBI Monetary Policy Committee decision days (including unscheduled ones, marked), Union Budget days
(including interim budgets), general-election counting days, 2019-2026. Out: state elections, US Fed, company results
(later stories).

**Expected design:** `research/data/events/events.csv` with columns `date, type (rbi_policy | budget |
election_result), scheduled (yes | no), announced_on, announcement_source_url, revised_from, description,
source_url`. `announced_on` is the date the event's date was first publicly announced (e.g. the RBI's annual MPC
schedule, the Election Commission's schedule press note), from an independent source, not the event day itself;
`revised_from` records an earlier announced date when the event was moved. A validator `fno/research_data/events.py`
checks types, dates, sources and that `announced_on` is before `date` for scheduled events.

**Acceptance criteria:**
1. Every row has a source link to the RBI, the Ministry of Finance / India Budget site, the Election Commission or PIB.
2. The file includes 1 Feb 2020 and 1 Feb 2025 (Saturday budgets), 1 Feb 2026 (Sunday budget), 23 May 2019 and 4 Jun 2024
   (election results), and every RBI policy decision day 2019-2026, with unscheduled ones marked "no".
3. The validator rejects a row with an unknown type, a bad date, a missing source or a missing announcement source.
4. Unscheduled events (e.g. an unscheduled RBI decision) are kept with `scheduled = no` and `known_on` never returns
   them ahead. (The test that F3 ignores them moved to B1 criterion 6 on 13 Oct 2026: F3 does not exist yet.)
5. (Moved to B5 criterion 8 on 13 Oct 2026: the commit order can only be checked at the challenge run.)

**Test plan:** validator unit tests; a count check (RBI decisions per year as published by the RBI).

**Judge verifies:** samples 10 rows and opens their source links; confirms the commit order.

**Depends:** - · **Size:** S · **Status:** done (judge 11: builder side clean; criteria 4 and 5 moved to B1 and B5, `reviews/judge/judge_11_a6_events_calendar_rejudge.md`)

**Implementation notes (facts found while building):** 61 events (49 RBI policy decisions incl. 3 off-cycle,
10 Budgets incl. 2 interim, 2 election results), every date from a page actually opened; sources and every gap in
`research/data/events/SOURCES.md`. `announced_on` = the earliest page that gave the final date (for RBI April
meetings, the February resolution, earlier than the yearly schedule). Budget announcement dates are **late bounds**
(the earliest official page that could be opened; earlier posts on X could not be opened), which can only make the
event filter treat a Budget as unknown when it was in fact known: never look-ahead, but it may hide a known event for a
few days. For the 2019 and
2020 Budgets no official advance page exists; the announcement source is press (ANI, PTI), labelled in the row. An
upcoming meeting (4 Dec 2026) has its announcement source but no "held" source until it happens; the validator
allows that only for dates after today. Rescheduled meetings keep the earlier date in `revised_from` and, since judge 8
(13 Oct 2026), its first announcement in `first_announced_on`: `known_on` shows a moved meeting at its original date
until the move was public, so a known meeting never vanishes. **Pending outside A6:** criterion 4 (F3 ignores
unscheduled events) is proven when F3 is built (F3's story must test it through `known_on`); criterion 5 (commit order)
is checked when the challenge run is committed.

---

## A7. Every component uses the session calendar

**Repository:** trading

**Description:** As the data engineer, I want the 3 pm quote recorder (and every later scheduled component) to decide
"is today a trading session" from the A1 session calendar, so that a special Saturday session is recorded and a
weekday holiday is never mistaken for a failure.

**Context and why:** Today `fno/quotes/recorder.py` (`record`, line about `WEEKEND_START`) skips every Saturday and
Sunday and treats "no contract traded today" as a holiday. NSE sometimes opens on a Saturday (Budget days, e.g.
1 Feb 2025) and that session would be lost forever: only recording builds quote history. ChatGPT reviews 20-21 and
design 13.1 item 1 require one calendar for A1, B2, E1 and the recorder. The A4 behaviour is judge-passed, so this
change must keep every A4 criterion and the byte-identical baseline (`tests/quotes/test_recorder_baseline.py`).

**Scope.** In: the recorder's trading-day decision; a fail-closed cross-check. Out: changing capture times, columns or
validity rules (A4).

**Expected design:** `QuoteSnapshotRecorder` receives a `SessionCalendar` (A1) through `fno/composition.py`. `record()`
asks `calendar.is_session(today)`; not a session -> "not a trading day" (records nothing). A session day keeps the
existing "no contract traded today" check as a **cross-check**: if the calendar says session but no contract traded,
the attempt is recorded as incomplete with reason "calendar says session, no same-day trades" (never silently
"not a trading day"), and an alert is raised; the day's canonical becomes "none" if this persists to 15:10.

**Acceptance criteria:**
1. Given a special Saturday session in the calendar and a fake provider with same-day trades, the recorder records
   it and writes a canonical snapshot.
2. Given a weekday holiday in the calendar, nothing is recorded and the result is "not a trading day".
3. Given a calendar session with no same-day trades at all, the attempt is kept with `complete = false` and the stated
   reason, the run exits non-zero, and no day is silently skipped.
4. All A4 tests and the four byte-identical baseline scenarios still pass unchanged.
5. A day outside the calendar's covered range fails loudly (no guess).

**Test plan:** extend `tests/quotes/` with calendar fakes for the three cases; run the baseline test.

**Judge verifies:** runs the special-Saturday and holiday tests; confirms the baseline test is untouched and passes.

**Depends:** A1 (calendar) · **Size:** S · **Status:** done (judge passed, `reviews/judge/judge_12_a7_session_calendar.md`)

---

## A8. Positioning data source (participant open interest)

**Repository:** trading

**Description:** As the positioning analyst, I want NSE's daily participant-wise open interest (FII, DII, pro,
client) stored as raw files with point-in-time rules, so that positioning can be studied (edge family E6) and given
to AI roles without look-ahead.

**Context and why:** The old desk's parser was removed in the clean slate (`docs/CLEAN_SLATE_DESIGN.md` section 4);
the design requires a named story before any E6, F2 or AI-book use, with release time, coverage and archive stability
checked. Spot check 12 Oct 2026: NSE's archive served `fao_participant_oi_DDMMYYYY.csv` for 3 Jun 2019, 2 Jan 2020,
3 Jan 2022, 1 Oct 2025 and 9 Oct 2026; full coverage and release times are not verified.

**Scope.** In: a `RawFileSource` for the file, download through the laptop tool and the raw library, coverage check,
a parser, a release-time rule. Out: any trading signal (B6 or a research experiment decides that).

**Expected design:** `ParticipantOiSource(NseArchiveSource)` in `fno/storage/raw_source.py` wired in
`fno/storage/wiring.py`; the laptop tool (`tools/nse_raw_download/`) gains the dataset; `data-coverage` (A1) checks
it; parser `fno/research_data/participant_oi.py` returning per participant long and short contracts by instrument
group; **availability rule:** a day's file is usable for decisions only from the next session's decision time unless
its actual publication time is measured and recorded (a small recorder logs the first time the file is reachable on
each of 20 days; the rule is then set from that evidence and committed).

**Acceptance criteria:**
1. Coverage for 2019 to today reports every session present or a sourced exception; damaged files fail.
2. The parser returns identical numbers to a hand reading of three real files (one per year 2019, 2022, 2026).
3. A look-ahead test proves a decision on day D never sees D's file unless the measured release rule allows it.
4. Raw files are stored unchanged with SHA-256, like A1.

**Test plan:** parser tests with three committed real files; coverage test with a fake store; look-ahead test.

**Judge verifies:** re-reads one file by hand; confirms the release-time evidence file exists before any use.

**Depends:** A1 · **Size:** M · **Status:** partly built; waiting on the owner's Drive upload and 20 measured release days (claims: `reviews/claude/response_40_2026-10-13-a8-participant-oi.md`)

---

## A9. Drive uploads as the owner, and the historical-data librarian

**Repository:** trading

**Description:** As the owner, I want the cloud to upload historical raw files to my Google Drive by itself, in a clear
folder layout, so that no agent needs me at a laptop and no raw data goes into GitHub.

**Context and why:** Owner decisions, 13 Oct 2026:
- static, re-downloadable historical files are stored in Google Drive, never in GitHub;
- agents must work autonomously.

A service account cannot upload: it has no storage quota (tested 13 Oct 2026, HTTP 403 "Service Accounts do not have
storage quota"). The owner therefore created an OAuth Desktop client and consented once (`tools/gdrive_oauth_setup.py`).
The environment holds `FNO_GDRIVE_OAUTH_CLIENT_ID`, `FNO_GDRIVE_OAUTH_CLIENT_SECRET` and
`FNO_GDRIVE_OAUTH_REFRESH_TOKEN` (names in `fno/constants.py`). The app may still be in Google's "Testing" status, in
which case the refresh token expires after 7 days.

The archive layout is `fno-research/raw/<publisher>/<market>/<dataset>/<YYYY>/<MM>/<original name>`
(`fno/storage/README.md`).

**Scope.** In:
- a writable Drive store behind `RawFileStore`, which signs in as the owner from the three settings and refreshes the
  access token; it keeps the archive rules: never overwrite different bytes (`RawFileConflict`), never a duplicate name,
  and folders created as needed;
- wiring, so `RawFileLibrary` archives fetched files straight to Drive;
- a librarian command that fills a dataset's gaps in Drive from its source, politely paced, verifying every file
  against its manifest where one exists, and resumable;
- the first job: upload A8's participant-OI files (1,929 files, verified against
  `tools/nse_raw_download/manifest_participant_oi.csv`);
- an alert to #fno-desk when the token is refused (expired), naming the owner's one-minute fix.

Out:
- choosing new datasets (each needs a story);
- deleting anything in Drive.

**Acceptance criteria:**
1. A real upload works. Write a probe file to `fno-research/_probe/`, read it back byte-identical, and record its
   Drive ID. (A Drive delete is allowed only for that probe file.)
2. Saving the same bytes again changes nothing. Different bytes at an existing path raise `RawFileConflict` and change
   nothing (tests with a fake Drive; one real check).
3. The participant-OI dataset is complete in Drive. `python -m fno data-coverage` reports participant OI 1,929 of
   1,929 present with 0 damaged, and its SHA-256 values match the manifest.
4. The librarian is resumable. A stopped run, when restarted, uploads only what is missing (test).
5. An expired or refused token gives a clear error and an alert naming the fix, never a silent skip (test).
6. No credential value appears in any file, log or message (the record scan stays clean; a test greps the output).

**Test plan:** a fake Drive for create, read, conflict and resume; one real probe; the real participant-OI upload with
coverage.

**Judge verifies:** runs data-coverage for participant OI; opens 5 random files in Drive and compares their SHA-256
with the manifest; plants a different file at an existing path and confirms it is refused.

**Depends:** A1, A8 (manifest) · **Size:** M · **Status:** done: judge 23 PASS (13 Oct 2026); minors 1-2 moved to A10

---

## A10. 2018 warm-up closes, and a fingerprint for every new file

**Repository:** trading

**Description:** As the statistician and the data engineer, I want the 250 trading days before the panel's first
decision day available as index closes, and every newly archived raw file fingerprinted when it is saved, so that F1
and F2 are defined from the first day of the 2019-23 challenge and a damaged new file is never reported as complete.

**Context and why:** B1 (13 Oct 2026) found that F2 needs 250 previous India VIX closes and F1 21 previous NIFTY
closes; the archive starts on 1 Jan 2019, so F2 is `None` for nearly every 2019 decision day, which silently weakens
experiment 1's challenge period for every policy using F2. Judge 23 (A9) minors 1-2: a file with no manifest row is
checked by content only while coverage still says "complete" (true for the current-format F&O file of 12 Oct and every
new day since), and the current-format manifest is the laptop tool's file, stopped at 9 Oct.

**Scope.** In: NSE index-close files (`ind_close_all_DDMMYYYY.csv`) for the 2018 sessions needed as warm-up (NIFTY 50
and India VIX rows are what the features read), their calendar rows, coverage and manifest; SHA-256 recorded at save
time for every raw dataset; one way of producing every manifest. Out: 2018 option or futures outcomes (never needed,
and never to be opened by experiment code: the warm-up is index closes only).

**Expected design:**
- 2018 sessions added to the session calendar from NSE's 2018 holiday circular (sourced, like A1/A7).
- The librarian (A9) fetches, verifies (schema) and archives the 2018 index-close files to Drive under the existing
  layout; a manifest row with SHA-256 is written for each file when it is saved.
- Every raw dataset's manifest is produced by the same code path (A9's fingerprints), so `manifest.csv` (current F&O)
  is regenerated from Drive, never the laptop tool's copy; new files get their row at save time.
- `data-coverage` prints per dataset how many files were checked without a fingerprint, and the result is not
  "complete" while that number is above zero.
- The panel/feature readers can read the 2018 closes as warm-up only; a test proves no 2018 option or futures row is
  read by any experiment code path.

**Acceptance criteria:**
1. Given the 2018 warm-up sessions, `data-coverage` shows the 2018 index-close dataset complete in Drive, 0 missing,
   0 damaged, every file fingerprinted.
2. F2 is not `None` on the first 2019 decision day (2 Jan 2019) and F1 is not `None` on it if its option legs traded;
   both equal hand-computed values from the raw closes (the judge recomputes one).
3. Given a file archived with no manifest row (planted), `data-coverage` reports it as unfingerprinted and the result
   is not "complete"; a file saved through the librarian has its manifest row written in the same operation.
4. `manifest.csv` for current-format F&O covers every session to the latest archived day and is produced by the same
   code as the other manifests (the laptop copy is no longer read).
5. No 2018 F&O option or futures data is read by experiment code (test).
6. Code size, lint, imports, tests pass; raw files only in Drive.

**Judge verifies:** runs data-coverage; recomputes F2 for 2 Jan 2019 from raw India VIX closes; plants an
unfingerprinted file and confirms the result is not complete.

**Depends:** A1, A9, B1 · **Size:** M · **Status:** done: judge 34 PASS (13 Oct 2026)

---

## A11. Revisions of NSE files (NSE rewrites a file after first publishing it)

**Repository:** trading

**Description:** As the data engineer and the statistician, I want every later version of an NSE file archived beside the
first one, never over it, so that research can use exactly what was known at a decision time and publishing can use
NSE's latest version.

**Context and why:** P6 found (13 Oct 2026) that NSE rewrote `ind_close_all_12102026.csv` at 23:20 IST on 12 Oct, adding
two indices; our archived copy is the earlier version. Raw files never change (A1). Orchestrator decision (owner may
override): an append-only revisions area.

**Acceptance criteria:**
1. A later NSE version of an archived file is stored under a revisions area with the same path, a revision timestamp and
   its SHA-256; the raw file is never overwritten (test).
2. A point-in-time reader returns the version available at a given time; a latest reader returns the newest; both are
   tested on the real 12 Oct 2026 index-close case (both versions archived, fingerprints recorded).
3. A8's rewrite sweep stores what it finds as revisions instead of only reporting it.
4. Coverage reports revisions per dataset; code size, lint, imports, tests pass.

**Depends:** A1, A8, A9, A10 · **Size:** S · **Status:** done: judge 48 PASS (13 Oct 2026; claims `reviews/claude/response_54_2026-10-13-a11-revisions.md`)

---

## A12. Company filings archive (Nifty 500, last 3 years, numbers only)

**Repository:** trading

**Description:** As the analyst and the statistician, I want every listed company's filed numbers (results, balance
sheet, cash flow, shareholding, the list of announcements and board meetings) stored in Google Drive by a scheduled job,
so that any rule or prediction can use them point-in-time without calling a third-party server.

**Context and why:** Owner decisions, 13 Oct 2026 (`docs/DESK_DECISIONS.md`):
- every filing of a listed company is research input; one downloader stores the raw files in Drive, and every consumer
  reads only from Drive;
- start with **Nifty 500, last 3 years, numbers only** (no PDFs); later batches of 500 for the rest of NSE, then US
  companies from the SEC's bulk files; older years and PDFs only when a rule needs them;
- polite: about one request per second per site, never bursts;
- the download runs as a plain scheduled job (GitHub Actions; this repository is public, so its runners are free), not
  inside an AI session.

Facts to verify, not assume (reasoning only today): Indian companies file the balance sheet and cash flow every half
year (September and March results), not every quarter; how far back NSE's XBRL results go; whether NSE's filings API
answers from GitHub's runners (if not: BSE's filings, then report).

**Scope.** In:
- a `RawFileSource` per filing type (results XBRL, shareholding XBRL, announcement and board-meeting lists), NSE first,
  BSE as a swappable second source; the company list from the archived Nifty 500 snapshot (P6);
- archive layout under `fno-research/raw/<publisher>/<market>/filings/...` (`fno/storage/README.md`), each file with its
  SHA-256 and the time NSE says it was published (`filed_at`) and the time we first saw it; a revised filing is a new
  version, never an overwrite (A11's rule);
- a resumable librarian job that respects a 6-hour run limit and the one-request-per-second pace;
- a scheduled GitHub Actions workflow: backfill until complete, then daily new filings; failures post to #fno-desk with
  `FNO_SLACK_BOT_TOKEN`;
- a parser that turns results XBRL into a point-in-time table (revenue, profit before tax, net profit, EPS, total
  debt, cash and equivalents, operating, investing and financing cash flow, total assets, equity) read only from Drive;
- a measured sample first (20 companies): real file sizes, counts and history depth, reported before the full run.

Out: PDFs and annual reports; companies outside Nifty 500; US companies; any change to the stock tool's repository.

**Acceptance criteria:**
1. Sample report: for 20 companies, real counts, sizes and earliest available date per filing type, with the
   projection for Nifty 500 (3 years) in GB and hours.
2. The full backfill is in Drive: `python -m fno data-coverage` reports, per filing type, companies covered of 500 and
   files present, with 0 damaged and every file fingerprinted; any company or period NSE does not have is listed with
   the reason, never silently skipped.
3. Point-in-time: the parsed table never returns a filing before its `filed_at` (test with a planted early read); a
   revised filing keeps both versions.
4. Polite and resumable: tests show at most one request per second per host, and a stopped run restarts only what is
   missing.
5. Runs without AI: the workflow runs on schedule in GitHub Actions; the owner's one-time step (adding the Drive
   upload settings as repository secrets) is written as a checklist; no secret value in any file or log (record scan).
6. Half-year balance sheet and cash flow are present for at least 90% of Nifty 500 companies for each of the last 6
   half-years, or the gap is explained with NSE's own data.

**Judge verifies:** opens 10 random archived files and checks their SHA-256 and `filed_at` against NSE; compares 5
companies' parsed revenue, debt and cash flow with the filing; plants an early read and a burst of requests.

**Addendum, 13 Oct 2026 (owner, through the orchestrator):** downloads run only as the scheduled GitHub Actions job,
never in an AI session. Scope: today's Nifty 500, numbers only, as far back as NSE has them, as a work queue kept in a
progress record in Drive: step 1 the last 3 years, step 2 older years, step 3 companies that were Nifty 500 members
in past years (survivorship). Layout: `raw/nse/equities/filings/<category>/<SYMBOL>/<YYYY>/<file>`, later categories
(annual reports, insider trades, pledges, credit ratings, corporate actions) in the same shape; index files (progress,
symbol and ISIN map) in their own area; derived tables in `derived/`. Each run posts one line to #fno-desk with its
files and size and the totals. PDFs stay out; the sample measures their size for a later decision. Builder's status
of each item: `reviews/claude/response_56_2026-10-13-a12-filings-archive.md`, part 5 (step 3 is proposed as its own
story: the membership history comes from NSE Indices' dated press-release PDFs, with no index page).

**Depends:** A9, A11, P6 (Nifty 500 snapshot) · **Size:** L · **Status:** built; awaiting judge (claims: `reviews/claude/response_56_2026-10-13-a12-filings-archive.md`; full backfill running in GitHub Actions)

## A13. NIFTY option panel extends daily

**Repository:** trading

**Description:** As the statistician, I want the NIFTY option panel (A3) to gain each new session's option and future
rows the evening after it closes, so that live forecasts and features that need past implied volatility never go stale
waiting for a manual rebuild.

**Context and why:** Judge 47 addendum 4. G1 protocol v2 (frozen at ab2e811) reads past IV30 from the panel for
question 5's base rate. Its gate `iv30_history_stale` needs option rows up to 21 trading days before the forecast day.
The panel ends on 12 Oct 2026, so from **13 Nov 2026** (the first stale day by the session calendar) Q5's base rate
records "no forecast". O6 already appends the daily closes (`warmup_closes.csv`); this story does the same for the
option and future rows.

**Scope.** In:
- a scheduled GitHub Actions step after NSE's evening F&O file, with no AI session, that adds each new session's NIFTY
  option and future rows using A3's rules (calendar days, the same columns, values copied never rounded, a missing
  file or close fails the day and is named);
- the input is the F&O daily file already archived in Drive (A9), its latest version under A11;
- point in time: rows are only appended after the panel's last day; a day already present is never rewritten. A later
  NSE revision is kept beside the original (A11) and changes past rows only through an A11 revision, named day by day;
- one #fno-desk line when the step fails.

Out: any change to rows already in the panel; any change to a frozen file.

**Design constraint (13 Oct 2026, why the build is stopped):** every way to extend the panel today touches a frozen
file. The owner must choose:
- **Option A: append into the existing panel folder.** A new module writes one new gzip member per year file and adds
  the day's entries to `manifest.json`.
  - No frozen code changes: the reader is unchanged, and `baseline_wiring.py` already reads this folder.
  - But `manifest.json` and the 2026 panel files are experiment 1's frozen inputs (hashes in
    `research/2026-10-12-experiment-1/FREEZE.md`). G1 v1 and v2 record them as "grows with new days" (not
    byte-checked).
  - Two unfrozen G tests would then fail and must be re-scoped to their own date range:
    `tests/forecast/test_golden.py` (a new day is "not in the golden file") and `tests/forecast/test_backfill.py` (the
    back-fill's `pack_sha256` is the manifest's hash at its build).
- **Option B: a separate append-only folder with a new reader module.**
  - Experiment 1's and G2's inputs never change.
  - But wiring the new reader means editing `fno/forecast/baseline_wiring.py`, which is byte-frozen by G1 v2. That needs
    protocol version 3 (text, judge, freeze) before the live capture can read it.

**Acceptance criteria:**
1. After each session the panel holds that session's NIFTY option and future rows, equal to A3's build of the same
   day: a test rebuilds the day with A3's builder and compares them row for row.
2. Point in time: a day already present is never rewritten. A planted second run with changed values fails and names
   the day.
3. Rows from before the append are byte-for-byte unchanged (old files' bytes are a prefix of the new, or the old
   folder is untouched under option B).
4. A missing file, close or contract fails the day, posts one #fno-desk line, and writes nothing.
5. The live capture's Q5 base rate stays fresh: `iv30_history_stale` does not fire on a test day 30 sessions after
   the last manual build.
6. No frozen file changes, or the change is approved and frozen as a new version first.

**Judge verifies:** rebuilds two appended days with A3's builder and compares them; plants a rewrite; checks that every
frozen file's hash is unchanged.

**Depends:** A3, A9, A11, O6 · **Size:** M · **Status:** done: judge 64 PASS with addenda 1-4 (G1 v3 frozen 14 Oct 2026, protocol 904c036); scheduled 21:41 and 12:11 IST; first append 13 Oct (9cba740). Judge compares the first two scheduled appends with A3's build on 14-15 Oct

---

## A14. Margins from NSE automatically

**Repository:** trading

**Description:** As the risk manager, I want each session's initial margin per lot for SF, SC and BF computed from NSE
Clearing's own SPAN file and exposure-margin rule, recorded with the file's name and SHA-256, so that C2's margin
check (issue #85) has fresh inputs every day without the owner typing them in.

**Context and why:** Owner, 14 Oct 2026: "let's build it to fetch margins from NSE automatically, so the margin inputs
(#85) don't need you every week." C2 refuses every paper trade while `research/data/margins/margins.csv` has no row
younger than 7 days (`risk.margins.max_age_days`) and while the stressed-margin factor is unset.

Facts checked on 14 Oct 2026 (builder, response 77):
- NSE Clearing publishes six SPAN risk-parameter files a session at
  `https://nsearchives.nseindia.com/archives/nsccl/span/nsccl.<YYYYMMDD>.<i1..i5|s>.zip` (XML, SPAN 4.00, about 9.5 MB
  zipped). The beginning-of-day file `i1` for day d is written the evening before d (its own `<created>` stamp and
  NSE's Last-Modified agree: `nsccl.20261014.i1` created 2026-10-13 21:28; 131 sampled files from 2020, 2024 and 2026
  were written between 18:00 and 03:05 IST, 2026's between 20:00 and 24:00, none after 09:00 on d); `i2` to `i5` follow
  at about 11:03, 12:32, 14:03 and 15:32 IST on d, and the end-of-day `s` file at about 16:51. The archive goes back to
  at least 2 January 2020.
- For NIFTY the file holds one scan tier, a short-option minimum rate of 0 and calendar-spread charges only between
  different expiries, so a one-expiry four-leg structure's SPAN margin is its scanning risk: the largest of the 16
  scenario losses of the summed risk arrays, times the lot.
- NSE's daily exposure-margin file (`archives/exp_lim/ael_DDMMYYYY.csv`) lists stocks only. For index options the
  exposure (extreme-loss) margin is NSE's published rule: 2% of the notional value of each short option (underlying's
  last close times quantity), 3% for a short option more than 10% out of the money, 5% beyond 9 months to expiry, plus
  2% on its expiry day; long options carry none.

**Scope.** In:
- a dated raw dataset `nse/derivatives/span-bod` (the `i1` file of each session), archived in Drive by the A9
  librarian with its manifest row, later NSE versions kept by A11's sweep;
- a reader of the SPAN file's NIFTY parts (index close, futures expiries, option risk arrays, the scan-tier,
  short-option-minimum and spread definitions) that refuses any file whose NIFTY method differs from the one modelled;
- a calculator: initial margin per lot = SPAN scanning risk + exposure margin, for SF, SC and BF at each of the
  research widths (300, 250, 200, 150, 100), with the legs built by B2's `Structure` classes on the file's own listed
  strikes and index close, on the first monthly (futures) expiry at least 30 calendar days after d (the A5/B2 entry
  window's near edge);
- an append-only writer to `margins.csv` (`source` = `NSE SPAN <file name> sha256=<SHA-256>`, `as_of` = d) that never
  edits or reorders a past row; the same row again is a no-op, a different figure for the same key is a conflict;
- judge 75 (14 Oct 2026): the scanning risk, the net option value and the exposure are stored as separate columns; C2
  counts `max(0, scan - NOV) + min(0, NOV) + exposure` and stresses only the scan (`max(0, k x scan - NOV) + min(0, NOV)
  + exposure`, k from config); with an open losing trade C2 never leaves more free than a broker that nets the
  premium (test);
- a GitHub Actions job (no AI) with the A13 shape, run each morning before the open (07:45 IST, retry 08:30):
  librarian, revisions sweep, compute, commit; one #fno-desk line on any failure;
- a proposal (not a change) for deriving C2's stressed-margin factor from archived files.

Out: C2's frozen method and `config.yaml` `risk` values (owner decision first); broker-specific add-ons (Groww's own
extra margin, if any) which only the broker's calculator shows; placing or sizing any order.

**Point in time:** a row dated d comes only from `nsccl.<d>.i1`, whose `<created>` stamp must be before 09:00 IST on d
(checked; a later stamp writes nothing). C2 uses the latest row dated on or before the decision day, so a decision
on d never sees a file published after its decision time.

**Fail closed:** a missing file, a file that is not valid SPAN XML, a NIFTY method outside the model (more than one
scan tier, a non-zero short-option minimum, a missing series or contract, a non-unit contract value factor), an
expiry-day or beyond-9-months leg, or a structure whose legs are not all listed writes no row for what it affects, so
C2 keeps refusing. One #fno-desk line names the cause.

**Acceptance criteria:**
1. On real files the computed figures equal an independent figure: NSE's SPAN calculator or a broker's calculator, on
   the same contracts and day, within a stated and justified tolerance. Until that check passes the job stays
   unscheduled (manual `workflow_dispatch` only) and the exact one-time check for the owner is written down.
2. Hand computation: for a small planted SPAN file the SPAN, exposure and total per lot equal a hand calculation to the
   rupee (test).
3. Point in time: a planted file whose `<created>` stamp is at or after 09:00 IST on its day writes no row (test); a
   decision on d reads no row dated after d (C2's rule, test with a row dated d+1).
4. Fail closed: a missing file, a damaged zip, XML without NIFTY, a non-zero short-option minimum, two scan tiers and a
   structure with an unlisted leg each write no row and produce one alert naming the cause (tests); a mutation that
   writes a row from an invalid file fails a test.
5. Append-only: existing bytes of `margins.csv` are a prefix of the new file; a second run is a no-op; a different
   figure for an existing (structure, width, as_of) is refused and alerted (tests).
6. Provenance: each row's source names the exact file and its SHA-256, which equals the archived file's manifest row.
7. Stressed margin: a written proposal derives the factor from archived history with a stated window and rule; C2's
   method and config are unchanged until the owner answers.
8. Code size, lint, imports and the full suite pass; nothing touches `fno/forecast/`, `fno/ai/` or the forecast
   capture.

**Test plan:** a small synthetic SPAN XML built in the tests (two expiries, a handful of strikes, known arrays) for the
hand calculation and every refusal; the real `nsccl.20261014.i1` file for the validation numbers (kept out of git,
re-downloadable; its SHA-256 recorded in the claims).

**Judge verifies:** recomputes two rows by hand from the real file; plants a late-created file and a damaged one;
re-runs the job twice and checks the CSV is unchanged; checks the validation evidence and tolerance.

**Depends:** A9, A11, C2, O6 · **Size:** M · **Status:** in progress (builder session 01FVYzWZtDAZrZLDZ6DtmSYL)
