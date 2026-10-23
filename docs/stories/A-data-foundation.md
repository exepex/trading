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
  writable store, never overwritten (A4b, 15 Oct 2026: the quote file in the owner's Drive only, the sidecar and the
  canonical marker in the repository folder `research/data/quotes/`).
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

## A4b. Raw Groww quotes in Google Drive only; the public repository keeps hashes, counts and derived values

**Repository:** trading · **Lane:** 1 (outside-service data, the daily routine's output, inputs of the forecasts and
the paper desk) · **Branch:** `story/a4b-quotes-drive-only` · **Claims:** `reviews/claude/response_111_a4b-quotes-drive-only.md`

**Description:** As the owner, I want the 3 pm recorder's raw Groww quote rows (bid, ask, quantities and every other
per-contract value) saved only in my private Google Drive, while the public repository keeps what proves and dates
them (capture ID, times, counts, completeness, the SHA-256 of the Drive file) and the derived values the desk and the
forecasts need, so that the public repository no longer republishes Groww's data and nothing that reads the snapshots
stops working.

**Context and why:**
- Owner decision, 15 Oct 2026 (`docs/DESK_DECISIONS.md`, owner "6 A"): "Raw Groww quotes go to Drive only from now on;
  the public repository keeps hashes, counts and derived values". It changes A4 through a lane-1 story; A16 (15-minute
  recorder) and R2 follow it from the start; `research/data/quotes/groww/derivatives/quote-snapshots/2026/10/
  nifty_20261014_145500.csv` stays in git history (history is never rewritten).
- Design v2 section 4.4, "Data rights, retention and security": raw quotes stay in Drive (private); the public
  repository holds only derived figures (counts, gaps and the like); raw files are kept under A11's rule (never
  overwritten); keys follow section 6.6.
- Today (A4 as built) every attempt's CSV and sidecar are written by `LocalFolderStore` into `research/data/quotes/`,
  and the routine commits that folder to the public repository. One Groww snapshot is in the tree (14 Oct 2026, 184
  contracts, commit 5c22bcc). A9 already gives a writable Drive store as the owner (`build_owner_drive`).

**What is raw and what is kept in the repository (the split).** Raw = every row of a Groww attempt's quote file
(`<snapshot_id>.csv` of the dataset `groww/derivatives/quote-snapshots`: bid, ask, last, quantities, last trade time,
contract ID, per-row spot, each row's raw-response SHA-256). Kept in the repository, per attempt: the sidecar
`<snapshot_id>.meta.json` and the day's `nifty_<YYYYMMDD>.canonical` marker. Every sidecar key, and why it is not a
raw Groww quote:

| Sidecar key | What it is | Why it may be public |
|---|---|---|
| `snapshot_id`, `underlying`, `provider`, `started_at`, `finished_at`, `in_window`, `note` | identity and capture times | metadata |
| `expiries`, `expiry_source`, `monthly_check` | which contracts were asked, from NSE's public files | metadata from NSE |
| `expected_contracts`, `recorded_contracts`, `complete`, `failures` | counts, completeness and failure entries | counts; each failure entry is a fixed text with the exception's type, never its message (criterion 9) |
| `csv_sha256`, new `raw_file_saved` | the Drive file's SHA-256 and whether it was saved | the hash is the anchor the readers check |
| `spot` | NIFTY's index level with the chain | an index level, not an option quote; read by B7's `CutoffSnapshot` |
| `india_vix`, `india_vix_time`, `futures`, `levels_source`, `levels_failures` | NSE's public India VIX and futures levels (A4's `NseLevelSource`) | NSE's public data, not Groww's; the G1 v2 live pack reads them |

The orchestrator's brief named "the 15:00 spot/VIX/futures fields the G1 live pack reads". Checked against the 14 Oct
pack (`research/forecasts/live_v2/2026/2026-10-14_pack.json`): it reads `nifty_spot` from the quote rows (so from
the Drive file), `india_vix` and the futures from the sidecar, and derives the ATM IVs from the rows' mids. The pack
itself holds only those derived values and the two hashes, so it stays public unchanged.

**Decision on the existing 14 Oct file (for the judge):** it is uploaded to Drive at the new path with the same bytes,
read back and checked against its sidecar's `csv_sha256` (`9d9de08b...`), and then **removed from the tree** (`git rm`,
never a history rewrite). Reasons: (1) one way to read a Groww quote file: through Drive with the hash check; keeping
this one file in the tree would need a "repository fallback" path in every reader, which is exactly the path the owner
closed; (2) the test "no Groww quote file is tracked under `research/data/quotes/groww/`" can then hold without an
exception; (3) removal un-publishes nothing (it stays public in history at 5c22bcc) and loses nothing (Drive copy,
hash-checked). Its sidecar and canonical marker stay in the tree. (The routine's rule "never edit or delete a recorded
attempt" binds the routine; this one move is the owner's decision applied by this story, with the bytes kept in Drive.) The sidecar has no `raw_file_saved` key; a sidecar
without the key counts as saved (only A4b's recorder writes `false`).

**Scope.** In:
- a quote store behind `RawFileStore` that sends the Groww dataset's quote files to a private store (the owner's Drive,
  `raw` area, A9) and every other file to the repository folder, and returns a Groww quote file only after checking its
  SHA-256 against the committed sidecar; wired in `fno/storage/wiring.py` `build_quote_store`, so every reader that gets
  its store there is switched with no change of its own;
- the recorder: a quote file that cannot be saved makes the attempt incomplete (never canonical), recorded in the
  sidecar (`raw_file_saved: false`, written only then, so a complete attempt's sidecar is byte-identical to A4's; the
  reason in `failures`), printed in the result line and alerted to #fno-desk by
  the command; nothing raw is ever written to the repository instead;
- the readers that read the folder directly (`quotes report`, `quotes compare`) read through the store; E3's
  execution capture commits only the files the repository holds;
- the 14 Oct file moved as decided above; a `.gitignore` rule for Groww quote files under `research/data/quotes/groww/`;
- docs: A4's "Expected design" storage line, `fno/storage/README.md`, and the routine's steps in `CLAUDE.md` (wording
  below).

Out:
- NSE's public chain (`research/data/quotes/nse/`, story O6): public NSE data, not Groww's; stays in the repository;
- A16 (15-minute recorder) and R2: their own stories; they reuse this store from the start (owner decision row);
- the E2 common pack's per-contract quote items (see "Found outside scope", item 1): not written to the repository
  today, but would be once the paper desk's daily run commits its packs;
- deleting anything in Drive; rewriting git history.

**Expected design:**
- `fno/quotes/drive_only_store.py`: class `DriveOnlyQuoteStore(RawFileStore)` with the repository store, a factory of
  the private store (called on first use, so building the store never signs in: the forecast job's golden step and the
  NSE recorder build it without needing Drive), and the private dataset (`groww/derivatives/quote-snapshots`).
  - `put(path)`: a Groww quote file goes to the private store only; with no private store, `RawQuoteStoreUnavailable`
    (naming the four Drive settings, never their values). Every other file goes to the repository store.
  - `get(path)` of a Groww quote file: reads its sidecar from the repository. No sidecar, or a sidecar with
    `raw_file_saved: false` → `None` (there is no such file). Otherwise the private store's bytes, only if their
    SHA-256 equals `csv_sha256`; a different hash → `RawQuoteHashMismatch`; no file in Drive → `RawQuoteMissing`; no
    private store → `RawQuoteStoreUnavailable`. A saved file is never reported as quietly absent.
- `fno/storage/wiring.py` `build_quote_store(folder=None)` calls `fno/storage/quote_wiring.py`
  `build_drive_only_quote_store`, which returns `DriveOnlyQuoteStore(LocalFolderStore(folder), <the raw area of
  build_owner_drive(), built on first use>, GROWW dataset)` (a new composition root, listed in `CLAUDE.md`: `wiring.py`
  would pass the 350-line limit). Drive path of a file:
  `raw/groww/derivatives/quote-snapshots/<YYYY>/<MM>/<snapshot_id>.csv` (A9's layout).
- `fno/quotes/recorder.py` `_attempt`: the quote file is saved first, inside a guard; on any error the failure
  `raw quote file not saved: <type>` is added (the error's type only: a Drive error's text can hold the request URL with
  the private folder's ID, and the sidecar is public; the full text goes only to the private #fno-desk alert),
  `complete` is false and the sidecar says `raw_file_saved: false`; then the sidecar is written as before. `RecordResult.raw_file_error` carries the reason.
- `fno/quotes/cli.py`: the result line ends with ` - raw quote file not saved: ...`; the alert
  `3 pm quote recorder: raw quote file NOT saved to Drive (...); the sidecar is kept, no raw quote went to the
  repository; the recorder retries until 15:10. Fix: check the four FNO_GDRIVE_* settings (A9: run
  tools/gdrive_oauth_setup.py if the owner's consent expired)` is sent; exit code 1.
- Frozen files are not edited: G1 v2's byte-frozen `fno/forecast/capture.py`, `baseline_wiring.py` and `cli.py` get
  the new store through `storage.build_quote_store()`; `fno/quotes/recorder.py` and
  `fno/research_data/quote_snapshots.py` are in v2's "recorded, not byte-checked" table (behaviour locked by the golden
  cases, which `tools/forecast_live_golden.py` recomputes on synthetic files in the golden folder with its own
  `LocalFolderStore`; already changed since the freeze by A7, A5 and O6).

**Readers of the snapshot files (each must keep working):**

| Reader | Reads | Gets its store from | Change |
|---|---|---|---|
| `fno/forecast/capture.py` `load_snapshot` (G1 v2 live capture and `forecast snapshot-ready`; byte-frozen) | canonical, quote file, sidecar | `storage.build_quote_store()` in frozen `baseline_wiring.py` / `cli.py` | none (store swapped) |
| `fno/research_data/quote_snapshots.py` `RecordedSnapshots` (B7 live features, `composition.py`) | same | `build_quote_store()` | none |
| `fno/desk/snapshot_inputs.py` `SnapshotInput` (E2 common pack) | same | `build_quote_store()` in `pack_wiring.py` | none |
| `fno/desk/snapshot.py` `RecordedExecutionSnapshots` (E4 fills) | quote file, sidecar by ID | `build_quote_store()` in `desk/wiring.py` | a failed Drive read becomes `SnapshotError`, so C3's gate refuses and alerts and the day's exits still run |
| `fno/checks/validity_evidence.py` `EvidenceReader` (C4) | quote file, sidecar by ID, hashes checked | `build_quote_store()` in `checks/wiring.py` | none |
| `fno/books/book1_inputs.py` (Book 1) | quote file by ID, hash checked | `build_quote_store()` in `book1_wiring.py` | none |
| `fno/desk/execution_capture.py` (E3, 15:15 capture) | quote file, sidecar; commits them | `build_quote_store()` | commits the repository files only; an unsaved or unreadable quote file gives no capture record (its sidecar is still committed) |
| `fno/quotes/report.py`, `fno/quotes/compare.py` | canonical, quote file, sidecar | read the folder directly | read through the store |
| `tools/forecast_live_golden.py` (frozen) | synthetic golden files | its own `LocalFolderStore` | none (their hand-built sidecars' `csv_sha256` is not their files' hash, so they could not pass this store's check; they never go through it) |
| `fno/forecast_scoring/wiring.py` `recompute_live_day` (G4's live replay; in G1 v3's "recorded, not byte-checked" table, already changed since; the byte-frozen `replay.py` is not changed) | canonical, quote file, sidecar of a commit's exported inputs | its own `LocalFolderStore` | `replay_quote_store`: a commit from before A4b is read from its own files (as captured then); a later commit's quote files from Drive, hash-checked, so a missing copy stops the replay instead of switching quietly to NSE's snapshot |
| `research/2026-10-14-desk-meeting-2/analysis.py` (a dated research record) | the 14 Oct quote file by its repository path | none | none: a record of its day, re-run at its own commit, where the file exists; its committed output holds derived values only (half-spreads, IVs) |

**Judge 111 (story check of d1c2d06): readings R1-R4 accepted; this revision fixes its two should-fixes (criterion 6,
merge condition) and minor 1 (criterion 9).** Minor 2 ("`replay_quote_store` hash-checks pre-A4b files too") is
answered with a pushback, for the judge to rule: a commit from before A4b is read by the replay from `git archive` of
that commit, and git's objects are addressed by their own hash, so those bytes are exactly the committed ones; a
second check against the sidecar adds no protection there. It would also refuse a legitimate input: the G1 v2 golden
cases' hand-built sidecars (frozen) carry a `csv_sha256` that is not their file's hash, and
`tests/forecast_scoring/test_live_replay.py::test_the_real_recompute_is_the_v2_capture` replays golden case A through
this code; with the check that test fails and could only pass by editing frozen fixtures or loosening the test. The
check exists for Drive because a Drive copy can change after the commit. If the judge still wants it, the builder adds
it and the test question goes to the judge first.

**Who calls `build_quote_store` (every call site, how it reads after A4b, and its test):**

| Call site | Component it feeds | After A4b | Test |
|---|---|---|---|
| `fno/forecast/cli.py` `snapshot-ready` (byte-frozen) | `load_snapshot` | sidecar and marker from the checkout, quote file from Drive, hash-checked | readers test "forecast capture reads the same files" |
| `fno/forecast/baseline_wiring.py` `build_live_capture` (byte-frozen) | `LiveCapture.quotes` → `load_snapshot` | same | same, plus "the live pack is the same from Drive" |
| `fno/checks/wiring.py` `build_trade_validator` (C3/C4) | `EvidenceReader` | same; its own hash checks unchanged | readers test "C4's evidence is the same and still hash-checked" |
| `fno/desk/pack_wiring.py` (E2) | `SnapshotInput` | same | readers test "E2's common pack input is the same" |
| `fno/desk/wiring.py` `build_execution_snapshots` (E4) | `RecordedExecutionSnapshots` | same; a Drive read failure is `SnapshotError` | readers tests for E4 (same result; Drive failure) and `tests/desk/test_safety.py` (given a fake Drive) |
| `fno/desk/daily_wiring.py` (E3) | `RecorderExecutionCapture` and the recorder's `capture` | quote file saved to Drive; record and sidecar committed | readers tests for E3 (repository files only; unsaved; unreadable) |
| `fno/books/book1_wiring.py` | `LiveBook1Inputs` | same; its hash check against the pack unchanged | readers test "Book 1's snapshot is the same" |
| `fno/composition.py` (recorders; B7's `RecordedSnapshots`) | `QuoteSnapshotRecorder`, `RecordedSnapshots` | the recorder writes through it; B7 reads as above | recording tests; readers test "B7's cutoff snapshot is the same" |
| `fno/quotes/cli.py` `report`, `compare` | `canonical_snapshots`, `compare_lines` | through the store (they read the folder before) | readers test "report and comparison are the same" |

**Answers to the story check (judge D, through the orchestrator, 15 Oct 2026):**

1. **G4's replay (`fno/forecast_scoring/replay.py`, byte-frozen by G1 v3) is not changed.** It exports
   `research/data/quotes` from the pack commit's parent and calls `recompute_live_day` in
   `fno/forecast_scoring/wiring.py`, which is in G1 v3's "recorded, not byte-checked" table (its reason: the Q5
   resolver) and already differs from its recorded hash. The pack does **not** carry every quote it used (it holds
   derived values and the quote file's SHA-256), so a replay after A4b needs the quote file. A4b changes only
   `recompute_live_day`'s store: a commit that holds its Groww quote files (every commit before A4b) is read from them
   as now; a later commit holds the sidecar, whose `csv_sha256` pins the bytes, and the quote file is read from Drive and
   checked against it. Real replay of 14 Oct (builder's session, real Drive, real git history): (A) as today, from the
   commit's own file: pack and records identical; (B) the same exported inputs with the quote file deleted, read from
   Drive: identical (10.6 s); (C) the same deleted file with main's folder-only reader: both differ, so without this
   change every post-A4b replay would report DIFFERS. **The open question for the judge and the owner:**
   PROTOCOL_v3 section 2 says the replay "exports ... the quote snapshots ... from that commit". In the builder's
   reading the commit still fixes the bytes (through `csv_sha256`) and the frozen code is unchanged, so no new version
   is needed (reasoning, backed by test B). If the judge reads "exported from that commit" as "the quote file's bytes
   in git", this story needs a G1 v3 amendment, which is the owner's decision; then A4b stops here until it is made.
2. **`fno/quotes/recorder.py`: pushback, with the evidence, for the judge to rule.** FREEZE_v2 lists it under
   "Recorded, not byte-checked (behaviour locked by the golden cases)"; its bytes already differ from the recorded hash
   (`a9a06063...` now, `0775c4cc...` recorded) after A7, A5 and O6, each judge-passed. A4b's change keeps the golden
   behaviour: a complete attempt's files are byte-identical (A4's baseline test `tests/quotes/test_recorder_baseline.py`
   and `python tools/forecast_live_golden.py` both unchanged), and no golden file moves. Leaving its bytes alone and
   changing only the store is possible, but loses the Drive-down handling: the store cannot tell the recorder that the
   save failed except by raising, and an exception out of `_attempt` ends `record()` at once: no retry inside the
   window, no sidecar recording why, no "none" marker at 15:10, and a traceback instead of the result line. A store
   that swallowed the error would be worse: the attempt would be marked complete and canonical while its quote file is
   nowhere. The builder recommends the small recorder change (a guarded save, `raw_file_saved: false` only on failure);
   if the judge still requires the bytes unchanged, the fallback is the store-only change with that loss stated.
   `market_levels.py` is not changed in either case.
3. **Every call site:** the table above.
4. **The forecast-capture Action and Drive.** `.github/workflows/forecast-capture.yml` already passes
   `FNO_GDRIVE_FOLDER_ID`, `FNO_GDRIVE_OAUTH_CLIENT_ID`, `FNO_GDRIVE_OAUTH_CLIENT_SECRET` and
   `FNO_GDRIVE_OAUTH_REFRESH_TOKEN` to its capture job (and `forecast-scores.yml` to the replay), so no new secret and no
   workflow change is needed for A4b. That token's scope is full Drive (`https://www.googleapis.com/auth/drive`, A9),
   not read-only. **Owner step, optional, not done by this story:** a read-only path would be the service account
   (`FNO_GDRIVE_SERVICE_ACCOUNT_JSON`, Viewer on the project folder, A9's reader) added as an Actions secret, and the
   quote store reading through it; until the owner adds it, reads use the owner's token. **Fails closed:** with Drive
   down, missing settings, a missing or changed copy, `load_snapshot` raises (never falls back to git or to NSE's
   snapshot); `snapshot-ready` keeps polling until 15:13, `forecast capture` fails, and the workflow's failure step
   alerts #fno-desk; that day has no live forecast (found outside scope, item 5).
5. **Per file, what stays in git:** see "What is raw and what is kept" above. Of the sidecar's values: India VIX, its
   time and the futures' last price and volume come from NSE's public pages (`levels_source: nse`, A4's
   `NseLevelSource`): NSE data, not Groww's; times and counts are ours; `spot` is the NIFTY index level that Groww's
   chain response carries (a value Groww returned, of a public index; not an option quote): it stays public by **the
   orchestrator's decision** (15 Oct 2026, owner away, logged: "an index level the NSE publishes itself, not a raw
   bid/ask"), accepted by judge 111 (R4). Guard against a raw quote file in the repository: `.gitignore`, a test on the real tree, and **a record-scan
   rule** (story O5's pre-commit hook) that refuses a staged `.csv` under `research/data/quotes/groww/` even when added
   with `git add -f` (criterion 2).

**Point in time and the 15:15 lock:** the sidecar with `csv_sha256` is committed by the routine right after the
capture (GitHub's push receipt dates it); every read of the Drive copy is checked against it, so a Drive copy changed
later is refused, never used. The live capture reads the same bytes as before, so the pack and its hashes are
unchanged (test). Added time: one Drive read per snapshot read (the forecast job polls `snapshot-ready` every 20 s
from 15:10 and must generate by 15:15); measured on the real 14 Oct file and reported in the claims.

**Drive down at 15:00 (the failure case):** the attempt's quote rows are not saved anywhere (never to the repository,
never to a local spool); its sidecar is kept with `complete: false`, `raw_file_saved: false` and the reason; it is
never canonical; the recorder retries every minute until 15:10 as A4 does; if Drive never comes back the day's
canonical is "none" and the command prints `recorded: <id> (<n> contracts, complete=False) - raw quote file not saved:
<reason>`, sends the alert above and exits 1. The day's quotes are lost (A4's rule: never back-filled). If Drive comes
back inside the window, the next attempt is complete and canonical.

**Acceptance criteria:**
1. **Raw rows to Drive only.** A recording through `build_quote_store`'s store saves the attempt's quote file only in
   the private store at `raw/groww/derivatives/quote-snapshots/<YYYY>/<MM>/<snapshot_id>.csv`; the repository folder
   gets the sidecar and canonical marker and no `.csv`; the Drive bytes hash to the sidecar's `csv_sha256` (tests:
   positive; an NSE-dataset file still goes to the repository and never to Drive).
2. **No raw quote in the repository.** The sidecar's keys are exactly the table above (test fails on any new key);
   `.gitignore` ignores any `.csv` under `research/data/quotes/groww/` (test with `git check-ignore`); the record scan
   (O5's pre-commit hook) refuses a staged `.csv` there, also one added with `git add -f` (test); no file under
   `research/data/quotes/groww/` ending `.csv` is tracked (test on the real tree); the 14 Oct file is in Drive with its
   hash verified (evidence in the claims) and removed from the tree; its sidecar and marker stay.
3. **Hash-checked reads, loud failures.** A Groww quote file is returned only when its bytes hash to the committed
   `csv_sha256`; a different hash raises `RawQuoteHashMismatch`, a saved file absent from Drive `RawQuoteMissing`, no
   Drive settings `RawQuoteStoreUnavailable`; `None` only when there is no sidecar or it says `raw_file_saved: false`
   (tests for each; boundary: a one-byte change; empty: an empty quote file with its correct hash is returned as
   empty bytes).
4. **Every reader keeps working.** Each reader in the table gives the same result from the split store (fake Drive) as
   from A4's single folder for the same snapshot (tests); E3's capture commits only repository files and returns no
   record for an unsaved quote file; `quotes report` and `quotes compare` give the same output as before.
5. **Drive down.** With the private store failing on save: the attempt's sidecar is kept with `complete: false`,
   `raw_file_saved: false` and the reason; no `.csv` exists anywhere under the repository folder; the attempt is not
   canonical; the window ends "none"; the command prints the reason, sends one alert and exits 1. Drive failing on the
   first attempt and working on the second: the second is complete and canonical (tests; the alert text names no
   credential value).
6. **Frozen files; point in time.** No byte-checked file of the G1 v1, v2 or v3 freeze records changes (a script over
   every `FREEZE*.md` byte-checked table against the diff; `fno/forecast_scoring/replay.py` among them). The two
   "recorded, not byte-checked" files change only as judge 111 ruled: `fno/quotes/recorder.py` (the guarded save, R2,
   and the fixed failure texts below) and `fno/forecast_scoring/wiring.py` (the replay's quote store, R1). With them:
   the freeze tests, `python tools/forecast_live_golden.py` ("unchanged"), A4's baseline test
   `tests/quotes/test_recorder_baseline.py` (byte-identical output for its normal and december scenarios; for retry and
   none only the `failures` texts change, to the fixed form below, and its fixture files are updated for exactly those
   strings) and G4's Q5 wiring test `tests/forecast_scoring/test_scoring_wiring_q5.py` all pass; the live pack built from
   the split store equals the pack built from A4's folder for the same bytes (test); a real replay of 14 Oct reproduces
   its pack and records both from the commit's own file and, with that file removed, from Drive.
7. **The routine stays correct.** `CLAUDE.md`'s 3 pm steps say where the raw rows go, what step 3 commits and the new
   alert; `git add research/data/quotes/` after a recording stages only sidecars and markers (gitignore test above).
8. Code size, lint, imports and the full suite pass; no credential value in any file, log or message.
9. **Public failure texts are fixed texts.** Every entry the recorder writes to the public sidecar's `failures` is
   `<where>: <exception type> (provider message withheld)` (for a provider or expiry-listing error) or
   `raw quote file not saved: <exception type>` (for the save), never the exception's own message, which can carry a
   request URL, a Drive folder ID or a value (test: a planted value in a provider's and in Drive's exception never
   appears in any file under the repository folder or in the printed result line). The full text of a failed save goes
   only to the private #fno-desk alert. Cost, stated: the message of a provider error is no longer kept anywhere public;
   the type and the contract stay.

**Merge condition (judge 111, should-fix 2; for the orchestrator before the merge):** a write-read check of Drive in
the 3 pm routine's own environment, printing no value: the routine's environment saves a small probe file through
`build_quote_store` to a probe path, reads it back hash-checked and prints only "drive write-read ok" or the error
type. Without the four Drive settings there, every attempt fails and every day ends "none" (no forecast pack, no desk
inputs). After the merge, Quality rule 8's first real run of the 15:00 recorder (its result line, the sidecar committed,
the Drive file's hash equal to the sidecar's) is recorded in the conversation log and the merge record.

**Test plan:** a fake private store (dict, with switches for "down on save", "missing", "tampered") and a temporary
repository folder; the recorder's fake provider from the A4 tests; each reader run once through the old layout and
once through the split store on the same synthetic snapshot; a dry run of `record_today` with fake quotes and a fake
Drive for the claims' real output sample (no real quote in the repository). One real check: the 14 Oct file uploaded
and read back through the committed store with its hash checked, and the read time measured.

**Judge verifies:** reads the diff and the frozen-file hashes; plants a changed byte in a fake Drive copy and sees it
refused; makes the fake Drive fail and checks that no `.csv` appears under the repository folder and the day ends
"none"; checks that no Groww `.csv` is tracked; reads one sidecar against the key table; checks the 14 Oct Drive copy's
hash if it can reach Drive (else says so).

**Gap list (design 4.4, the owner's decision row and the orchestrator's brief):**

| Requirement | Where |
|---|---|
| Raw Groww quotes stay in Drive (private) (4.4; owner "6 A") | criteria 1, 5 |
| The public repository holds only derived figures, hashes and counts (4.4; owner "6 A") | criterion 2 (key table) |
| Raw files kept under A11's rule: never overwritten (4.4) | criterion 1 (A9's Drive store refuses different bytes at a path: `RawFileConflict`, already tested by A9) |
| Key handling, section 6.6 (4.4) | criterion 5 and 8 (settings only from the environment, named never valued) |
| Card records, section 8.5 (4.4) | out of scope: T1's story (cards in Drive, owner decision 15 Oct) |
| "Unless the terms allow more" (4.4) | settled by the owner: "6 A" (Drive only), although Groww's terms allow storing |
| The existing file stays in git history (owner row) | criterion 2 (moved, `git rm`, no rewrite) |
| A16 and R2 follow from the start (owner row) | out of scope: their own stories, which build their store with `build_quote_store` |
| Every reader keeps working; derived values the desk and forecasts need (brief) | criterion 4, key table |
| Drive down at 15:00; no raw quote falls back to the repository (brief) | criterion 5 |
| Frozen readers: stop before changing them (brief) | criterion 6 and answers 1-2: no byte-checked file changes; two "recorded, not byte-checked" files do, with the judge to rule |
| Point in time and the 15:15 lock unaffected (brief) | criterion 6, "Point in time" paragraph |
| The routine's CLAUDE.md steps stay correct (brief) | criterion 7 |
| NSE files under `research/data/quotes/nse` | out of scope: public NSE data |
| Clock contract (4.4) | unchanged: no time field changes |

**Proposed routine wording (`CLAUDE.md`, "3 pm quote recorder", lane 1):** step 2 gains "The raw quote rows go to
Google Drive only (story A4b, needs the four `FNO_GDRIVE_*` settings); the repository gets each attempt's sidecar
(`.meta.json`, with the Drive file's SHA-256) and the day's `.canonical` marker." Step 3 is unchanged (it commits
`research/data/quotes/`; `.gitignore` keeps Groww quote files out). Step 4 adds the command's third alert "raw quote
file NOT saved to Drive".

**Found outside scope (reported, not built):**
1. **E2's common pack republishes raw quotes.** `SnapshotInput` copies every option row's bid, ask and quantities into
   `journal/packs/<day>/common.json`, and the paper desk's daily run (E3) commits each step's files. Owner, 15 Oct
   ("8 A"): the daily packs keep only derived quote figures (mid, spread in %), raw bid/ask in Drive, before the paper
   desk goes live: **follow-up story E2b**, not A4b's scope.
2. **Until A4b is merged, each day's routine still commits the raw quote file.** Owner, 15 Oct ("7 A"): today's routine
   may commit one more raw file; A4b lands only after the judge's PASS. Each such file is moved the same way as 14 Oct
   (Drive copy verified against its sidecar, then `git rm`) by the merge.
3. The routine's environment must hold the four Drive settings; if it does not, every attempt fails loudly and the day
   is "none". To be checked before the merge (this builder session has them; the routine's environment was not
   checked from here).
4. P5 (read models for the dashboard: quotes) must publish only derived values under this rule.
5. **Behaviour change for the owner to know:** before A4b, a Groww quote file the forecast job could not read made it
   use NSE's snapshot (O6's order); now a canonical Groww snapshot whose Drive copy is missing, changed or unreadable
   stops the job, which alerts #fno-desk ("forecast capture failed"), and that day has no live forecast. This is the
   owner's "never a guess" rule applied to Drive; the alternative (fall back to NSE) would hide a Drive failure.
6. The desk's 15:15 capture (E3) gets no alert of its own when its quote file is not saved: C3's gate alerts "no
   capture" instead. Left for E3 (not live).

**Depends:** A4, A9 · **Size:** M · **Status:** story text for the judge's check, revision 3 (15 Oct 2026; judge 111 FAIL on revision 2, fixed)

---

## A4c. The other index options at 3 pm (all-F&O recording, part 8a)

**Repository:** trading · **Lane:** 1 (Groww data, the daily routine's output) · **Branch:** `story/a4c-all-indices`

**Description:** As the execution specialist and the volatility trader, I want the bid/ask of the other traded NSE
index options recorded after NIFTY in the 3 pm routine, each with its real capture time, so that spreads, skews and
liquidity of BANKNIFTY, FINNIFTY and MIDCPNIFTY options are measured, not assumed.

**Context and why:**
- Owner, 13 Oct 2026: record all index and stock F&O. Owner, 15 Oct 2026 (`docs/DESK_DECISIONS.md`; response 144,
  decision 3): the 3 pm recorder records all F&O in time slots, NIFTY first (14:55-15:00, pushed at once), other
  indices next, stocks after, each quote stamped with its real time; data only. Response 144's plan step 8: "8a
  indices (about 4-5 minutes); 8b stocks" after the Drive-only story (A4b, merged).
- The recorder records NIFTY only (`UNDERLYING = "NIFTY"`, `fno/quotes/recorder.py`; A4 "Out: other underlyings").
- NSE's F&O file of 14 Oct 2026 (strong evidence: counted from the archived file) lists index options on six
  underlyings. For the two nearest monthlies, strikes within 5% of spot:

  | Underlying | Contracts | Traded that day |
  |---|---|---|
  | NIFTY (A4, unchanged) | 184 | 177 |
  | BANKNIFTY | 220 | 198 |
  | FINNIFTY | 146 | 70 |
  | MIDCPNIFTY | 220 | 109 |
  | NIFTYNXT50 | 276 | 8 |
  | NIFTYFPI | 120 | 0 |

  Owner, 15 Oct 2026 (`docs/DESK_DECISIONS.md`): "drop NIFTYFPI and NIFTYNXT50, record only the traded indices". So
  this story records BANKNIFTY, FINNIFTY and MIDCPNIFTY: about 590 quotes a day (220 + 146 + 220, plus about 6 chain
  and expiry calls). Each lists monthlies only (3 expiries), so A5's monthly rule needs no change.

**Scope.** In: BANKNIFTY, FINNIFTY and MIDCPNIFTY (owner's list), each checked against the previous session's NSE F&O
file (point in time: the file's name and SHA-256 are kept in each sidecar); the two nearest monthlies; strikes within 5% of spot; A4's
columns and validity rule; Drive-only quote files through A4b's store; one routine step after NIFTY's push.
Out: NIFTYFPI and NIFTYNXT50 (owner, 15 Oct: barely traded; 0 and 8 of 120 and 276 contracts on 14 Oct); stocks
(8b: a stock expiry rule, the 14:20 start that needs an owner schedule change); NIFTY weeklies, BSE
SENSEX, futures per underlying and lot sizes (response 144 finding 8, owner's choice); any reader of the new
snapshots (data only; no forecast, desk or card uses them); NIFTY's own recording (unchanged).

**Expected design (the simplest that covers the real cases):**
- `QuoteSnapshotRecorder` takes the underlying as a constructor value (default `NIFTY`); file stems become
  `<underlying lower-case>_<YYYYMMDD>_<HHMMSS>` and `<underlying lower-case>_<YYYYMMDD>.canonical`, which for NIFTY are
  today's names byte for byte. Same dataset (`groww/derivatives/quote-snapshots`), so A4b's store sends every new quote
  file to Drive and keeps sidecars and markers in the repository.
- The window is a constructor value too: NIFTY keeps 14:55-15:10; the other indices use 15:01-15:13 (after A16's
  15:00 snapshot, about 50 s; before 15:13, when forecast-capture stops pulling, and before the 15:15 marks of A16 and
  E3, which share the Groww key). No request starts outside the window, so no row can come after 15:30 (response 144
  finding 5).
- Pace: the index run uses at most 3 parallel requests and at most 2.5 request starts a second (A16's `RatePacer`).
  Together with A16's 5 a second this stays under the about 10 a second where Groww began failing (A16 step 0;
  some evidence, one morning). About 600 calls at 2.5 a second take about 4 minutes: done by about 15:05.
- The calendar cross-check "calendar says session, no same-day trades" stays NIFTY's only (response 144 finding 3):
  an index whose contracts did not trade today is recorded complete, its rows `valid=false` ("no trade today") as A4
  already marks them, and raises no alert (a quiet day for FINNIFTY or MIDCPNIFTY must not read as a closed market).
- The universe: the owner's three names (a constant in `fno/constants.py`). The latest NSE F&O file before today is
  read once per run and serves every expiry lookup (response 144 finding 6: about 0.8 s a parse); a name the file no
  longer lists as an index option (`IDO`) gets an incomplete attempt with that reason, never a silent skip.
- Command `python -m fno quotes record-indices`: records each underlying in turn (an incomplete one is retried while
  the window lasts, A4's rule), prints one result line per underlying, exits 1 if any is not complete, and sends one
  #fno-desk alert naming the incomplete ones (Slack token from the environment, as A4).
- Routine order (judge 151; the handover session's NSE step, `conversations/2026-10-15.md`: the 14:33 routine runs the
  Groww and NSE recorders in parallel and pushes Groww first, then NSE). NIFTY (Groww) and NSE start together as
  today. Right after NIFTY's push, `record-indices` starts, alongside the NSE recorder if that is still running. Each of
  the three parts commits and pushes **only its own files** when it is done, one commit at a time (`git pull
  --no-rebase` first): NIFTY its `nifty_*` sidecars and marker, NSE `research/data/quotes/nse/`, the indices their
  `banknifty_*`, `finnifty_*` and `midcpnifty_*` sidecars and markers. Never `git add research/data/quotes/` as a
  whole. NIFTY is always pushed first; NSE and the indices in whichever order they finish. The `CLAUDE.md` 3 pm
  section is changed in this branch (below); the owner copies the same steps into the routine's prompt.

**Step 0 (before code; read-only, counts and names only):** one call each of Groww's expiry list and option chain for
BANKNIFTY, FINNIFTY and MIDCPNIFTY, to confirm Groww's names for them. A name Groww refuses is reported in the claims,
and that underlying's attempts are recorded incomplete with the error type, never skipped silently.

**Acceptance criteria:**
1. **Each index recorded.** On a session day, `record-indices` writes, for each of the three underlyings, an attempt
   with every contract of its two nearest monthlies within 5% of spot (A4's columns, validity and freshness rules), its
   quote file in Drive only and its sidecar (with the universe file's name and SHA-256) and canonical marker in the
   repository (tests with a fake provider and a fake Drive: positive; a provider that refuses one underlying, or an
   NSE file that no longer lists it, gives that underlying an incomplete attempt and canonical "none", the others
   complete).
2. **NIFTY unchanged.** A4's byte-for-byte baseline test, the G1 v2 golden cases and every reader's test pass
   unchanged; no reader reads the new files (they match only `nifty_*`).
3. **Time box and pace.** No request starts before 15:01:00 or after 15:13:00 IST; request starts are at least 0.4 s
   apart; an underlying still incomplete at 15:13 gets canonical "none" (tests with a fake clock: at, just before and
   just after each limit).
4. **No false closed-day alert.** An index with no same-day trade is recorded complete with invalid rows and no
   cross-check alert; NIFTY's cross-check is unchanged (tests).
5. **Not a trading day / empty.** On a closed day the command records nothing and prints "not a trading day"; with no
   NSE file in the last 7 days it records nothing, prints why, alerts once and exits 1 (A4's fail-closed rule).
6. **Routine and docs.** `CLAUDE.md`'s 3 pm section (changed in this branch) lists the NIFTY, NSE and index steps,
   their order and each part's own `git add` paths (wording below); each part's paths stage only its own sidecars and
   markers, never a Groww quote file (test with `git add --dry-run` on a fixture folder holding all three parts' files;
   A4b's `.gitignore` and record-scan rule already cover `groww/**.csv`).
7. Code size, lint, imports and the full suite pass.
8. **First live day (rule 8).** On the first session after the merge, `main` holds NIFTY's, NSE's and the three
   indices' sidecars and markers for the day, each part in its own commit, NIFTY's pushed first; the orchestrator
   records the commits and their push times in the conversation log.

**`CLAUDE.md` 3 pm section, as changed in this branch (steps 2-3b; steps 1 and 4 unchanged):**
- 2: "`python -m fno quotes record` (NIFTY, Groww) and `python -m fno quotes record --source nse` (NSE's public chain,
  story O6) run in parallel from the routine's start; each waits for 14:55 IST and retries until 15:10. [the existing
  calendar and Drive-only text stays]"
- 3: "Each part commits and pushes only its own files, one commit at a time, `git pull --no-rebase` first; never
  `git add research/data/quotes/` as a whole. NIFTY first, as soon as its result line is printed:
  `git add ':(glob)research/data/quotes/groww/**/nifty_*'`. NSE when it is done: `git add research/data/quotes/nse/`.
  [the existing never-edit, record-scan and alert text stays]"
- 3b: "Right after NIFTY's push, run `python -m fno quotes record-indices` (BANKNIFTY, FINNIFTY and MIDCPNIFTY;
  15:01-15:13 IST, paced; raw quotes to Drive only), alongside NSE if it is still running. When it is done:
  `git add ':(glob)research/data/quotes/groww/**/banknifty_*' ':(glob)research/data/quotes/groww/**/finnifty_*'
  ':(glob)research/data/quotes/groww/**/midcpnifty_*'`, commit and push. It alerts #fno-desk itself for any index not
  recorded."

**Test plan:** A4's fake provider extended with a per-underlying chain; a fake clock for the window and pace; A4b's
fake Drive; one dry run with fake quotes for the claims' output sample; step 0's read-only check.

**Judge verifies:** the window and pace with a fake clock; NIFTY's baseline bytes; one real run's sidecars after the
first live day (rule 8); no Groww quote file in the repository.

**Known limits (one line each, nothing built for them):**
- A push of an index's canonical marker before 15:13 starts another forecast-capture run; it waits in the concurrency
  group and stops at its gate (the day's pack is already on main).
- The rate figures come from one morning's measurement (A16 step 0); a slower Groww day can leave an index "none".
- A new index or a change in which indices trade needs an owner decision and a one-line change of the list.
- NIFTY's own retries can run to 15:10 (A4's rule) and the indices start only after NIFTY's push, so on such a day the
  indices get the last minutes of their window and may end "none" (data only).

**Gap list (owner decisions 13 and 15 Oct; response 144 findings 1-9 on all-F&O recording):**

| Requirement | Where |
|---|---|
| All index F&O recorded, each quote with its real time (owner 13 and 15 Oct), only the traded indices (owner 15 Oct: drop NIFTYFPI and NIFTYNXT50) | criterion 1 (A4's per-row request and response times); scope |
| Time slots: NIFTY first and pushed at once, other indices next (owner 15 Oct) | design (routine step 3b), criterion 3 |
| Finding 1: stock chains fail on the IDO-only expiry history | out of scope: stocks are 8b (indices are IDO) |
| Finding 2: NIFTY must be pushed alone before 15:13 | unchanged step 3; indices run after it |
| Finding 3: cross-check on NIFTY only | criterion 4 |
| Finding 4: point-in-time universe with the file's SHA-256 | design (universe: the owner's list, checked against the previous session's file, its SHA-256 kept), criterion 1 |
| Finding 5: no rows after 15:30 | criterion 3 (nothing starts after 15:13) |
| Finding 6: parse the NSE file once | design (universe) |
| Finding 7: one shared Groww rate budget, NIFTY first | design (pace, window after A16's 15:00 mark), criterion 3 |
| Finding 8: weeklies, SENSEX, futures, lot sizes not recorded | out of scope (owner's choice) |
| Finding 9: raw files never under `research/data/quotes/` | A4b's store (criterion 1), A4b's ignore and scan rules (criterion 6) |
| Stocks at 14:20 need an earlier routine start (owner schedule change) | out of scope: 8b |
| Coordination with the NSE step in the same routine (owner 15 Oct; judge 151) | design (routine order), criteria 6 and 8; `CLAUDE.md` |

**Depends:** A4, A4b, A5 · **Size:** M · **Status:** story text for the judge's check, revision 3 (15 Oct 2026: three indices, owner; judge 151's should-fix and minor)

---

## A4e. A named quote window for protocol v4's 14:30-14:40 pack (A4 behind config)

**Repository:** trading · **Lane:** 1 (the 3 pm recorder, Groww, a v2-recorded file) · **Branch:**
`story/a4e-named-quote-window` · **Judge:** B (G10's judge)

**Description:** As the statistician and G10's pack builder, I want the 3 pm recorder to run a second, separately
named NIFTY capture in a window set in `config.yaml` (v4: 14:30-14:40 IST), so that protocol v4's pack can be built
from live quotes with honest times, while today's 14:55-15:10 capture and every reader of it stay exactly as they are.

**Context and why:**
- G10 (`docs/stories/G-forecasts.md`, "The day at go-live"; owner decisions of 15 Oct, rows "v4 timeline" and
  "Honest times") needs a NIFTY capture from 14:30:00 with retries, each quote kept with the time its answer was
  received; the pack takes only answers received by 14:40:00. A4 runs only in 14:55-15:10 (`fno/quotes/recorder.py:39`).
- The orchestrator (16 Oct): behind config, default unchanged, interface agreed with G10's builder (agreed 16 Oct:
  the 14:40 cut is the pack's, A4 never drops or relabels a row; the setting must work both as an extra capture and,
  if the owner later ends 14:55, as the only one).
- `fno/quotes/recorder.py` and `config.yaml` are in `FREEZE_v2.md`'s "recorded, not byte-checked" table: their behaviour
  is locked by the v2 golden cases, so the default run must not change.
- Readers of the 14:55 capture find it by name: `nifty_<day>.canonical` in `groww/derivatives/quote-snapshots`
  (v2 capture, E2/E3 packs, C3, O8 health, LR1, G4 replay, `report.py` and `compare.py`, which glob `nifty_*.canonical`).
  A new file prefix in the same folder would leak into those globs; a new dataset folder cannot.

**Scope.** In: `quotes.windows` in `config.yaml` (named windows; none required); `python -m fno quotes record --window
<name>`; the named capture in its own dataset `groww/derivatives/quote-snapshots-<name>` (Drive-only quotes through
A4b's store, sidecar and marker in the repository, as today); no request after the named window's end; A16's clock
check around a named capture, written to its sidecar. Out: the 14:30 run in the routine and the owner's 14:05 start
(O1 and the owner, after the orchestrator's decision below); the pack itself and its 14:40 cut (G10 part b);
the index windows at go-live (a later item); any change to the default run or its readers.

**Expected design (the simplest that covers the real cases):**
- `QuoteWindow(start, end, max_early_wait, stop_requests)` (new `fno/quotes/window.py`). The default window is A4's
  constants (14:55, 15:10, 20 minutes, no stop): the default run is unchanged byte for byte.
- `quotes.windows.<name>: {start, end, max_early_wait_minutes}` read in the composition root; an unknown name, a start
  not before the end, or a bad time format is refused before any request (ConfigError naming the key). The v4 entry is
  `{start: "14:30", end: "14:40", max_early_wait_minutes: 30}` (routine at 14:05 waits 25 minutes).
- A named capture: `record()` waits for the start (no request before it), retries each minute while it is open, and
  starts no request after its end (A4c's `Slot.stop_requests_at`); a request started before the end keeps its real
  `response_received_at`, even after the end. It reads A16's `ClockCheck` before its first and after its last
  request and writes `clock_status` and the worst skew to the sidecar (the pack decides what a skew means).
- Same stems (`nifty_<YYYYMMDD>_<HHMMSS>`, `nifty_<YYYYMMDD>.canonical`) in the named dataset, so the routine's NIFTY
  commit glob `groww/**/nifty_*` covers it and A4b's ignore rule and record scan keep its quote files out of git.

**Acceptance criteria:**
1. **Default unchanged.** `quotes record` without `--window` behaves as today: A4's byte-for-byte baseline, the v2
   golden cases (`tools/forecast_live_golden.py` "unchanged") and every existing quotes, checks and desk test pass
   unchanged.
2. **Named window.** With `--window v4` and a fake clock: nothing is asked before 14:30:00 (a run at 14:05 waits; one
   at 13:59 is "too early"); an incomplete attempt retries; no request starts after 14:40:00 (a request at 14:40:00 is
   allowed, at 14:40:01 refused); a request started at 14:39:59 keeps its later answer time; the day ends "none" at the
   window's end if nothing is complete.
3. **Separate dataset.** The named capture's sidecar, marker and Drive file are under
   `groww/derivatives/quote-snapshots-v4/`; nothing is written to the default dataset, and the default readers
   (`report`, `compare`, the v2 capture, the desk's snapshot inputs) do not see it.
4. **Clock.** A16's `ClockCheck` (one rule, A16's 5-second WARNING threshold, no copy) runs once before the first
   request and once after the last. The sidecar holds `clock_checks` (the two readings' statuses, in order, each one of
   A16's `clock_ok`, `clock_skew`, `clock_partial`, `clock_unchecked`), `clock_status` (`clock_ok` only when both
   readings are `clock_ok`, else the worse one) and `clock_worst_skew_seconds` (null when no server answered). Tests
   with fake servers: both ok; a skew before; a skew after; no answer; the run stopped before its last request (one
   reading only, so not `clock_ok`). What a status means for the pack's label is G10's rule (agreed 16 Oct: only
   `clock_ok` can give label `A`).
4b. **Every pack field has its own request and receive time (G10, 16 Oct; protocol v4 section 1.6; judge 278).**
   Today only the option rows carry `request_sent_at` and `response_received_at`; spot (from each expiry's chain call),
   India VIX and the NIFTY futures (NSE's level calls, `fno/quotes/market_levels.py`) carry none of ours (India VIX has
   NSE's own stamp only). A named capture's sidecar adds, on the same clock:
   - `chains`: one entry per expiry with `expiry`, `spot`, `request_sent_at` and `response_received_at` of that
     expiry's chain call;
   - `levels_requested_at` and `levels_received_at`: when the level reads (India VIX and the futures, one `levels()`
     call making both NSE requests) started and returned. Both answers had arrived by the return, so
     `levels_received_at` is an honest upper bound for each; NSE's `india_vix_time` is kept beside it. NSE's futures
     give last price and volume only, **no bid or ask** (G10's pack carries None for them).
   The default run's sidecar is unchanged. Tests with a fake clock: each expiry's two times are its own chain call's;
   the level times bracket both level calls and come before the first quote request; a level read that returns after
   the window's end keeps that real later time (nothing is clamped or relabelled).
5. **Refusals.** An unknown window name, a start not before the end, or a malformed time exits 1 before any request.
6. Code size, lint, imports and the full suite pass.

**Known limits (one line each, nothing built for them):**
- A 14:30 capture beside A16's 14:30 mark puts about 190 more Groww quote calls (plus a few chain, expiry and level
  calls) on the one key in those minutes; whether 14:30 is an extra capture or replaces 14:55 is the orchestrator's
  and owner's decision (G10's builder raised it), not this story's.
- A4's default run keeps an unchecked host clock (v2's frozen behaviour); only named captures are clock-checked.
- A named capture is not in the routine until O1 adds it and the owner moves the start to 14:05.

**Gap list:**

| Requirement | Where |
|---|---|
| Capture from 14:30 with retries, honest answer times (G10, owner 15 Oct) | criterion 2 |
| The 14:40 cut is the pack's; A4 drops nothing (agreed with G10, 16 Oct) | design, criterion 2 (late answer kept) |
| No request before the window's start (G10 point b) | criterion 2 |
| Checked clock for `response_received_at` (G10 point a; protocol v4 section 1.6) | criterion 4 |
| Our request and receive times on spot, India VIX and the futures (G10, 16 Oct; judge 278) | criterion 4b |
| Default 14:55-15:10 unchanged, v2 frozen behaviour (orchestrator; FREEZE_v2) | criterion 1 |
| Works as an extra capture or as the only one (G10 point 6) | design (own dataset), criterion 3 |
| Routine start 14:05 (G10 table) | out of scope: O1 and the owner |

**Depends:** A4, A4b, A4c (`Slot.stop_requests_at`), A16 (`ClockCheck`) · **Size:** S · **Status:** story text for
judge B (16 Oct 2026)

## A4f. NIFTY weekly expiries and open interest in the 3 pm capture

**Repository:** trading · **Lane:** 1 (the 3 pm recorder, Groww, a v2-recorded file) · **Branch:**
`story/a4f-nifty-weekly-oi` · **Judge:** F · **Claims:** response 302

**Description:** As the options strategist and the statistician, I want the 3 pm capture to record the NIFTY weekly
contracts (the nearest weekly, and the next) and every contract's open interest, so that contract-level forecasts can
be built and scored on the weeklies, where most NIFTY option trading is, and the report can show today's put-call
ratio and the strikes with the most call and put open interest.

**Context and why:**
- Owner, 21 Oct 2026 (`docs/DESK_DECISIONS.md`, row "Contract-level forecasts", piece 3): "Weekly contracts", the 3 pm
  capture extended to NIFTY weekly expiries, history from its start (no back-fill: quotes cannot be rebuilt), joining
  the go-live when judged (f2293cea). BANKNIFTY lists no weeklies since Nov 2024, so NIFTY only.
- A4 records the two nearest **monthlies** only (`fno/quotes/recorder.py`, A5's point-in-time rule). Groww's chain
  already returns each leg's open interest (`fno/providers/groww.py:63`, `OptionQuote.oi`; NSE's at
  `fno/providers/public.py:106`), but no snapshot column keeps it.
- Every reader of the snapshot CSV uses `csv.DictReader` (`research_data/quote_snapshots.py`, `desk/snapshot_inputs.py`,
  `checks/validity_evidence.py`, `forecast/live_pack.py`, `quotes/report.py`, `quotes/compare.py`), so a new last
  column changes no reader. `recorder.py` and `config.yaml` are in `FREEZE_v2.md`'s "recorded, not byte-checked" table:
  the v2 golden cases (which read committed fixtures) must stay "unchanged"; A4's own byte-for-byte baseline test changes
  by exactly the new column, on purpose.
- Readers find the monthly capture by `nifty_*.canonical` in `groww/derivatives/quote-snapshots` (`report.py:22`,
  `compare.py:29`), so the weeklies cannot share that folder or stem (the A4e reason).
- `recorder.py` is at 348 of 350 lines (A4e's known limit): it is split first, with no behaviour change.

**Scope.** In: an `open_interest` column (last) in every Groww and NSE 3 pm snapshot CSV, from the chain leg; a NIFTY
weekly slot recording the two nearest NIFTY expiries that are not one of the monthly capture's two monthlies, strikes
within 5% of spot, A4's columns, validity and Drive-only rules, in its own dataset `groww/derivatives/quote-snapshots-weekly`
(stem `niftyweekly`); run by `record-indices` after MIDCPNIFTY, inside A4c's 15:01-15:13 window and pace; the indices
part in O1's `QUOTE_PARTS` gains the pathspec `groww/**/niftyweekly_*` and the canonical `(<weekly dataset>,
"niftyweekly")` for F1's restart rule, and `CLAUDE.md`'s step 3b its `git add` glob (O1/O2's owner agreed, 21 Oct). Out:
any reader of the weeklies or of the new column (pieces 1 and 2 are G13's); BANKNIFTY weeklies (none listed); a back-fill; the monthly capture's contracts,
window or timing; A4e's v4 window (it gains the column, nothing else).

**Expected design (the simplest that covers the real cases):**
- Split first: the row and CSV writing (`COLUMNS`, `_row`, `_csv`, the freshness helpers) move unchanged to
  `fno/quotes/snapshot_rows.py`; A4's byte-for-byte baseline passes untouched by this step.
- `open_interest`: the leg's `oi` from the chain call, written as A4 writes numbers (`_num`); a leg the chain does not
  list gives an empty cell. The value is as of the chain answer (seconds before that row's quote), stated in the
  sidecar `note`.
- Weekly slot: `Slot("NIFTY", cross_check=False, stop_requests_at=15:13, workers=3, per_second=2.5)` (A4c's pace),
  stem `niftyweekly` (so NIFTY's commit glob `groww/**/nifty_*` can never take a weekly file), dataset
  `quote-snapshots-weekly`, and an expiry rule `nearest_weeklies(listed, monthlies, day, count=2)`: the two
  nearest listed expiries from `day` on that are not among the monthlies A5's rule picks that day. A day whose nearest
  expiry is the monthly (its last week) records the two weeklies after it.
- `record-indices` runs BANKNIFTY, FINNIFTY, MIDCPNIFTY, then NIFTY weekly, round-robin retries as A4c does; one result
  line each; the one alert names any not recorded.
- **The weekly slot always leaves a canonical marker on a session day it runs** (F1's restart rule reads it: a missing
  marker means "restart"): the complete attempt's id, or `none` at the window's end; a day whose listed expiries hold no
  non-monthly one is one attempt with the reason and `none` at once, like A4c's unlisted index (the provider is not
  asked for a chain).

**Size (reasoning only, from A4c's measured pace):** about 2 x 46 strikes x 2 types = about 184 weekly quotes plus 2
chain calls: about 75 s at 2.5 a second, so the window ends about 15:07 on a normal day (A4c's indices end about
15:05:30, 19 and 21 Oct). Build about 1 day: split, column, slot and rule, tests, the first live day.

**Acceptance criteria:**
1. **Split changes nothing.** After the split alone, A4's byte-for-byte baseline, every quotes test and
   `tools/forecast_live_golden.py` ("unchanged") pass with no test edited.
2. **Open interest.** Every Groww and NSE snapshot row has `open_interest` as its last column, equal to the chain
   leg's `oi` (fake chain: a value, zero, and a leg the chain lacks gives an empty cell); A4's baseline differs from
   before by exactly that column; the v2 golden cases stay "unchanged"; every reader listed above still reads a new
   file (one test per reader on a file with the column).
3. **Weekly contracts.** On a session day, the weekly slot records the two nearest non-monthly NIFTY expiries within 5%
   of spot, in `quote-snapshots-weekly`, quotes in Drive only, sidecar and `niftyweekly_<day>.canonical` in the repository
   (fake provider: a normal week; a monthly-expiry week, where the weeklies after it are taken; only one weekly listed,
   which records one and is complete; none listed, which records nothing and ends "none" with the reason).
4. **Window and pace.** The weekly slot starts no request after 15:13:00 and keeps A4c's pace (fake clock); the monthly
   capture's contracts, window and bytes (apart from the column) are unchanged.
5. **Readers unaffected.** No reader of the monthly capture sees a weekly file (`report`, `compare`, the v2 capture, the
   desk's snapshot inputs).
6. **Routine.** `git add --dry-run` in a temp repository with every part's files: the indices part's pathspecs stage the
   weekly sidecar and marker; NIFTY's `groww/**/nifty_*` stages no weekly file; `.gitignore`, the record scan and
   E2b's guard refuse the weekly CSVs (A4c's path test, extended). F1's restart: the indices part's `canonicals` list
   the weekly marker (its dataset name imported from A4f's module, never typed); `tests/daily/test_part_resume.py` gains
   "three index markers present, the weekly one missing, inside the window: the part restarts"; the e2e kill-rerun set
   (`tests/e2e/test_kill_rerun.py`) passes with its `record-indices` child writing the weekly marker too; a no-weekly
   day writes `none` (criterion 3), so its rerun reads as recorded. `CLAUDE.md` step 3b lists the `niftyweekly` glob.
7. Code size, lint, imports and the full suite pass.

**Known limits (one line each, nothing built for them):**
- Groww's parser turns a missing `open_interest` into 0 (`or 0`), so a 0 cannot be told from "not given"; the cell
  says 0 in both cases (a reader treats 0 with care).
- The weeklies share A4c's window: a slow index day can leave the weekly slot "none".
- No history before the first live day.

**Gap list:**

| Requirement | Where |
|---|---|
| NIFTY weekly contracts, the nearest and the next (owner, 21 Oct) | criterion 3 |
| No change to the monthly capture or its 14:55-15:10 timing (orchestrator) | criteria 2 (bytes, only the column), 4 |
| Paced within Groww's limits | criterion 4 (A4c's 2.5 a second) |
| Write-once Drive and receipts as today | criterion 3 (A4b's store) |
| open_interest in the snapshot (PCR, max call/put OI) | criterion 2 |
| v2 frozen behaviour | criteria 1, 2 (golden "unchanged") |
| `recorder.py` at the size limit | design (split), criterion 1 |

**Depends:** A4, A4b, A4c, A5 · **Size:** M (about 1 day) · **Status:** story text for judge F (21 Oct 2026)

## A4h. Today's index close, read after 15:30 for the evening check

**Repository:** trading · **Lane:** 1 (NSE, Drive, O1's steps, a forecast check's input) · **Branch:**
`story/a4h-close-read` · **Judge:** F

**Description:** As the statistician and the F&O trader, I want today's NIFTY 50 and NIFTY BANK closes read from NSE
soon after 15:30, kept write-once and later confirmed against NSE's official index-close file, so that the evening
report can check today's forecast against today's close the same day, marked "provisional" until confirmed.

**Context and why:**
- Owner, 21 Oct 2026 (`docs/DESK_DECISIONS.md`): forecast before the open and check after the close (c3231785). The
  evening edition runs at about 19:00 IST, from a scheduled task the owner will create (bcbbc454).
- The official close reaches us only through NSE's index-close file (`ind_close_all_DDMMYYYY.csv`), archived by O6's
  `index-closes.yml`. That job is scheduled for 21:11 IST, and GitHub has started this repository's scheduled runs
  4.5-5.5 hours late (`participant-oi-watch.yml`'s note, 14 Oct). G13b scores against that file.
- When the file is first published is **not measured**:
  - NSE's server gives `Last-Modified: 17:50:10 GMT` (23:20 IST) for every file from 9 to 21 Oct (checked 22 Oct about
    04:00 IST). That is NSE's late rewrite (A11 found the 12 Oct one), not the first release.
  - The first version comes out before 23:20: on 21 Oct we archived it (manifest, 15,901 bytes, SHA-256 `0c3d63..`)
    by 23:04 IST, and NSE's file now is a later one (17,833 bytes, `ccaff4..`). So "the file comes out at 23:20"
    (response 304, point 2) is the rewrite's time, not the first release.
  - Our manifest commits for these files came between 22:58 and 02:12 IST, after the 21:11 job.
  - So nothing shows the official file is out by 19:00. (Some evidence.)
- NSE's public `/api/allIndices` carries the closes earlier. A4 already reads it at 3 pm (`fno/quotes/market_levels.py`,
  `ALL_INDICES_PATH`) through `PublicData.nse_json`.
- **Evidence for 21 Oct** (read 22 Oct, 03:57 IST, 12.5 hours after the close, compared with NSE's
  `ind_close_all_21102026.csv`):
  - the answer's `timestamp` was still `21-Oct-2026 15:30`;
  - NIFTY 50 matched exactly at 22811.35, NIFTY BANK at 54976.9, NIFTY FINANCIAL SERVICES at 24691.45 and NIFTY
    MIDCAP SELECT at 13367.85;
  - **INDIA VIX did not match: 15.7 in allIndices against 15.68 official.** So VIX's value is recorded as "the
    list's value", never called the official close, and its confirm records the difference without an alert.
  - The answer also carries each index's `open` (NIFTY 23016, equal to the official file), which FL1's "opening
    gap" reason needs (response 304, point 5).
  - The FL1 builder saw the same stamp and closes on 21 Oct hours after the close.
  - These are two reads of one day. (Some evidence.)
- **No past archive can test more days.** No read of allIndices after 15:30 was ever kept: A4's 3 pm read keeps the
  parsed levels only, before the close. So the 5 record-only sessions below are the test.

**Where the read runs (decided, with the reason):**
- It is an O1 step, `close_read`, `NotBefore(15:40)`, placed last in `DAILY_RUN_STEPS`: after `lab_close` for as
  long as that step exists, else after `candles` (judge 440 add. 1 SF2). Steps run in order and `NotBefore` waits, so
  placed before `lab_close` the two A4h steps would hold FL1-1's 15:45 report to about 16:01; last, no consumer's time
  moves, and close_read starts at about 15:46 instead of 15:40 while `lab_close` runs. When FL1-1d removes
  `lab_close`, whichever merges second resolves one line (O1/O2's owner agreed, 22 Oct).
  - The daily routine is the only runner alive every session today: the 19:00 task does not exist yet, and GitHub's
    schedule starts hours late.
  - 15:40 is 10 minutes after NSE fixes the close.
- The same command may be rerun later the same evening, for example by the 19:00 task when the step failed. The stamp
  rule decides whether a read counts, not the clock time.
- I considered the FL1 builder's proposal (one read at about 19:55 only) and did not adopt it as the only read:
  - it needs a runner that does not exist yet;
  - it rests on one day.
  It stays possible as the rerun.

**Scope.**
- In:
  - a command `python -m fno closes read` and its O1 step;
  - NIFTY 50 and NIFTY BANK, the indices G13b and FL1 check, and INDIA VIX as the list's value; for each, `last` and
    `open`;
  - the raw answer and a parsed record, both write-once in Drive (O9's data store) with SHA-256 receipts;
  - the confirm step against the archived official file;
  - one #fno-desk alert per failure or difference.
- Out:
  - other indices: no reader, but the raw answer keeps them all;
  - any reader or display (FL1's `ProvisionalCloses` port reads the record);
  - O6's job and files, which stay unchanged: A4h only reads the archived file, and O6's owner is told;
  - measuring the official file's first release minute (the owner's open question in bcbbc454; one line in the claims).

**Expected design (the simplest that covers the real cases):**
- **One read.** `nse_json("/api/allIndices")`, through the existing client, with up to 3 tries 60 seconds apart on an
  error or a refused stamp.
- **One gate time.** `CLOSE_READ_FROM = 15:40`, one constant: O1's `NotBefore` and the command's own "too early"
  check both use it, so a hand run and the routine start at the same time.
- **When a read counts.** Its `timestamp` parses to today's session date at 15:30 or later. Any other stamp (the
  previous session, today before 15:30, missing) is refused with its text.
- **Regular sessions only (known limit).** A7's calendar has no close time per session (columns: date, kind,
  description, source), and its special sessions do not all close at 15:30 (the DR-site Saturdays end F&O at 12:30).
  So on a `special` or `muhurat` day the command prints `nothing written: close not read: <kind> session (no close
  time in the calendar)` and exits 0. O1's `outcome` (`fno/daily/steps.py`) records that `refused`, never `ok` (O10's
  "no ok without data"), so the day reads "done with problems: close_read" and the owner sees it; such days are rare.
  FL1-1 likewise covers regular sessions only. A close time per session in A7 would lift it.
- No "unchanged for 60 s" rule: 10 minutes after the close, two reads a minute apart can only catch a change in that
  minute, while the confirm step catches any difference at all. (Reasoning only; the 5 sessions test the read itself.)
- **No 15:44 end.** The step starts at the later of 15:40 and the end of `candles` (as late as about 15:43), and any
  read stamped today 15:30 or later counts, so a 19:00 rerun works. The stamp, not the clock, guards against a later
  list: a list for another session carries another stamp and is refused. The tries end within about 4 minutes (3 tries,
  60 s apart, the client's timeout each), well inside O1's 600 s limit. (Some evidence: one day's stamp held 12.5
  hours.)
- **Records.** The raw answer and `closes/<yyyy>/<mm>/<day>.json` go to O9's data store, write-once. The record holds:
  day, the read and NSE's stamp, each index's `last` and `open`, `provisional`, and the raw answer's SHA-256.
- **Commits.** In the daily run the step's one pathspec is its own receipts folder, from `receipt_pathspecs()` in its
  module (as G13 and G13b), never the shared `receipts/` root; the command commits nothing itself.
  - A rerun on a day already recorded writes nothing and prints "already recorded".
- **Confirm.**
  - Each run first confirms every earlier recorded day that has no confirmation yet and whose official file is in
    Drive. It reads the file through the verified Drive cache, using the first archived version (what G13b scores), and
    `read_index_closes` ("Nifty 50", "Nifty Bank").
  - It writes `closes/<yyyy>/<mm>/<day>.confirm.json` write-once, per index: `confirmed` when within 0.01 point, else
    `differs by X`.
  - A NIFTY 50 or NIFTY BANK difference sends one alert; VIX's difference is recorded only.
- **Lines, exit codes and alerts. No printed line holds an index level** (judge 440 SF1): O1 stores every line in
  `journal/runs/<date>.json`, which is committed and public, and the levels belong in Drive only (O9). Lines name the
  indices, statuses, NSE's stamp, the record's Drive path and its SHA-256; a derived difference ("differs by 0.02") is
  allowed.
  - Exit 0: `close read <day>: NIFTY 50, NIFTY BANK, INDIA VIX (list) recorded, NSE stamp 21-Oct-2026 15:30,
    closes/2026/10/2026-10-21.json sha256 <first 12>`; `not a trading day`; `close already read <day>`.
  - Exit 1: `too early: before 15:40`; `close not read: <reason of the last try>` (for example `NSE stamp
    20-Oct-2026 15:30 is not today's session`).
  - A failed read alerts once, through O1's `Alerted` wrapper; the command does not also alert it. A confirm
    difference is the command's own alert (its read may still succeed, exit 0).
  - Each confirm prints one line per day: `close confirm <day>: NIFTY 50 confirmed, NIFTY BANK confirmed, INDIA VIX
    differs by 0.02 (list value)`.
  - **A day never confirmed** (judge 440 minor 2): O6's index-closes job already posts one line when the official file
    is missing. A4h's confirm part sends its own one alert when a recorded day is still unconfirmed at the second
    session after it, and writes `<day>.overdue.json` write-once in Drive so the alert is sent once.
- **The second read** (judge 440 minor 1): a separate O1 step, `close_recheck`, `NotBefore(16:00)`, after
  `close_read`, runs `closes read --recheck`. It reads the list again with the same rules and writes the raw answer
  and `<day>.recheck.json` write-once: per index `same` or `differs by X` against the 15:40 read. So when the official
  file differs the next day, the record shows whether the list moved after 15:40 (a timing cause) or never matched (a
  rule cause); by then that day's list is gone, so this is the only way to tell. It runs every session, not only the
  record-only days: it costs the routine about 15 minutes of waiting, and keeps the evidence for every later day
  (reasoning only). Its own live key `daily.live_from.close_recheck: null`, its gate `CLOSE_RECHECK_FROM = 16:00`.
  - **No first read** (close_read failed or did not run): the recheck's read, under the same rules, becomes the day's
    record `<day>.json` (marked `read at recheck`), so the evening still gets a close. It prints `close read <day> at
    recheck (no first read to compare)` and exits 0. A failed recheck then exits 1 as any read does; close_read's own
    failure was alerted once by its step and is never alerted again here.
  - **Special and muhurat days:** the same `nothing written:` line and exit 0 as close_read, so O1 records `refused`.
  - **Cost (reasoning only):** the routine's day ends after about 16:00 instead of about 15:45; on a closed day
    nothing waits (A7 skips the whole run). No limit on the routine session's length is known to me or to O1/O2's
    owner.
  - O1/O2's owner agreed to the step (22 Oct), wired as close_read with `CLOSE_RECHECK_FROM`.
- **Placement.** `fno/close_read/` (source, record, confirm, command) and its composition root
  `fno/close_read/wiring.py`. O1's step is `Alerted("close_read", LiveFrom(NotBefore(CommandStep(...), CLOSE_READ_FROM,
  waiter), live["close_read"]), alerts)`: `LiveFrom` outside, so a not-live day never waits until 15:40;
  `CLOSE_READ_FROM` a named constant in A4h's module. `config.yaml` gets `daily.live_from.close_read: null` and
  `LIVE_STEPS` the key; the date is set at go-live.

**Record-only first.** For the first 5 sessions the record is written but FL1 does not show it. Each confirm line is
reported. A difference over 0.01 on any of those days stops FL1's use until it is explained.

**Size:** about 270 lines of code and 340 of tests (the second read and the overdue alert add about 40 each). M,
about 1 day.

**Gap list (every rule to a criterion or to Out):**

| Rule or requirement (source) | Where |
|---|---|
| Check today's forecast after the close (owner, c3231785) | criteria 1, 7 |
| Evening edition at about 19:00; a later rerun valid (owner, bcbbc454) | design (stamp rule), criterion 1 |
| Provisional until confirmed against the official file within 0.01 | criterion 4 |
| A day never confirmed is not silent | criterion 4 |
| The cause of a difference visible (judge 440 minor 1) | design (second read), criterion 9 |
| Data write-once in Drive, one SHA-256 receipt in GitHub (owner, 16 Oct; O9) | criterion 2 |
| Public repository: no level in any printed or committed line (rule 50a79a43; judge 440 SF1) | criterion 8 |
| Alerts only to #fno-desk with `FNO_SLACK_BOT_TOKEN`, once each | criteria 4, 5 |
| Research only: no order, no Groww call | criterion 6 |
| No `ok` without data (O10; O1's `outcome`) | criterion 1 |
| A7's calendar decides; regular sessions only (known limit) | criteria 1, 3 |
| O1's step terms (last: after `lab_close` while it exists, `LiveFrom` outside, own receipts pathspec, exit contract, `null` live date) | criterion 5 |
| One gate constant for hand and routine runs | criterion 3 |
| INDIA VIX as the list's value, never the official close; `open` kept (FL1, response 304) | criteria 2, 4 |
| Record-only for 5 sessions | criterion 7, "Record-only first" |
| O6's job and files unchanged (read only) | Out; criterion 6 |
| A source behind an interface (`CloseListSource`, one NSE adapter, wired in `fno/close_read/wiring.py`) | design, criterion 6 |
| No file or class over 350 lines; ruff, imports, full suite | criterion 10 |
| Readers and display (FL1); other indices; the official file's release minute | Out |

**Acceptance criteria:**
1. **The stamp decides.** Using NSE answers built from the 21 Oct read (stamp 15:30 today, the previous session's
   stamp, today at 15:29, missing, an error page, one index missing), only the first is recorded. A special session
   day prints its `nothing written:` line, writes nothing and exits 0, and O1 records the step `refused`, never `ok`
   (test). Each refusal prints its reason. Stamp today at 15:31 is recorded. The tries stop at 3: a 4th try is never
   sent (the fake source counts calls).
2. **Write-once and receipts.** The raw answer and the record each go to the data store once, with a receipt. A rerun
   on a recorded day writes nothing.
3. **The calendar and the gate.** A closed day (A7) prints "not a trading day" and reads nothing. Before 15:40 the
   step does not start (O1's `NotBefore`), and a hand run prints `too early: before 15:40` and reads nothing; both use
   `CLOSE_READ_FROM`.
4. **Confirm.** Using the real `ind_close_all_21102026.csv` values:
   - 22811.35 confirms;
   - 22811.34 confirms (0.01 is inside the tolerance);
   - 22811.33 records "differs by 0.02" and alerts once;
   - a day whose official file is not yet in Drive stays unconfirmed with no alert;
   - the same day still unconfirmed at the second session after it alerts once, and never again on later runs;
   - a confirmation is never rewritten.
5. **O1.** In the real `DAILY_RUN_STEPS` tuple, `close_read` and then `close_recheck` are the last two steps: after
   `lab_close` while it exists (a test asserts `lab_close`'s index is below `close_read`'s), else after `candles`. Its
   failure makes the day "done with problems" and stops no later step. A rerun the same day skips it once recorded.
   `test_day_run`'s call lists and its rerun test's new calls, `test_steps`' live dates and health's step string are
   extended, never loosened. Not live (`null`), it neither waits nor reads.
6. **No Groww, no orders.** The source imports only the public client (`check_imports`).
7. **The first 5 live sessions** (claims after merge): each day's read time, NSE stamp, the values and the confirm
   line, against the official file. Go-live items: the two `live_from` dates, and the e2e fixture's `("closes",
   "read")` child once that date is on or before the fixture day (14 Oct).
8. **No level in a printed line.** A test plants distinct values (for example NIFTY 50 at 22811.37) in the fake
   answer and asserts that no line the command prints, for a read, a rerun, a recheck, a confirm or a refusal, holds
   any planted value in any format (`22811.37`, `22,811.37`, `22811.4`).
9. **The second read.** With a fake answer changed by 0.05 between the 15:40 and 16:00 reads, the recheck record
   says `differs by 0.05` for that index and `same` for the others; a rerun of the recheck writes nothing; not live,
   the step neither waits nor reads. With no first read, the recheck writes the day's record marked `read at
   recheck` and exits 0; a special day prints `nothing written:` and O1 records `refused`. The same three O1 test
   lists are extended for it.
10. **Gates.** No file or class over 350 lines; `ruff`, `check_imports` and the full suite pass.

**Depends:** A4 (market_levels' endpoint), A7, A10 (`read_index_closes`), O1, O6 (archived file, read only), O9 ·
**Size:** M · **Status:** story text for judge F (22 Oct 2026)

### A4h-2. The day's high, low and previous close in the same record (FL1-1f's request, 23 Oct 2026)

**Why.** FL1-1f's evening "why" block needs each index's day range (the owner's 30-second rule; orchestrator: one
source, A4h's 15:40 read). NSE's answer already carries `high`, `low` and `previousClose` for every index. One
parser of that answer, A4h's `read_answer`, keeps a second one out of FL1.

**What changes:**
- **The record.** Each index in `closes/<yyyy>/<mm>/<day>.json` (and `.recheck.json`) gets `high`, `low` and
  `previous_close` beside `open` and `last`, from the same answer.
- **The read.** NIFTY 50 and NIFTY BANK, the checked indices, are refused like `last` when a field is missing or
  unreadable. INDIA VIX keeps its new fields optional (`null` when NSE leaves them out), as it is recorded but never
  checked.
- **The range check (DR1 sanity check 5, judge 541 SF1).** For NIFTY 50 and NIFTY BANK, a read with `low > high`, or
  with `last` or `open` outside `[low, high]` (edges included), is refused with a named reason and no level, for
  example `NIFTY 50: last outside the day's high-low`. INDIA VIX is never refused for it: the same finding goes into
  the record's `problems` list.
- **The confirm.**
  - `high` and `low` of the checked indices are checked against the official file's "High Index Value" and "Low Index
    Value" within `TOLERANCE`.
  - The reader of those columns is one function beside `read_index_closes` in `fno/fo_bhavcopy.py`: index name to
    open, high, low and close.
  - `previous_close` is checked against the previous session's official close, read from that session's file.
    While that file is not in Drive, the field stays unconfirmed under the same overdue rule as `last`: one alert at
    the second session after the day, never silent and never twice.
  - Each difference is recorded in `.confirm.json` and alerted once, as `last`'s is.
- **The recheck.** Its line names each field's difference (`same`, or `differs by X`), never a level.
- **Nothing is rewritten.** Records before the first read after the merge lack the fields; readers say "day range
  not recorded". The record stays `provisional: True` until confirmed.

**Acceptance criteria:**
1. A fake answer with distinct planted `high`, `low` and `previousClose` values: the record holds them for all three
   indices.
2. A missing or unreadable field refuses the read for NIFTY 50 or NIFTY BANK, and leaves `null` for INDIA VIX.
2b. The range check, for NIFTY 50 and for NIFTY BANK each:
    - `last` 0.01 above `high` is refused, and so is `open` 0.01 below `low`;
    - `last == high` and `open == low` are accepted;
    - `low > high` is refused.
    For INDIA VIX the same cases are recorded in `problems` and the read is kept. No refusal line holds a level.
3. Confirm, using the real 21 Oct official file (and a missing previous-session file: `previous_close` stays
   unconfirmed, then alerts once at the second session after the day):
   - `high` and `low` at the official value and at 0.01 off confirm;
   - at 0.02 off they record the difference and alert once;
   - a `previous_close` that differs from the previous session's official close records its difference.
4. The recheck names a 0.05 change in `high` as `differs by 0.05`.
5. Criterion 8's no-level test is extended to the planted new values in every format.
6. An old record without the fields still reads (a reader test with 22 Oct's record shape).
7. Gates as A4h's criterion 10.
8. Each criterion has good, bad, boundary and empty cases (quality rule 5). Empty means an answer with no rows, or a
   field present but blank.

**Gap list (quality rule 2):**

| Rule or requirement (source) | Where |
|---|---|
| The evening day range, one source: A4h's 15:40 read (FL1-1f; orchestrator, 23 Oct) | criterion 1 |
| The owner's 30-second rule for the evening "why" block (FL1-1f) | Out: FL1-1f's display; this story only supplies the fields |
| DR1 checks 1-4 at the provisional level (integrity, layout, stamp, completeness) | A4h's criteria 1-2, unchanged; criterion 2 here |
| DR1 check 5, sanity: a close outside the day's high-low (judge 541 SF1) | criterion 2b |
| DR1 check 6, agreement with the official file at confirm | criterion 3 |
| O9 write-once: no old record rewritten; older records read "day range not recorded" | criterion 6 |
| No level in any printed or committed line (judge 440 SF1) | criteria 2b, 5 |
| Merge no earlier than Mon 26 Oct, never 14:00-16:15 IST | "Lane and dates" |
| Good, bad, boundary and empty cases (quality rule 5) | criterion 8 |
| A real output sample in the Claims section, no level (quality rule 6) | Claims at code time: one dry-run record shape with values replaced by `<level>` |
| An end-to-end run after merge (quality rule 8) | after merge: the first session's read, recheck and confirm lines (no level), with the merge message naming the command |
| DR1's own certifier and records | Out: DR1's story; it is told the new fields |

**Lane and dates.** Lane 1 (a record feeding the forecast lab), judge F. It touches a live reader, so it merges no
earlier than Mon 26 Oct and never 14:00-16:15 IST. The fields start with the first session read after the merge;
the claims name that date. DR1's certifier (story/dr1-design) is told the new fields, so its checks can cover them.

**Size:** S · **Status:** text PASS (judge 541 add. 1, 7fb7d3de, on main 930cb6eb); code for judge F (23 Oct 2026)

**Claims (code, branch `story/a4h2-day-range`):**

| # | Criterion | Code | Tests |
|---|---|---|---|
| 1 | New fields in the record | `answer.py` `_values`, `records.py` | `test_day_range.py` planted values for all three indices; `test_reader.py`'s record test extended |
| 2 | Missing, empty or unreadable field | `answer.py` `_number` | 18 cases (2 checked indices x 3 fields x missing / "" / "-"); VIX kept with `null` |
| 2b | Range check, edges | `answer.py` `range_problems` | `last` at the high and `open` at the low accepted, 0.01 beyond refused, `low > high` refused, for NIFTY 50 and NIFTY BANK each; VIX in `problems`, named in the read line; the refusal line holds no level |
| 3 | Confirm | `confirm.py` `_compare`, `_results`, `_previous`; `fno/fo_bhavcopy.py` `read_index_values` | high and low at 0.00 and 0.01 off confirm, 0.02 off alert once; `previous_close` 0.10 off recorded and alerted; VIX differences never alerted; the previous file missing: waits, then one overdue alert naming the previous session's file, never again |
| 4 | Recheck | `comparison.py`, `reader.py` `_recheck` | a 0.05 change in `high` named in `fields_against_first` and the line |
| 5 | No level | the same lines | `test_no_levels.py`: planted highs, lows and previous closes (list, moved and official) in 7 forms appear in no line or alert, and the new fields reach the lines |
| 6 | Older records | `confirm._previous` returns `{}`, `compared` skips absent fields | 22 Oct's shape rechecked and confirmed on `last` alone, with no previous file needed |
| 7 | Gates | | full suite 14623 passed, 16 xfailed; ruff, format, `check_imports` clean; largest file 175 lines |
| 8 | Good, bad, boundary, empty | | as above; empty = a missing or blank field |

**Planted bugs: 10 of 10 caught** (each made, the tests run, then reverted):

| Planted bug | Tests failing |
|---|---|
| range edges excluded (`<` for `<=`) | 4 |
| VIX refused instead of recorded | 1 |
| no `low > high` check | 2 |
| new fields not required for checked indices | 18 |
| a level in the refusal text | 7 |
| high confirmed against itself | 2 |
| no wait for the previous session's file | 1 |
| VIX field differences alerted | 12 |
| recheck silent on fields | 6 |
| an official "-" read as 0.0 | 1 |

**Self-review (quality rule 3).** An independent review agent found no crash or level leak. Its four points:
1. **One odd official cell ("NA") would fail the whole day's confirm: accepted.** The fix: `read_index_values` reads the extra columns leniently (None), so the reader that needs one says "not in the official file" and alerts. A test plants "NA" in another index's row.
2. **The previous session may be a muhurat session: checked, no change.** Real files show NSE's previous close after muhurat is the muhurat close (4 Nov 2024: 23995.35 + 309.0 = 24304.35, 1 Nov's muhurat close; 23 Oct 2025: 25891.4 - 22.8 = 25868.6, 21 Oct 2025's), and the calendar's `previous_session` counts muhurat sessions. The calendar-start edge (2019) cannot arise for records from 2026.
3. **The overdue alert said "no official index-close file" while the previous session's file was the one missing: accepted.** The reason is now named (`NO_FILE`, `NO_PREVIOUS_FILE`, `FAILED_RUNS`), with a test.
4. **VIX problems were only in the record: accepted.** The read line now names them, with no level.

**Output sample (quality rule 6; test fakes, the record's values replaced by `<level>`):**
```
close read 2026-10-21: NIFTY 50, NIFTY BANK, INDIA VIX (list) recorded, NSE stamp 21-Oct-2026 15:30, closes/2026/10/2026-10-21.json sha256 970a82653bde
close recheck 2026-10-21: NIFTY 50 same (high differs by 0.05), NIFTY BANK same, INDIA VIX same, NSE stamp 21-Oct-2026 15:30, closes/2026/10/2026-10-21.recheck.json sha256 52c05ee0b992
close confirm 2026-10-21: NIFTY 50 confirmed, NIFTY BANK confirmed, INDIA VIX differs by 0.02 (list value)
record indices["NIFTY 50"]: {"high": <level>, "last": <level>, "low": <level>, "official_close": true, "open": <level>, "previous_close": <level>}
```

**Deviations and facts to know:**
- **An interface change:** `OfficialCloses.closes(day)` is now `values(day)`, returning open, high, low and close per index. DR1-1 (story/dr1-1-closes-records) imports it; its builder has been told. Whichever merges second updates the call.
- **One refusal text changed:** a missing `last` for VIX now reads "INDIA VIX has no readable last" instead of "...last or open", so it names the field.
- **Record readers:** FL1's `A4hTodayCloses` reads only `nse_stamp`, `last` and `official_close`, so it is unaffected. FL1-1f reads `open`, `high` and `low` when present.
- **After merge (quality rule 8):** the first session's read, recheck and confirm lines.

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
  + exposure`, k from config; superseded by stories C2c and C2d, 15 Oct 2026: k stresses the exposure too, and comes
  from A14c's factor file); with an open losing trade C2 never leaves more free than a broker that nets the
  premium (test);
- a GitHub Actions job (no AI) with the A13 shape, run each morning before the open (03:30 IST, retry 07:45 IST;
  GitHub starts this repository's morning crons 4-5 hours late, so the main run lands before 09:15 even then;
  orchestrator, 16 Oct):
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

**Depends:** A9, A11, C2, O6 · **Size:** M · **Status:** done: judge 77 PASS (round 2 2c3865e, merged 6568315; Groww check ee7f35b, merged e49705e; funds at entry 90dfcd3, merged 6647511); schedule on `story/a14-schedule`, awaiting the judge

---

## A14c. The stressed-margin factor recomputed from NSE's archived SPAN files

**Repository:** trading · **Lane:** 1 (money and risk: C2's margin stress)

**Description:** As the risk manager, I want the stressed-margin factor recomputed from NSE's own archived SPAN files
by one fixed, tested rule, with its evidence table, before each 30-day expiry, so that C2's crash buffer is measured,
not typed by hand, and never lapses by surprise.

**Context and why:** `config.yaml` `risk.stressed_margin` holds `multiplier: 1.45`, `as_of: 2026-10-14`,
`max_age_days: 30` (owner, 14 Oct 2026, DESK_DECISIONS: "1.45 now, by hand"; "a monthly recompute from the 2020 archive
can follow"). C2 and C4 refuse every trade once `(day - as_of) > 30` (`fno/risk/margins.py`,
`fno/checks/validity_margin.py`), so **from 14 Nov 2026 every paper trade is refused** unless a new value is entered.
1.45 came from a one-off hand run (response 77, "Stressed-margin factor"): the largest rise of a held position's NSE
margin from entry to exit (21 days before expiry), SF, SC and BF at widths 100, 200 and 300, over three hand-picked
windows (Jan-Apr 2020 1.265; May-Jun 2024 1.407, BF 300 entered 5 Jun; Sep-Oct 2026 1.127), rounded up to the next
0.05. No code in the repository reproduces it.

Facts checked on 15 Oct 2026 (builder, response to the orchestrator; strong evidence unless marked):
- **The measured quantity and the applied quantity differ.** 1.45 is the rise of the held position's whole margin
  (scan and exposure, "today's method"). C2 multiplies the scan only: `max(0, k x scan - NOV) + min(0, NOV) +
  exposure` (judge 75). On 14 Oct the scan is 1-14% of the margin (exposure 59,077.07 on every row), so k = 1.45 adds
  +0.6% to SF 100 (59,899 to 60,269), +5.7% to SC 300 (the largest) and 0% to every BF row (response 77's own table). A
  1.4x rise of a held SF 100's whole margin (about 84,000) is not covered.
- NSE writes day d's `i1` file on the evening of the previous session (stamps read 15 Oct: `nsccl.20261012` at Fri
  9 Oct 22:36, `nsccl.20261005` at Thu 1 Oct 22:32), so every day of a holding has its own file.
- Drive holds the `i1` files from 1 Oct 2026 (manifest `span-bod.csv`); A14's schedule adds one a session. The 2020 and
  2024 windows are not archived: response 77 read them ad hoc. All of 2020-2026 is about 1,700 files, about 16 GB.
- 2020's files charged a short-option minimum (5% of the index per short unit). A14's reader refuses any non-zero
  minimum (fail closed), so it cannot read 2020 files as they stand.
- A14's exposure rule (2%, 3% beyond 10% out of the money) is coded, not read from NSE. A circular that raises it shows
  in no file, so no recompute from files can see it.

**Scope.** In:
- a read-only research command `python -m fno margins stress-factor --from <d> --to <d>` that, for every entry day in
  the range and every structure and width that C2 trades, rebuilds the entry's legs (A14's builder, the same expiry
  rule) and recomputes their margin parts (scan, NOV, exposure) on each later day's first-archived `i1` file up to the
  exit day; it reports the largest stress factor a held position needed (owner question 1, as answered on 16 Oct):
  per holding, the smallest k for which C2c's stressed margin of the entry's parts, `max(0, k x scan - NOV) +
  min(0, NOV) + k x exposure`, covers what C2 counts (`initial()`) on every later day held; rounded up to the next
  0.05, with an evidence table (window, structure, width, entry day, day of the peak, figures);
- the 2020 short-option minimum modelled as SPAN does (per tier: the larger of the scan and the minimum times the short
  units), behind A14's calculator interface, so the same code reads every year; any other method difference is still
  refused by name;
- the A9 librarian back-fill of every session's `i1` file since 1 Jan 2020 into Drive with their manifest rows
  (owner question 2; about 1,700 files, about 16 GB);
- the evidence written to `research/data/margins/stress/stress_evidence_<run day>.csv` and `.md`, with
  `stress_files_<run day>.csv` (every session's file and SHA-256);
- **the factor applied automatically (owner question 3)**: each run appends one row to
  `research/data/margins/stress_factor.csv` (append-only, never edited): `as_of` (run day), `factor` (in force),
  `computed` (this run's rounded result), `unrounded`, `status` (`applied` or `held`), `peak` (window, structure, width,
  entry day), `coverage_through` (the last session the archive covers, checked as below), `evidence_sha256` (of the
  evidence CSV). C2 and C4 read the latest row (story C2d); `config.yaml` keeps
  only the method, the file path and `max_age_days`. A run never edits `config.yaml`;
- **coverage check first (ChatGPT review 117; it replaces a session count, which a same-count archive with a different
  missing date, or one ending a session early, would pass):** before computing, the run derives the required date set,
  every session A7's calendar gives (regular and special, not muhurat-only) from 2 Jan 2020 through the latest session
  before the run day, and checks each date has its first-archived `i1` file in the A9 manifest; any gap is named, no
  row is appended, and one #fno-desk line goes out, so stale or holed data can neither drop the worst holding nor reset
  the 30-day age; `coverage_through` is that latest session, recorded in the row and the evidence;
- guardrails, in this order: a result below 1.0 is refused by name and writes no row; a result at or above the factor in
  force is `applied` (a rise applies at once); **any result below the factor in force is `held`**: the row keeps the old
  factor and the alert asks the owner to approve the lower one (DESK_DECISIONS row, then a row with status `applied`
  written by the next run that cites it);
- incremental runs: the rule is a maximum over a window that only grows, so a run computes only the entries whose
  holding ended since the last run's newest entry and takes the larger of that and the last `unrounded`; a full
  re-run from 2020 is a flag (`--full`) and must give the same `unrounded` (test); the first run, and any run whose last
  row has an empty `unrounded` (C2d's owner seed of 1.45, a hand value), is a `--full` run, so the seed never becomes a
  floor of the measured series (judge 176);
- a GitHub Actions job (no AI, no broker key) each Sunday 10:00 IST: the librarian archives the week's `i1` files, the
  run appends its row, the job commits; a weekly run keeps the row fresh (`max_age_days` 30 leaves three missed weeks
  before C2 refuses);
- one #fno-desk line per run: the factor in force, the change, `applied` or `held`, and the peak's window;
- **A14c part 2 (orchestrator, 16 Oct 2026: built after part 1 merges, with its own judge; judge 237 note 3):** the
  broker check of owner question 4, one step in the daily Claude routine that already holds Groww's read-only
  access (never in GitHub Actions, which holds no broker key); the routine's prompt is story O1's, so this story adds
  the command and O1 adds its one line (judge 173 addendum 3, note 1): `python -m fno margins stress-broker-check`
  runs in every session's daily run, first, before the 3 pm quote parts (so its Groww requests never overlap the 14:55
  capture); it checks the latest `applied` row once: one read-only Groww margin request for the SF 100 basket on the
  latest A14 row, compared with that row, and appends the result to `research/data/margins/stress_broker_check.csv`
  (append-only: the factor row's `as_of`, the check time, both figures, `ok` or `mismatch`); if that `applied` row
  already has a result, or the latest row is `held`, it prints "nothing to check" and exits 0 (idempotent); a Groww
  failure exits 1 and the next session retries; it writes no other path. It runs only in market hours (Groww recheck,
  16 Oct 10:42 IST: SPAN within Rs 0.25 of the row; at 00:12 IST Groww was still on the previous day's file, +Rs 155).
  Part 1 (the recompute, the factor row, its line and the weekly workflow) does not wait for it: the check never holds
  the factor.

Out: changing C2's formula (story C2c) or C2's input source (story C2d); writing `config.yaml`; any order.

**Owner questions (each with a recommendation):**
1. **Which quantity does k measure? ANSWERED (owner, 15 Oct 2026, relayed by the orchestrator): "WHOLE MARGIN. k
   multiplies the whole margin (scan plus exposure), as it was measured."** **Measure ANSWERED (owner, 16 Oct 2026,
   DESK_DECISIONS 07f62385, response 235): "Proposed: smallest k needed".** The plain ratio of the counted margins, as
   first built, gave 3.55 in April 2020: for a debit structure (BF 200 entered 8 Apr 2020: scan 57,720, NOV 56,911,
   exposure 22,860) the bought legs' value nearly cancels the scan at entry, so the ratio measured the position losing
   value. The needed factor there is 1.7483 (1.75 covers the 83,970 peak; 1.45 left it 24,040 short). For a credit
   structure (NOV below 0) the needed factor equals the plain ratio. The separate story C2c makes C2 and C4 multiply the same quantity; its effect at k = 1.45 on
   the 14 Oct rows: a held SF 100 from about 59,900 to about 86,900 a lot (today's scan-only stress gives 60,269), so C2
   refuses more trades for the same capital, about 31% fewer lots (judge 173 note 3). The report also gives the scan's
   own rise, for information only.
2. **Which windows? ANSWERED (owner, 15 Oct 2026, relayed): everything since 1 Jan 2020.** Every entry day from
   2 Jan 2020 to the run day; later runs add the new days. The `config.yaml` comment ("the same windows, plus any later
   ones") is corrected when the first value from this run is entered.
3. **Who sets the value? ANSWERED (owner, 15 Oct 2026, relayed): automatic, with an alert.** The run applies the
   factor itself through `stress_factor.csv` and posts it to #fno-desk (scope above). The orchestrator proposed holding
   only a fall of more than 0.05; this story holds **every** fall (reasoning): the rule is a maximum over a window that
   only grows, so a correct run can never give a lower value, and any fall means a data or method fault, which must not
   lower a crash buffer unseen. Falls of 0.05 or less are therefore held too.
4. **NSE's circulars. ANSWERED (owner, 15 Oct 2026, relayed): accept the limit, plus one Groww comparison at each
   recompute; a mismatch alerts.** No history covers a rate NSE raises by circular (2020's minimum, exposure rates).
   The comparison: Groww's SPAN within Rs 1 of the row's `max(0, scan - NOV)` and Groww's exposure within 1% of the
   row's after rescaling to Groww's index (response 77's check 2 met both: SPAN to the rupee, exposure to the paisa on
   the same index base). A mismatch posts one #fno-desk line and does not hold the factor, which is NSE-based; it is
   evidence that A14's coded exposure rule may be stale.

**Acceptance criteria:**
1. Reproduction, run after the back-fill of question 2 (Drive's archive starts on 1 Oct 2026 and the 2026 window has
   September entries; judge 173 note 1): the command reproduces each of response 77's three windows within 0.001, or
   explains each difference with the files' figures: 1.127 (Sep-Oct 2026, BF 100), 1.265 (Jan-Apr 2020, the
   short-option minimum binding) and 1.407 (May-Jun 2024, BF 300 entered 5 Jun, today's binding value). The 2020 and
   2024 figures are anchors the builder did not write (judge 173 note 2). **Done (16 Oct 2026, response 235):** all three reproduce
   to 0.001 with response 77's own measure, scan plus exposure, read to the window's end: 1.2650 (SF/SC entered 7 Apr
   2020, to 30 Apr, every structure alike), 1.4073 (BF 300 entered 5 Jun 2024, to 28 Jun) and 1.1272 (BF 100 entered
   28 Sep 2026, to 14 Oct). Held to the exit with the owner's measure (the needed factor), they are 1.7483, 1.3872 and
   1.0589.
2. Hand computation: on planted SPAN files (a held SF whose scan doubles on day 3) the reported factor and its day
   equal a hand calculation (test); a mutation that skips a day or takes the first rise instead of the largest fails a
   test. The needed factor (owner, 16 Oct): the real BF 200 of 8 Apr 2020 gives 1.7483, and 1.75 covers its 83,970
   peak (test); for a credit structure it equals the plain ratio (test); it is the smallest covering k on random parts
   (test); a mutation back to the plain ratio, or one returning a k that does not cover, fails a test.
3. Point in time: each day uses that day's first-archived `i1` file written before 09:00 IST on it, as A14 does
   (test); a missing day refuses the whole run before any computation (criterion 8), so no entry is ever filled.
4. 2020 method: a planted file with a non-zero short-option minimum gives the SPAN figure by hand (test); any other
   method difference is refused by name (test).
5. Output: the CSV and Markdown name every file's SHA-256, the rule, the windows and the run day; a second run on the
   same files writes byte-identical output; nothing writes `config.yaml` (test).
6. Owner questions 1 and 2 are recorded in DESK_DECISIONS (answered 15 Oct, commit d68b1a9c: "Crash buffer applies to
   the whole margin" and "Stressed-factor recompute uses everything since 1 Jan 2020"); 3 and 4 with the hold-every-fall
   rule at da0f769d; C2c and C2d are merged before it, so the value is applied as it was measured.
7. Guardrails (tests on planted runs): a rise is `applied`; any fall, 0.01 included, is `held` with the old factor kept
   and one alert asking the owner; a result below 1.0 is refused with no row; an owner-approved fall is `applied` only
   when its DESK_DECISIONS row is cited; a mutation that applies a fall fails a test.
8. Coverage (planted manifests and calendar, ChatGPT review 117): (a) the same number of files with one required date
   missing and another date present instead: refused, the missing date named, no row; (b) the latest session missing
   while every earlier one is present: refused, no row, so the 30-day age is not reset; (c) a complete archive: the
   row's `coverage_through` is the latest session before the run day (tests).
9. Incremental equals full: on planted files the incremental run's `unrounded` equals `--full`'s (test); after a row
   with an empty `unrounded` (the owner seed) the run is `--full` and the seed's 1.45 is not a floor (test: planted
   files whose true maximum is 1.30 give `computed` 1.30, then `held` against the seed's factor 1.45).
10. Alerts (part 1): one #fno-desk line per run with the factor, the change, the status and the peak (test). Broker
   check (part 2, its own judge): a Groww mismatch beyond the stated tolerance posts one line and leaves the factor applied (test on planted figures; the live check
   is read-only and places nothing); a second broker check of the same `applied` row writes nothing and prints
   "nothing to check" (test).
11. Code size, lint, imports and the full suite pass.

**Timeline:** story text judged by about 20 Oct 2026; build and back-fill by about 3 Nov; first run about 6 Nov; judge
by 11 Nov; 1.45 expires after 13 Nov. Then weekly (Sunday), automatic. Bootstrap: story C2d seeds
`stress_factor.csv` with the owner's 1.45 of 14 Oct (status `applied`, source response 77), so C2 keeps its current
factor until the first run. **Hard date (orchestrator, 15 Oct):** the code merged and its first row written by about
7 Nov, a week before every trade is refused from 14 Nov; any threat to that date is reported at once.

**Known limit:** no cache of the files' arrays. An incremental weekly run reads only the files back to the earliest
holding that ended since the last row (about 35-50 files); only a full run reads all of them once (about 1,700). A
cache would add a second store for no real saving (orchestrator agreed, 15 Oct). **Read-ahead (orchestrator, 16 Oct):**
one Drive stream gave 0.41 MB/s on 16 Oct (27-30 s per 12 MB file, so about 14 hours for a full run, past the
workflow's 330 minutes) and parallel streams were each as fast; the run downloads up to
`risk.stressed_margin.recompute_workers` files (8) ahead, each thread with its own Drive session, and still feeds them
in day order (a test proves the same row and byte-identical evidence with and without it). A download error writes
nothing and sends the one #fno-desk line. The first Actions run measures the seconds per file.

**Fail-closed details (builder self-review, 16 Oct 2026).** Any other stop (Drive consent expired, Drive settings
missing, a year missing from A7's calendar, a bad manifest row) also writes no row and sends the one line, naming the
error; A7's calendar ends on 25 Dec 2026, so from about 30 Nov an entry on a January 2027 expiry needs NSE's 2027
holiday rows first. A held position whose margin cannot be computed on a later day (a strike no longer listed) is
dropped and named, and the factor it needed up to then still counts, so a hole can never lower k; an entry the model
cannot price is named too, and the line gives the count. The workflow commits the factor row and its evidence only
when the factor step succeeded, and posts one line when the result was computed but not committed to `main`.

**Known limit: what is measured so far (16 Oct 2026, response 235).** The factor of about 1.75 comes from Jan-Apr 2020,
Jun 2020-Dec 2023, May-Jun 2024 and Sep-Oct 2026 (entries). Jan 2024-Aug 2026 outside May-Jun 2024 is not yet
measured; the first full run reads every session since 2 Jan 2020 and may set k higher. Response 77's three figures
(1.265, 1.407, 1.127) were a different measure, scan plus exposure read to the window's end; the evidence table shows
them beside this run's needed factor for reference only.

**Open items for when A14c resumes (after the phase-1 freeze):**
- **k per underlying.** The factor is measured on NIFTY monthly history only. The market school (MS-P1m) applies it to
  BANKNIFTY, FINNIFTY, MIDCPNIFTY and NIFTY's weeklies, labelled "measured on NIFTY monthly only [reasoning only]"
  (orchestrator, 22 Oct 2026).
- **k times the expiry-day ELM.** MS-P1m prices a school trade on its own expiry day with SEBI's extra 2% ELM
  (2024/132 para 5.6). C2's k also multiplies the exposure, so k 2.1 on the doubled ELM roughly doubles an expiring
  fly's stressed margin: NIFTY weekly SF 100 on 13 Oct 2026 needed Rs 2,48,443 a lot. That overstates the margin
  [reasoning only], which is conservative and accepted for P1 (orchestrator, 22 Oct 2026). The follow-up decides
  whether k should stress an expiry-day ELM at all, measured like the rest of k.

**Judge verifies:** recomputes one held position's needed factor by hand from two real files; plants a late file and a missing
day; checks the 2026 reproduction and the evidence table against the files' SHA-256.

**Depends:** A9, A14, C2, C2c, C2d; part 2 also O1 (the routine step) · **Size:** M · **Status:** text PASS (judge 173
addenda 1-3); part 1 code with judge D (judge 237), part 2 (the broker check) after part 1 merges

---

## A15. India VIX full history

**Repository:** trading

**Description:** As the statistician and the risk manager, I want India VIX's daily open, high, low and close for
every day NSE publishes, archived raw in Drive and as a checked table in the repository, so that the weather can be
calibrated and crash replays run over more than one crash.

**Context and why:** design v2 section 2.1 and `REPLAN_new_stories.md`: the repository holds India VIX closes only from
2017 (A3, A10's warm-up), which covers one crash (2020). Weather calibration and crash replay need 2008, 2011, 2013,
2016, 2020 and 2024. Facts checked on 14-15 Oct 2026 (builder, response 100):
- NSE's website serves the history as JSON (`/api/historicalOR/vixhistory?from=&to=`), at most 70 rows per answer
  (the rest are cut silently), and nothing before **19 Jul 2010** (every window from Nov 2007 to Jun 2010 answers no
  rows), although India VIX was launched in 2008. NSE Indices' own history page refused the cloud session.
- NSE's daily index-close files are no substitute before 2017: the 2 Jan 2013 file has no VIX row (the 4 Jan 2016
  file has one; the first year with one was not searched); 2017 onwards is already archived.

**Scope.** In:
- a raw dataset `nse/indices/india-vix-history`, one NSE answer per ended calendar month, archived to the owner's Drive
  with the A9 rules (never overwritten, manifest row at save time), resumable;
- A11's revision rule: a later NSE version of a month is kept beside the original and named day by day;
- a derived table `research/data/vix/india_vix_daily.csv` with a README (source URL, terms, `first_seen_at`, columns,
  units, findings) and its checks (gaps, doubtful levels, overlap with the index-close closes);
- the parts behind interfaces (`RawFileSource`, `RawFileStore`, `VixMonthReader`), wired only in
  `fno/vix_history/wiring.py`; commands `python -m fno vix-history fill|sweep|check|verify`.

Out: VIX before NSE's first served day (named as a gap with the evidence); a schedule (the daily VIX comes from the
index-close files, O6); any change to `warmup_closes.csv`, the panel, a frozen file or a forecast input.

**Acceptance criteria:**
1. Source and terms named: the README gives the publisher, the exact URL pattern, the terms position (with its
   evidence label) and the request pace.
2. Full range: every month from NSE's first served day to the last ended month is archived; the first day is found by
   probing (recorded with the probe range), not assumed; anything earlier than NSE's launch of India VIX that the
   source does not serve is stated as a gap, with the alternatives tried.
3. Derived rows equal the raw files: a command recomputes every row from the archived files in Drive (values, source
   path and SHA-256) and lists every difference, including every archived day the table lacks (a deleted month, a
   table cut short); tests plant a changed value, a wrong SHA-256, a removed month and a cut end, and each is named;
   every committed row's SHA-256 equals its month's manifest row (test).
4. Point in time: every row carries `first_seen_at` (archive time, stated as such); the README states when a day's
   value is known (after its 15:30 close, so a 15:00 decision on d uses d-1 at the latest); rows are only appended
   (old bytes are a prefix of the new), a day present is never rewritten, a hole is never filled from behind, a month
   still running is never fetched even when asked for (tests of the command's month range: mid-month, its last day,
   the first of the next month, `--to` the running month);
   revisions only through A11 (stored beside the original, the table unchanged, changes named day by day; an error
   page is never kept as a version) (tests).
5. Overlap check: the table's close is compared day by day with the VIX closes the repository already holds from 2017
   (A3/A10); every mismatch is listed in a committed file, rounding told apart from real differences, never fixed.
6. Gaps recorded, never filled: sessions without a row (NSE's calendar), and, before the calendar's first year,
   weekdays without a row as unverified; rows on muhurat and special sessions labelled, with the README telling users
   to select regular sessions through the A7 calendar; doubtful levels (zero, open or close outside the day's range)
   kept as published and listed. A sweep that finds a missing original names it and fails.
7. A missing or failed download (no answer, an HTML page, a cut or malformed answer) writes nothing and is named; a
   stored file that fails its check or its manifest SHA-256 is reported and never replaced; a rerun fetches only what
   is missing (tests).
8. No frozen file changes (FREEZE records and the frozen-file tests pass); code size, lint, imports and the full suite
   pass.

**Gap list (quality rule 2): every requirement of design v2 2.1's A15 row, REPLAN's A15 paragraph and 2.1's
outputs and failure modes.**

| Requirement | Where |
|---|---|
| India VIX daily open, high, low, close | criteria 2, 3 |
| back to its start | criterion 2 from NSE's first served day (19 Jul 2010); **2008 to Jul 2010 out**: NSE does not serve it (probed), NSE Indices refused; open owner question |
| from NSE historical files | criterion 1 |
| frequency daily | **out of scope**: no schedule (orchestrator: no schedules); daily closes come from the index-close files (O6); monthly `fill` by hand, lane 1 |
| into Drive (raw) | criteria 2, 7 |
| a derived table | criteria 3, 4, 6 |
| A11's revision rule | criterion 4 (revisions) and 6 (missing original) |
| every row with source, as_of, first_seen_at and the raw file's SHA-256 (2.1 outputs) | `source_path` (the publisher's file), `date` (as_of), `first_seen_at`, `source_sha256`: criteria 3, 4 |
| look-ahead failure mode (2.1): a value used before it was known | criterion 4 (known-at rule) |
| a source rewriting history (2.1) | criterion 4 (revisions kept apart) |
| gaps recorded, never filled (2.1) | criterion 6 |
| why: weather calibration and crash replays over several crashes | context; covers 2011, 2013, 2016, 2020, 2024, not 2008 |

**Judge verifies:** runs `vix-history verify` (or recomputes 5 random months from Drive by hand) and `vix-history
check` (committed checks unchanged); probes NSE for a window before 19 Jul 2010; plants a changed row and a rewrite of
an old row; checks 2 Mar 2024 and the zero-open days against NSE; confirms no frozen file changed.

**Depends:** A9, A10, A11 · **Size:** S · **Status:** done: judge 100 addendum 1 PASS (b377af2), merged
176a1a1 (addendum 2; claims: `reviews/claude/response_100_a15-vix-history.md`)

## A17. Global cues, daily

**Repository:** trading

**Description:** As the risk manager and the macro economist, I want the overnight global cues (previous US closes of
the S&P 500 and Nasdaq 100, the US 10-year yield, Brent and USD/INR) as they were known before each NSE open, from
official or primary sources, so that the weather and gap-risk work use real cues and never a value published after
the decision.

**Context and why:** design v2 section 2.1 (data table) and the weather's drivers (2.3); `REPLAN_new_stories.md` A17.
Facts checked on 15 Oct 2026 (builder, response 103):
- FRED's site is refused by this environment's network policy, and S&P Dow Jones Indices answers 403. Nasdaq's and
  Cboe's sites are reachable, but their terms forbid automated capture (Nasdaq) and storing index values (Cboe).
  Owner decision a927390 (15 Oct 2026): use them anyway for personal, non-commercial research, with raw files and
  values in Drive only, at most one download a day, and no display until the owner approves one.
- The US Treasury (yearly par-yield CSV), EIA (Brent, released weekly), RBI (reference rate archive; none from
  25 Jul 2018 to 11 Apr 2022) and FBIL (reference rates from 10 Jul 2018; public site about a week late) are
  reachable.

**Scope.** In:
- one `GlobalCueSource` per cue and publisher, wired only in `fno/global_cues/wiring.py`;
- raw copies archived in the owner's Drive through `RawFileStore` (A9), one per fetch, never overwritten, each logged
  with its URL, SHA-256 and fetch time; a later copy that changes a held value is logged as a revision and the table
  keeps the first value (A11's rule);
- a derived table per cue in `research/data/global-cues/` with a README (source, URL, time zone, publication lag,
  terms with evidence labels), `first_seen_at` and `provenance` (`live` or `backfilled`) on every row;
- the as-of rule for an India date across time zones and holidays, at an explicit cutoff (09:15 or 15:00 IST), with
  a live-only mode;
- the private cues (S&P 500 from Cboe, Nasdaq 100 from Nasdaq): tables in Drive only, the four copies already there
  adopted as the history start, at most one download a day;
- commands `python -m fno global-cues fill|check|verify|adopt`.

Out: a schedule; any display of the private cues (open owner item); any change to a frozen file, a forecast input
or the weather.

**Acceptance criteria:**
1. Each cue names its publisher, URL, the time zone of its dates, when a value is published and the terms that apply,
   each terms statement with an evidence label; a source whose terms restrict this use is named with its terms quoted
   and is used only under a recorded owner decision; a source the network refuses is named and another is proposed.
2. Every value carries `first_seen_at`; back-filled history is marked `backfilled` and only a value first seen before
   09:15 IST on the first NSE session after its date is `live` (test on the committed tables recomputes the label).
3. The as-of rule at an explicit cutoff (09:15 or 15:00 IST): a value is usable when its source says it was published
   before the cutoff (US close 16:00 US Eastern with daylight saving; reference rate 13:30 IST; assumptions named);
   a US Monday holiday gives Tuesday the Friday value; the same day's USD/INR counts at 15:00 and not at 09:15; live
   use also needs `first_seen_at` before the cutoff (tests, including the exact publication time).
4. Raw copies in Drive through `RawFileStore`, never overwritten, each logged; a later change to a held value is
   logged as a revision and never rewrites the table; a late value is logged, never inserted; tables are append-only
   (tests).
5. Gaps recorded, never filled (weekdays without a value, repeated values); RBI and FBIL compared on every date both
   publish, differences listed, the number compared printed (tests; committed check files reproduce); a cue whose
   newest value is older than its source allows is named STALE.
6. A failed download, a file that is not the publisher's, an empty answer, or a copy Drive refuses writes nothing to
   that cue's table and is named; a Drive or setup failure stops the command with one line and exit 1 (tests).
7. Derived rows equal the archived copies: `verify` recomputes every row's value from its copy, checks
   `first_seen_at` is not before the copy was fetched and recomputes `provenance`, names a date held twice, rows out of
   order and an empty cue table; tests plant each.
8. Behind interfaces with one composition root (added to CLAUDE.md); no frozen file changes; code size, lint, imports
   and the full suite pass.
9. Private cues (owner decision a927390): their rows, revisions and gaps are written to Drive only, as write-once
   parts; the repository holds only their copy logs (paths, URLs, hashes, sizes) and code; tests use made-up values
   labelled fake; a second download on the same IST date is refused; the kept copies are adopted at their own fetch
   times (tests; a test checks no private table or value is in the repository).

**Gap list (quality rule 2): every requirement of REPLAN's A17 paragraph, design 2.1's data row, outputs and failure
modes, and the orchestrator's brief.**

| Requirement | Where |
|---|---|
| previous US close, S&P 500 and Nasdaq 100 | criterion 9 (Cboe, Nasdaq; Drive only, owner decision a927390), criterion 1 (their terms and FRED's notices quoted in the README) |
| owner's conditions: Drive only, one download a day, no display until approved | criterion 9; display **out**, an open owner item |
| Brent | criterion 1 (EIA; weekly release, every row `backfilled`) |
| USD/INR | criterion 1 (RBI, and FBIL for RBI's 2018-2022 hole) |
| US 10-year yield | criterion 1 (US Treasury) |
| each behind `GlobalCueSource`, one composition root | criterion 8 |
| `first_seen_at` on every value; back-fill marked as such | criterion 2 |
| official or primary sources first; source, publication lag and time zone named | criterion 1 |
| NSE currency and MCX files (design 2.1's suggestion) | **out**: NSE's currency-derivative file paths tried answered 404 and MCX answered 403 from this session; RBI and FBIL are the official reference rate, and NSE's USD/INR futures are a different quantity (a futures price) |
| FRED for US closes (design 2.1) | **out**: refused by the network policy, and carries the same owners' restrictions (quoted in the README) |
| "previous US close known before 09:15 IST": the date mapping across time zones and US holidays | criterion 3 |
| known before 09:15 IST (REPLAN) and "global cues as of 15:00" (2.1 outputs) | criterion 3: both cutoffs, chosen explicitly |
| raw files in Drive (A9) with A11's revision rule | criterion 4 |
| derived daily table with a README | criteria 1, 2, 5 |
| gaps recorded, never filled | criterion 5 |
| a failed download writes nothing and is named | criterion 6 |
| a publisher revising history kept apart (2.1; FRED revises) | criterion 4 |
| look-ahead failure mode (2.1) | criterion 3 (`live_only`) |
| licence and terms of each source, honestly labelled | criterion 1 |
| no scheduling; O6 fetch-and-trigger | **out** (orchestrator: no schedules) |
| no frozen files | criterion 8 |

**Judge verifies:** runs `global-cues verify`; reads each source's terms itself; checks two US-holiday India dates
with `value_for`; plants a revised value and a late value; confirms no S&P 500 or Nasdaq 100 data is in the repository.

**Depends:** A7, A9, A11 · **Size:** M · **Status:** built, with the US closes in Drive only (owner decision
a927390); awaiting judge (claims: `reviews/claude/response_103_a17-global-cues.md`, addendum 1)

---

## A17b. Guards before any consumer reads a global cue

**Repository:** trading

**Description:** As the risk manager and the statistician, I want every global-cue reading to say how old it is and
whether it is the session it should be, so that the weather, M1 and the forecasts never use a stale or missing US close
as if it were last night's.

**Context and why:** judge 103 (A17 PASS, 15 Oct 2026) minors 1, 3, 4 and 5, and judge 100 (A15) minors; orchestrator,
15 Oct 2026. Judge 103 found that `value_for` returns sp500's 14 Oct value for 27 Nov 2026, six weeks old, and that on
15 Oct at 09:15 nasdaq100's "previous close" is 13 Oct, because Nasdaq lacked 14 Oct. Only the run says STALE. No code
reads a cue yet, so this must be done before the first consumer. Judge 103 minor 2 (FBIL in a public repository) is
the orchestrator's decision: the table stays public for now, as an open owner item (superseded: the owner moved it to
Drive on 15 Oct 2026, story A17d).

**Scope.** In:
1. **Readings with an age and an expected date.** A `CueReading` returns the row, its age in calendar days from the
   India date, the date the source *should* have given (its expected value date), and a status. Statuses, decided in
   this order:
   - `none`: nothing usable;
   - `current`: the value is the expected date's, **whatever its age** (after Hurricane Sandy, 26 Oct 2012's close is
     the expected one on 31 Oct and is `current`);
   - `ahead`: newer than the expected date (the calendar did not expect a value that day but the source published one,
     e.g. RBI on an NSE holiday). Usable like `current`, and flagged so the calendar mismatch is seen;
   - `behind`: older than the expected date, age within the source's `max_age_days`;
   - `stale`: older than the expected date **and** age over `max_age_days`.
   For a cue without an expected date (Brent) only `behind` (age within `max_age_days`), `stale` and `none` are
   possible.
   `value_for` stays for research and gains no silent behaviour. Callers use `reading_for` and must refuse `stale` and
   `none`. A caller using `behind` must state it in its own rules.
2. **A US stock-market session calendar** (behind a new `UsSessionCalendar` interface) gives the expected date for the
   S&P 500 and the Nasdaq 100: the last NYSE trading date whose close is published before the cutoff. It is built
   from:
   - NYSE's holiday rules, computed: weekend observance, Good Friday from Easter, Juneteenth from 2022;
   - a sourced list of unscheduled NYSE closures since 2007, each row with an https source:
     - 2 Jan 2007, national day of mourning for President Ford;
     - 29-30 Oct 2012, Hurricane Sandy;
     - 5 Dec 2018, President G. H. W. Bush;
     - 9 Jan 2025, President Carter.
   Reasoning only: the computed rules are not NYSE's own published list for each year. The test (criterion 2) checks
   them against a **dates-only list of US trading days** committed as
   `research/data/global-cues/us_trading_dates.csv`. It is derived from the Drive-only S&P 500 table, with a column
   saying whether the Nasdaq 100 table has the date too. Orchestrator's decision (owner away, logged): trading dates
   are exchange-calendar facts, not index values, so the Drive-only rule for values still holds. The list is
   rewritten by `global-cues check` when the Drive settings are present. Nasdaq's extra holiday rows (repeated values)
   show as Nasdaq-only dates and are listed, not counted as sessions.

   **The US 10-year is not on the NYSE calendar** (judge 116: `us10y.csv` has no value on Columbus Day 2025 or
   Veterans Day 2024, when NYSE was open, and has values on Good Friday 2015, 2021 and 2023, and on 2 Jan 2007,
   29 Oct 2012 and 9 Jan 2025, when NYSE was closed). It follows the bond-market (SIFMA) calendar. Simplification,
   like USD/INR's: its expected date is the previous Monday-to-Friday weekday before the cutoff. A bond-market holiday
   then shows as `behind`, never wrongly as `current`; a sourced SIFMA calendar is **out** for now.

   For the USD/INR cues the expected date is the previous **NSE session** (the A7 calendar's `regular` or `special`
   sessions, not plain Monday to Friday) or, at 15:00, the same day when it is one. This is a simplification: RBI's and
   FBIL's holidays are not NSE's. A mismatch shows as `behind` or `ahead`, never wrongly as `current`. **FBIL will
   almost always read `behind`**: its public site trails by about a week. For Brent there is no expected date; age
   only.
3. **`max_age_days` per cue for readings:**
   - US index closes and the US 10-year: 4 days. Thursday's close on Monday covers a Good Friday, and Friday's close on
     Tuesday covers a US Monday holiday.
   - USD/INR (RBI): 5 days.
   - FBIL: 14 days (its public site trails a week).
   - Brent: 16 days (weekly release).
   These are the run's STALE limits made per reading. The US numbers are newly tightened from 7 days, to the
   calendar's worst normal case.
4. **The `live` label skips muhurat sessions.** The first NSE open after a value date is the first `regular` or
   `special` session; a muhurat session has no 09:15 open. Committed labels are unchanged, because every affected row
   is already `backfilled`; a test recomputes them all.
5. **`adopt` checks Drive's own creation time.** The copy's `createdTime` in Drive must fall within 10 minutes after
   the time in its path; otherwise adopt refuses and names both times. This needs a new read of Drive metadata behind
   the store interface; stores without it refuse adopt.
6. **The once-a-day rule also caps failed attempts.** Every download attempt of a once-a-day cue is logged (time and
   outcome, no value) in `research/data/manifests/global-cues/attempts/<cue>.csv`. A third attempt on one IST date
   is the last: after 3 attempts, or after 1 saved copy, nothing is downloaded that day, and the run says so.
7. **Judge 100's A15 minors:**
   - a test of `vix-history sweep`'s exit code when the original is missing;
   - the README's muhurat wording: one-hour sessions, in the evening until 2024 and 13:45-14:45 IST in 2025, per the
     calendar's circulars;
   - the `lambda` and `noqa` in `fno/vix_history/wiring.py` replaced by a named function.
8. **FBIL:** the data README records the orchestrator's decision (the table stays public, non-commercial use of a
   published benchmark) as an open owner item. Superseded by story A17d (the owner's decision: FBIL in Drive).

Out: any consumer (M1, the weather, forecasts); any display of the private cues; changing past table rows.

**Acceptance criteria:**
1. `reading_for` gives row, age, expected date and status, decided in the stated order. Tests cover each status, with
   good, bad, boundary and empty cases:
   - 15 Oct 2026, 09:15, nasdaq100 last value 13 Oct: `behind` (expected 14 Oct);
   - 27 Nov 2026 with nothing after 14 Oct: `stale`. The expected date is 25 Nov: Thanksgiving is 26 Nov 2026, from the
     computed 2026 US calendar;
   - 31 Oct 2012 at 09:15, sp500 last value 26 Oct: `current` (Sandy closed NYSE on 29-30 Oct), although 5 days old;
   - usdinr_rbi with a value for a date that is an NSE holiday but an RBI business day: `ahead`;
   - us10y with a value for Good Friday read on the following Monday: `current`. Under the Monday-to-Friday rule
     Good Friday is the expected date; that rule never makes us10y `ahead`;
   - an age exactly at `max_age_days` is `behind`, one day more is `stale`;
   - Brent: only `behind`, `stale` or `none`;
   - no rows: `none`.
2. The US stock-market calendar's expected date is right on:
   - a US Monday holiday (MLK, 20 Jan 2026 gives 16 Jan);
   - Good Friday (Monday gives Thursday);
   - Thanksgiving week;
   - Juneteenth before and after 2022;
   - a weekend-observed holiday;
   - each listed closure;
   - US summer and winter time at 09:15 and 15:00.
   A CI test checks the committed `us_trading_dates.csv` (dates only) against the calendar: every weekday since 2007
   without an S&P 500 date is a holiday or a listed closure, and every S&P 500 date is a computed session; any
   mismatch is named. A second CI test checks us10y's own dates against the Monday-to-Friday rule: every missing
   weekday is listed as a bond-market holiday or gap, never treated as a session.
3. The `live` label never uses a muhurat session as an open (test with a value dated the day before a muhurat
   session); every committed label still recomputes.
4. `adopt` refuses a copy whose Drive creation time is before its path time or more than 10 minutes after it, and a
   store that cannot give the time (tests with a fake store; one real check on the four adopted copies).
5. Attempts are logged and capped: a third failed attempt is the last that day, and a saved copy ends the day's
   downloads; the attempt log holds times and outcomes only (tests).
6. Judge 100's minors are done (tests for the sweep's exit code; README text; no `noqa` left in the vix wiring).
7. The FBIL decision is in the data README as an open owner item.
8. Quality rules:
   - a gap list;
   - a self-review by independent agents;
   - a broken-code proof per criterion;
   - real output in dates, ages and statuses only, never a private value.
   Code size, lint, imports and the full suite pass; no frozen file changes.

**Gap list (quality rule 2):**

| Requirement (source) | Where |
|---|---|
| `value_for` refuses or marks a value older than `max_age_days` (judge 103 minor 1; orchestrator (1)) | scope 1 and 3, criterion 1 |
| readers check the previous US session before using a US close (judge 103 minor 1; orchestrator (1)) | scope 2, criteria 1-2 |
| the US 10-year's own calendar (judge 116 a) | scope 2: the Monday-to-Friday simplification; a sourced SIFMA calendar **out** |
| status precedence; a value newer than expected; Brent's statuses (judge 116 b) | scope 1, criterion 1 |
| the archived-table test in CI without Drive (judge 116 c) | scope 2: the dates-only `us_trading_dates.csv` (orchestrator's decision), criterion 2 |
| muhurat is not an NSE open in the labels (judge 103 minor 3; orchestrator (3)) | scope 4, criterion 3 |
| `adopt` cross-checks Drive's creation time (judge 103 minor 4; orchestrator (4)) | scope 5, criterion 4 |
| failed attempts capped (judge 103 minor 5; orchestrator (5)) | scope 6, criterion 5 |
| FBIL in a public repository (judge 103 minor 2) | scope 8, criterion 7: an owner item, the table stays |
| A15 sweep exit code, muhurat wording, `lambda` + `noqa` (judge 100 minors) | scope 7, criterion 6 |
| no consumer reads a cue before this story (judge 103) | out of scope: consumers come later and must use `reading_for` |
| RBI's own holiday calendar for USD/INR | **out**: the simplification is stated in scope 2; it can only make a reading `behind`, never wrongly `current` |

**Judge verifies:** runs `reading_for` on real tables for 15 Oct 2026 and 27 Nov 2026 (statuses and dates only); checks
the US calendar against the archived trading dates; plants a muhurat case, a mis-timed adopt and a fourth attempt.

**Depends:** A17 · **Size:** S · **Status:** story text for the judge's check (quality rule 1); no code yet

---

## A17d. FBIL's USD/INR table moves to Drive

**Repository:** trading

**Description:** As the owner, I want FBIL's USD/INR reference-rate table kept in my Drive, not in this public
repository, because FBIL does not authorise commercial use of its data without written permission.

**Context and why:** owner decision of 15 Oct 2026 (`docs/DESK_DECISIONS.md`, row "FBIL's USD/INR reference-rate table
moves to Drive"). It reverses response 113's decision 17 and closes A17b's open owner item (judge 103 minor 2). A17
already keeps the US closes this way (owner decision a927390): a source marked `private` has its rows, revisions and
gap list in Drive (`DrivePartsRowLog` and `DriveSnapshots` under `derived/global-cues/<cue>/`). The repository keeps
only the copy log (paths, URLs, SHA-256 values and sizes). Readers go through `wiring.build_tables` and
`build_reader`, which already download a private table first. Nothing outside `fno/global_cues/` reads
`usdinr_fbil`: the weather reads the US cues only, and no forecast, check, dashboard or freeze uses it (searched
15 Oct). So this story only moves the cue to that existing mechanism. It adds no class, option or new path.

**Facts (15 Oct 2026, strong: read from the files):**
- `research/data/global-cues/usdinr_fbil.csv` holds 1,981 rows, 10 Jul 2018 to 7 Oct 2026, all `backfilled`, all
  first seen at 06:16:31 IST on 15 Oct.
- Its two raw copies are already in Drive's raw area. The copy log is `research/data/manifests/global-cues/
  usdinr_fbil.csv`: the full history at 06:16:31 and a top-up at 06:17:49.
- The shared public `revisions.csv` does not exist yet, so no FBIL revision is public.
- `checks/gaps.csv` lists 171 FBIL gap dates (dates only).
- `checks/overlap_usdinr.csv` has its header only, but its `fbil` column would hold FBIL values on any date where RBI
  and FBIL differed.

**Scope.** In:
1. **FBIL becomes private.** Set `private = True` on `FbilUsdInrSource`, the same flag the US index sources use. Rows,
   revisions and gaps then go to Drive through the existing wiring. `once_a_day` and `may_hold_unfinished` stay off:
   they are the US closes' own conditions, and FBIL publishes one rate a day, a week late.
2. **The public overlap check names dates, never rates.** `overlap_usdinr.csv` keeps `date,kind` only, with no `rbi`
   or `fbil` column. A difference against the public RBI value would reveal FBIL's rate, so no difference is
   published either. The run line keeps its counts ("N dates compared, differs M").
3. **The table moves without losing a row or a first-seen time.** After the merge, `global-cues adopt` takes the two
   Drive copies, in their fetch order, into the Drive table. It is A17's own path: each row is first seen at its
   copy's fetch time, and Drive's creation-time check applies. A one-off comparison then shows that the Drive table
   equals the repository file row for row, on every column, with `git show` of the last commit that held it. It
   prints counts and one SHA-256 over the sorted rows, never a value.
4. **The repository file is removed in its own commit,** after the comparison passes:
   `research/data/global-cues/usdinr_fbil.csv`, and FBIL's rows in `checks/gaps.csv` (they move to Drive's gap
   list). The copy log stays: hashes and paths only, as for the US closes.
5. **Tests and docs follow.** `test_no_private_cue_has_a_table_or_values_in_the_repository` names `usdinr_fbil` too,
   so a committed FBIL table, revision or gap row fails CI from then on.
   - Two fixtures hold real FBIL rates: `test_sources.py:37` and `test_as_of_checks.py:70-72`. They get made-up
     values.
   - Docs:
     - the global-cues README: the public and private lists, the overlap columns, and the closed owner item;
     - A17's and A17b's FBIL lines, marked as superseded by this story;
     - the docstrings of `row_log.py`, `wiring.py`, `check_files.py` and `source.py`;
     - `fno/storage/README.md` ("private" beside FBIL's raw folder).

Out:
- Rewriting git history to purge the old file and old quotes. The owner chose "repos stay public" on the same day, and
  a rewrite would break every clone and session.
- RBI's public table (`usdinr_rbi.csv`): RBI's own publication, not FBIL's.

**Known limits:**
- Past copies stay readable in git history: the table at d359fc3e and later commits up to the removal, and one FBIL
  row quoted in `reviews/claude/response_103_a17-global-cues.md` (a historical record, left as written).
- RBI's public table carries the same rate on the 1,086 dates both publish (A17's overlap: no difference). So FBIL's
  values stay public through RBI on those dates; only its 2018-2022 fill is unique to FBIL.
- Without the Drive settings (CI, a fresh clone), FBIL is skipped like the US closes, and the overlap check compares
  0 dates.

**Acceptance criteria:**
1. `FbilUsdInrSource.private` is true. `build_tables(include_private=False)` has no `usdinr_fbil`, and
   `build_tables()` with the Drive settings reads it from `derived/global-cues/usdinr_fbil/rows`. Tests use a
   local-folder Drive: a fill writes FBIL's rows and revisions there and none into the repository folder.
2. `overlap_usdinr.csv` has columns `date,kind`. A planted difference gives one `differs` row that has no rate in it.
3. The committed-files test lists `usdinr_fbil` as private and fails on a planted `usdinr_fbil.csv`, revision row or
   gap row in the repository.
4. No test fixture holds a real FBIL rate.
5. **Real run (rule 6; rule 8 after the merge):** the adopt of both copies, then the comparison, give equal row
   counts (1,981, plus any newer rows) and equal SHA-256 values. `global-cues check` with Drive prints FBIL's gaps as
   counts and the overlap as counts.
6. Gates: pytest, ruff, imports, code size. Quality rules 1-8. Rule 9 does not apply: no money path.

**Gap list (requirement -> where):**

| Requirement (source) | Where |
|---|---|
| FBIL's table in Drive, like the US closes (owner, 15 Oct) | scope 1, criterion 1 |
| only derived and hashed values in the repository (orchestrator) | scopes 2 and 4, criteria 2-3 |
| the removal in its own commit (orchestrator) | scope 4 |
| every reader downloads first (orchestrator) | scope 1: `build_tables`/`build_reader` already do; no other reader exists |
| past copies in git history (orchestrator) | known limits |
| the simplest design (owner, 15 Oct "keep the design simple") | one existing flag; no new class, option or path |

**Judge verifies:** the diff is the flag, the overlap columns, the removal, tests and docs; the committed-files test
fails on a planted FBIL file; the fixtures hold no real rate; after the merge, the adopt and comparison output.

**Depends:** A17, A17b · **Size:** S · **Status:** story text for the judge (quality rule 1); no code yet

---

## A9b. NSE downloads: one retry policy, and a named failure everywhere

**Repository:** trading

**Description:** As the data owner, I want every NSE download to retry what is worth retrying, stop politely on a
refusal, and end in a failure each command names, so that no dataset crashes with a traceback, waits into a longer
block, or skips a file silently.

**Context and why:** judge 100 (A15), open item: `fno/storage/raw_source.py:123` lets NSE's 403, 429 and 5xx out as
`requests.HTTPError` on the first answer, never retried and not as `RawSourceUnavailable`, the error
`RawFileSource.fetch` promises. `NseArchiveSource._response` is shared by A1, A8, A10, A11, A12, A14, A15, P6 and P8
(22 source classes, one of them on NSDL's host through the same code). Inventory of 15 Oct 2026 (builder, read-only):
- a 403/429/5xx is a traceback in `data-librarian`, `data-snapshot`, `data-revisions sweep`, `data-fingerprints
  --spot-check`, `market archive`, `market daily` (CRASHED), `market look-up`, `participant-oi watch` and
  `participant-oi sweep`;
- `participant-oi check-once` crashes before its UNREACHABLE alert is built, so #fno-desk hears nothing;
- `SourceCoolingOff` (the pacer's 15-minute pause after two refusals, `fno/http_pacing.py`) is a
  `RequestException`, so `_response` sleeps 5 + 15 + 45 s into a host that is cooling off, then gives up;
- `market`'s `_archive_revisions` (`fno/market_read_models/cli.py:137`) drops the sweep's unanswered paths: a silent
  skip;
- the VIX sweep's and the revision sweep's "no answer" lines do not say why (404, refusal or no connection);
- `research/data/participant_oi/README.md:54` says the sweep asks for headers only; the wired sweep
  (`RevisionCapturingSource`) reads every file in full.
No raw file is ever written partially today (bytes are complete and checked before any `put`); this stays so.

**Scope.** In:
1. **One retry policy in `NseArchiveSource._response`** (GET and HEAD alike), as named constants:

   | Answer | What the source does |
   |---|---|
   | 2xx | returns it: **unchanged**, one request, no wait |
   | 404 | `None` (not published): **unchanged** |
   | no connection, timeout, cut answer (a `RequestException` other than `SourceCoolingOff`) | retried |
   | 429, and every 5xx (500-599) | retried |
   | 403, and every other 4xx | **not retried**: raises `RawFileRefused` at once (retrying a refusal invites a longer block; the pacer already pauses a host after two refusals in a row) |
   | `SourceCoolingOff` from the session | **not retried**: raises `RawSourceUnavailable` at once, naming the cool-off |

   - At most 4 tries: waits of 5, 15 and 45 s before tries 2-4 (today's waits, kept).
   - `Retry-After` (seconds or an HTTP date) on a retried answer: the wait is the larger of the scheduled wait and
     `Retry-After`. Above `MAX_RETRY_AFTER_SECONDS` (120) the source stops at once with `RawSourceUnavailable` naming
     it, rather than block a run; the next scheduled run tries again. A malformed or past `Retry-After` is ignored.
     Why 120 (reasoning only; judge 119 minor 2): past two minutes NSE is blocking, not hiccuping; the pacer pauses
     the host for 15 minutes and the next scheduled run is the right retry.
   - With the pacer: a 429 counts as a refusal, so a second 429 in a row pauses the host and the next try stops at
     once as cooling off. A 429 therefore gets one retry in practice; a 5xx up to three.
   - Worst case per file: 65 s of waits, or 3 x 120 s with long `Retry-After` values, plus up to 4 request timeouts
     of 60 s. A12's `filings archive --max-minutes` checks its deadline before each file, so only the file in flight
     runs over (twice that for a truncated file's second download).
2. **One failure contract.** `fetch`, `fetch_published` and `last_written` of an NSE source return the bytes (or the
   time), `None` for 404, or raise `RawSourceUnavailable`; never `requests.HTTPError` or `SourceCoolingOff`.
   - New `RawFileRefused(RawSourceUnavailable)`: this one file was refused (403 or another 4xx). A subclass, so every
     caller that handles `RawSourceUnavailable` handles it too; a caller that can go on to the next file catches it
     first.
   - Both carry the HTTP status (or none) and the number of tries, and their message names the source, the path, the
     status or error, and the tries: e.g. `NSE archive: nse/indices/index-close/2026/10/ind_close_all_14102026.csv:
     HTTP 503 after 4 tries`.
3. **Every caller names a final failure** (table below): a named line and a non-zero exit, a recorded failure, or an
   alert; never a traceback, never a silent skip, never a partial or empty raw file.

   | Command or caller | On `RawSourceUnavailable` (incl. `RawFileRefused`) |
   |---|---|
   | `data-librarian <ds>` | `stopped: ...` line, exit 1, manifest rows committed (today's path, now reached) |
   | `data-snapshot <ds>` | `NOT archived: ...`, exit 1 (today's path) |
   | `data-revisions sweep` | each path listed `no answer` **with its reason**, exit 1 |
   | `data-fingerprints --spot-check` | **new**: one named line, exit 1, the manifest already written stays |
   | `market archive`, `market daily` | the problem line (`ARCHIVE_FAILED`, or `Stopped` with its alert), not CRASHED |
   | `market`'s revision step | **new**: every unanswered path is a problem line (today dropped); like any archive problem it stops that day's publication, since NSE's latest version cannot be confirmed (judge 49) |
   | `market look-up` | **new**: one named line, exit 1 |
   | `participant-oi watch`, `check-once`, `sweep` | the `unreachable` row and #fno-desk alert / `no answer` line (today's path, now reached for HTTP errors too) |
   | `vix-history fill`, `sweep` | `STOPPED (...)` line / `no answer` **with its reason**; the stale "not retried" comments go |
   | `filings archive` (A12) | `RawFileRefused`: a failure for that company, the run goes on (as an `HTTPError` is today); any other `RawSourceUnavailable`: the run stops naming the company (as today); the truncated-file second download alike |
   | `filings day-lists` | each list stops with its own named line; the next list still runs |
   | library consumers (quotes recorder, expiry and validity listings, settlement, panel daily files, participant-OI point in time, the capacity script) | receive `RawSourceUnavailable` instead of `HTTPError`; no caller anywhere catches `requests.HTTPError` from an NSE source after this story (a test checks the code) |
4. **Docs:** `docs/DATA_SOURCES.md` "Politeness" states the policy; `research/data/participant_oi/README.md:54`
   corrected (the sweep reads files in full through `RevisionCapturingSource`).

Out:
- `PublicData` (`fno/providers/public.py`: the option chain and the A12 filing indexes on www.nseindia.com/api) keeps
  its own three-attempt loop with cookie warm-up; it is not an `NseArchiveSource`. Bringing it under this policy is its
  own change (it needs the warm-up kept). Safe today (judge 119 minor 3) because its callers catch everything it
  raises: `NseLevelSource` records any failure, and A12's indexes make a list failure that company's failure and a
  cool-off a stop. A new caller must do the same until `PublicData` comes under this policy;
- `tools/nse_raw_download/nse_raw_download.py` (a one-off script, stops at the first 403/429 by design);
- the pacer's numbers (1 request a second a host, a 15-minute pause after two refusals: owner decision,
  `docs/DESK_DECISIONS.md:44`);
- non-NSE sources (the global cues have their own rules).

**Acceptance criteria:**
1. The policy, for every NSE source class (a test over all 22 `NseArchiveSource` subclasses, with a fake session; GET
   and HEAD):
   - 200 at once: the same bytes, one request, no sleep (unchanged);
   - 404: `None`, one request;
   - 503, 503, 200: the bytes, waits [5, 15]; 4 x 503: `RawSourceUnavailable` with status 503 and 4 tries, waits
     [5, 15, 45]; the same for 500, 502, 504 and a dropped connection;
   - 429 then 200: the bytes; 429 twice through the real pacer: the third try stops at once as cooling off;
   - 403 and 400: `RawFileRefused` after one request, no wait;
   - `SourceCoolingOff`: `RawSourceUnavailable` at once, no wait;
   - `Retry-After`: 30 waits 30 (over the scheduled 5); 3 waits 5; exactly 120 waits 120; 121 stops at once; an HTTP
     date; a malformed value and a past date use the scheduled wait.
2. No `requests.HTTPError` or `SourceCoolingOff` leaves an NSE source (tests above), and no code in `fno/` or
   `research/` catches `requests.HTTPError` around an NSE source's `fetch`, `fetch_published` or `last_written` (a
   test reads the code).
3. Every row of the caller table, tested end to end with a fake NSE answering 503 four times and with 403: the named
   line or recorded failure, the exit code, nothing saved for that file, and work done before it kept (manifest rows
   committed). `participant-oi check-once` sends its UNREACHABLE alert on a 503. `market`'s revision step names an
   unanswered path. `filings archive` goes on after a 403 on one company and stops on a cool-off. `filings day-lists`
   runs the second list after the first stops.
4. Successful downloads are unchanged: for every source, a 200 makes one request and returns the same bytes and
   `Last-Modified` time as before (the tests above); one real download through the new code matches its manifest
   SHA-256.
5. Docs: the policy in `docs/DATA_SOURCES.md`; the participant-OI README line corrected.
6. Quality rules 1-9:
   - rule 1: this text first, code after the judge's check;
   - rule 2: the gap list below;
   - rule 3: self-review by independent agents (correctness, silent failures);
   - rule 4: a broken-code proof per criterion;
   - rule 5: good, bad, boundary and empty cases (the boundaries are `Retry-After` 120/121, the fourth try, the second
     429; the empty case is an empty 200 body, which stays the dataset check's job and is never retried);
   - rule 6: real output: one real successful download, and each command's failure line from the end-to-end tests
     (labelled as test output: NSE cannot be made to fail on purpose);
   - rule 7: the orchestrator's check;
   - rule 8: after the merge, one real `data-librarian` run on a recent day;
   - rule 9: no money path, so no ChatGPT review (stated, not skipped).
   Code size, lint, imports and the full suite pass.

**Gap list (quality rule 2):**

| Requirement (source) | Where |
|---|---|
| 403/429/5xx raised as `HTTPError`, not `RawSourceUnavailable` (judge 100, `raw_source.py:123`) | scope 2, criteria 1-2 |
| no retry of 429/5xx (judge 100) | scope 1, criterion 1 |
| which statuses, how many tries, backoff, `Retry-After` (orchestrator, 15 Oct 2026) | scope 1, criterion 1 |
| what each caller does on a final failure: named, never silent, never a partial file (orchestrator) | scope 3, criterion 3 |
| cross-dataset tests (judge 100; orchestrator) | criterion 1 (all 22 classes), criterion 3 (every command) |
| no behaviour change for successful downloads (orchestrator) | criterion 4 |
| polite: one a second a host, pause after two refusals (owner, `docs/DESK_DECISIONS.md:44`) | kept (out: the pacer's numbers); scope 1: 403 not retried, a cool-off never waited into |
| `SourceCoolingOff` retried into a paused host (inventory) | scope 1-2, criterion 1 |
| `check-once` alert lost on an HTTP error (inventory) | scope 3, criterion 3 |
| `market` revision step drops unanswered paths (inventory) | scope 3, criterion 3 |
| "no answer" without a reason in the sweeps (inventory) | scope 3, criterion 3 |
| stale HEAD-only line in the participant-OI README (inventory) | scope 4, criterion 5 |
| `PublicData`'s own retry loop (inventory) | **out**: not an `NseArchiveSource`; needs its cookie warm-up |
| the download tool script (inventory) | **out**: one-off, stops on refusal by design |
| A8's release time is the answer's, with the check's start beside it (orchestrator's decision 37) | code round: `checked_at` is the answer time; `started_at` goes to the side log `release_check_starts.csv` |
| the A8 Claude routine commits `release_checks.csv` by path (judge 119 addendum 1; orchestrator's decision 49) | code round: the check log keeps its name and header, so the routine's rows are never lost; only its start times would be, since it does not commit the side log. **Owner item**: update the routine's prompt to commit `research/data/participant_oi/`, or retire it |

**Judge verifies:** plants 503s, a 403, a 429 with `Retry-After` and a cool-off against two datasets of its choice and
reads each command's line and exit code; checks no `HTTPError` escapes; confirms a successful download is byte- and
request-identical.

**Depends:** A1, A9, A11, A12, A15, P8 · **Size:** M · **Status:** story text passed (judge 119); code round for the
judge (response 119)
