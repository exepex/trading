# A22. Pre-open data for the 08:45 forecast: GIFT Nifty and NSE's pre-open auction

**Repository:** trading · **Lane:** 1 (new story; outside services NSE, Groww, Drive, Slack; a Claude routine) ·
**Branch:** `story/a22-preopen` · **Builder:** session_013u1Ac2N9eRQ8XCYPjwpaat · **Orchestrator:**
session_01VG1RqxLFUVdvvPuMRYZtDH · **Judge:** Judge F (session_01QLDqmpqUA7gAi7vcijnj5Y)

**Description:** As the forecaster and the F&O trader, I want the morning's first market signals, GIFT Nifty before
08:45 and NSE's pre-open auction result at 09:08, captured every trading day with the time they were seen and
committed by 09:12 IST, so the 09:15 forecast (FL1; owner, 21 Oct: a 09:15 pre-open report) uses what was knowable
then and a failure, including a routine that never starts, is never silent.

**Context:** owner, 21 Oct 2026 (`docs/DESK_DECISIONS.md`): the engine forecasts NIFTY and BANKNIFTY at 08:45, 09:30
and 15:45; "Skip 08:45 until A22". GitHub starts this repository's crons 4-5 h late (judges 350, 351), so the capture
runs inside a Claude routine started at 08:36 IST (the owner creates it from the prompt below).

## Step 0 (21 Oct 2026, 19:45 IST, from this container) [strong: direct reads]

| Data | Source | Read result | Terms |
|---|---|---|---|
| GIFT Nifty (NSE IX's NIFTY future) | NSE's homepage API `www.nseindia.com/api/NextApi/apiClient?functionName=getGiftNifty` (JSON, no cookie) | 200; `giftNifty`: last price, day change, contracts traded, expiry, `timestmp` "21-Oct-2026 19:46" (it trades into the night); also USDINR futures | NSE's terms page answers 403/404 to scripts, so the terms could not be read; NSE IX's site is a script page. Applied: the owner's 15 Oct personal-research rule (values in Drive only, never redistributed or shown publicly) [some] |
| Pre-open auction, F&O stocks | `www.nseindia.com/api/market-data-pre-open?key=FO` | 200, 213 stocks, each with IEP (equilibrium price), final quantity, previous close, `lastUpdateTime` 09:08:44 | as above |
| Pre-open, NIFTY 50 / BANKNIFTY constituents | `...market-data-pre-open?key=NIFTY` and `key=BANKNIFTY` | `{"data":[],"msg":"No Data Found"}` in the evening; whether they answer at 09:08 is **unknown until a morning read** | as above |
| Index pre-open result (NIFTY, BANKNIFTY) | Groww 1-minute index candles (A16b's read-only adapter): the close of the last pre-open candle is NSE's official open (A16 amendment 3, judged) | proven for NIFTY on 114 sessions (A16b); BANKNIFTY to be checked in step 0b | Groww: the owner's paid subscription, read-only; values in Drive only (owner decision) |
| Asia opens (Nikkei 225, KOSPI, Hang Seng) | A17e (the A17 builder's story: every non-Indian index) | not A22 | **A17e, not A22** (agreed 21 Oct). If A17e finds a legal pre-09:15 Asian level, A17e owns the code and data and may propose a command for A22's routine to call; no second Asian reader |

## Step 0b (22 Oct 2026, 02:40 IST, Groww read-only, A16's `ReadOnlyGroww`; differences and times only) [strong]

- NIFTY and BANKNIFTY 1-minute index candles exist for 09:00-09:14 on every regular session checked.
- Over the 21 regular sessions 21 Sep-21 Oct 2026, the close stays at its final pre-open value from the 09:08 candle
  (10 sessions) or the 09:09 candle (11), identically for both indices; never later.
- On all 21 sessions, for both indices, **the 09:09 candle's close equals NSE's official open** (`ind_close_all`'s
  Open Index Value) exactly (largest difference 0.00 points).
- So the index pre-open value is the close of the 09:09 one-minute candle, complete at 09:10:00. Still unknown until a
  live morning: how soon after 09:10:00 Groww serves that candle (the window allows retries to 09:10:59). NSE's
  `key=NIFTY`/`key=BANKNIFTY` lists are kept only if they answer at 09:08 (not needed for criterion 3).

## Scope

In:
1. `python -m fno preopen record` (one command, run by the routine), on a **trading day** (`is_trading_day`: regular
   or special session; a muhurat-only day, weekend or holiday prints "not a trading day", exit 0):
   - **GIFT Nifty, window 08:40:00-08:44:59 IST:** read, and retried every 30 s inside the window until fresh; kept
     with our `seen_at` and NSE's `timestmp`. Fresh when NSE's time is today's and at most 15 minutes before
     `seen_at` (GIFT Nifty trades from 06:30 IST). A run started after 08:44:59 still reads it once and records it as
     `late` (alerted); before 08:40:00 it waits.
   - **Pre-open, window 09:08:30-09:10:59 IST:** NSE's `key=FO` list (and `key=NIFTY`, `key=BANKNIFTY` if they
     answer) from 09:08:30, and the Groww 1-minute candles 09:00-09:09 of NIFTY and BANKNIFTY from 09:10:00 (the 09:09
     candle's close is the pre-open value: step 0b); retried every 30 s inside the window. Complete when NSE's
     `lastUpdateTime` is today's and both indices' 09:09 candles are present.
   - **Commit by 09:12 IST:** the run writes Drive, commits its receipts and error rows and pushes at 09:11 at the
     latest, so the 09:15 forecast reads them.
2. Storage: every raw answer write-once in Drive (`data/preopen/raw/...`, O9 `DataStore`), one derived row per day
   under one fixed, write-once name `data/preopen/day/YYYY/MM/<date>.csv` (GIFT Nifty level and time, NIFTY and
   BANKNIFTY pre-open closes, the number of F&O stocks with an IEP, `seen_at` and status of each); a second run the
   same day finds the name taken and writes nothing, so a late run never hides an on-time one; receipts committed.
   No value enters the repository.
3. Failures: one #fno-desk line per run naming every problem (`AlertSender` via `StepOutputAlerts` pattern), and one
   row per problem in O10's `research/ops/capture_errors.csv` (`python -m fno health record-error`, O10's writer for
   routines), committed by the run.
4. The routine prompt for the owner (below) and the CLAUDE.md section for it.
5. **A witness for a routine that never starts** (judge 407 SF1; A16's 09:00 routine missed its first fire on 16
   Oct, 1 of 3 sessions):
   - O8 (agreed with its owner, session_012eM7Ti, 21 Oct; it reviews the `fno/health/` diff before the judge): a new
     `fno/health/preopen_checks.py` behind `SessionCheck`, one `Expectation` row (`RECORDED_SESSION_KINDS`,
     `live_from` None until the first live day, set in a separate commit). Status from the receipt's **push time**
     (`Evidence.file_pushed_at`), never its self-written time; unknown push time is `unknown`, never `ok`; the
     deadline `PREOPEN_RECEIPT_BY = time(9, 20)` and the receipt path pattern are A22's constants, imported by O8.
     O8 runs at 17:51 IST, so it names a missed morning that evening.
   - The same-morning alarm is FL1's 09:15 report line "pre-open data: missing" when today's row is absent (agreed
     with FL1's builder; FL1-2 is not built yet).
   - The measured miss rate of the first live week is reported in the claims file.

Out: Asia opens and every foreign index close (A17e, the A17 builder's; GIFT Nifty and pre-open are A22's); using the
values in a forecast (FL1's job: the 09:15 forecast can use both); historical back-fill of GIFT Nifty (no free source).

## Design

- `fno/preopen/`: port `PreopenSource` with adapters `NseGiftNifty`, `NsePreopenList` (NSE's JSON, behind the shared
  polite session) and `GrowwIndexPreopen` (A16b's `GrowwCandleSource`, read-only allow-list reused, not copied);
  a `PreopenRun` that waits for each window (injected clock, A16's checked clock), retries, and returns one result per
  part; `fno/preopen/wiring.py` the composition root; the CLI wires the alert and O10's error writer.
- Pure readers raise on any answer not in its layout; "no data" is never "complete".

## Acceptance criteria (each with good, bad, boundary and empty cases)

1. GIFT Nifty: a fixture of today's real answer gives level, NSE time and contracts; a time 15 minutes old is fine,
   16 stale; yesterday's time stale; a missing `giftNifty` or a non-JSON answer fails.
2. Pre-open list: today's real `key=FO` answer gives 213 IEPs; a `lastUpdateTime` of another day is incomplete; an
   empty `data` (as `key=NIFTY` answers in the evening) is incomplete, never complete.
3. Index pre-open: the close of the 09:09 one-minute candle (fixture cut from a real answer; step 0b: equal to NSE's
   official open on 21 of 21 sessions for both indices); a day whose candles stop before 09:09 is "incomplete"
   until 09:10:59; candles only from 09:15 are "no pre-open value" (A16's rule).
4. Windows, exact boundaries (injected clock): GIFT at 08:39:59 waits, at 08:40:00 reads, at 08:44:59 is in the
   window, at 08:45:00 is `late`; pre-open at 09:08:29 waits, at 09:08:30 reads, at 09:10:59 retries, at 09:11:00
   stops and reports incomplete; the commit is done by 09:12:00; a GIFT answer stale at the first read and fresh at
   a retry is fresh; a weekend, a holiday and a muhurat-only day do nothing.
5. Storage and records: raw answers and the day row go to Drive with receipts; no value in the repository (test of
   the committed paths); each problem gives one O10 row and the run sends one alert.
6. The routine prompt and its CLAUDE.md section exist; the command runs end to end against fixtures in a test.
7. Real output sample: the first two live mornings' lines in the claims file.
8. Witness: a planted trading day with no pre-open row gives O8's row `missed` after 09:20 and FL1's line "pre-open
   data: missing"; a holiday gives neither; the first live week's miss rate (routine fires missed / trading days) is in
   the claims file.

## Gap list

| Requirement | Where |
|---|---|
| GIFT Nifty level and time (owner, 21 Oct) | criteria 1, 4 |
| NSE pre-open equilibrium for NIFTY, BANKNIFTY or constituents | criteria 2, 3 |
| Asia opens if cheap | Out (no free official real-time source) |
| Check every source's terms | Step 0 table; NSE's terms unreadable by script, stated |
| Inside a Claude routine about 08:40 IST | scope 4, criterion 6 |
| Failures alert and go to O10's capture_errors | criterion 5 |
| A routine that never starts is noticed (judge 407 SF1) | scope 5, criterion 8 |
| Committed by about 09:12 IST for the 09:15 report (owner, 21 Oct) | scope 1, criterion 4 |
| Boundary with A17e (foreign index closes) | Out: foreign closes and USD/INR are A17/A17e's (agreed with its builder) |
| Point in time (`seen_at`), raw in Drive (O9) | criteria 4, 5 |

## Routine prompt (for the owner to create, 08:36 IST daily)

"Run the pre-open capture in CLAUDE.md, section 'Pre-open capture (story A22)'." (created for 08:36 IST so setup ends
by 08:40) The section: `sh tools/routine_setup.sh
--groww`, then `python -m fno preopen record`; commit and push only `receipts/` and `research/ops/capture_errors.csv`
(`git pull --no-rebase` first); if it prints "alert NOT sent", post its lines to #fno-desk with the Slack connector.

## Open questions

1. Step 0b (first trading morning after the text PASS, 09:08-09:15 IST): do `key=NIFTY` / `key=BANKNIFTY` answer, and
   does Groww give BANKNIFTY's pre-open candle? The design keeps whichever answers; criterion 3 needs one.
2. The owner confirms the personal-research rule covers NSE's GIFT Nifty and pre-open pages (same as the US closes, 15
   Oct).
