# A22. Pre-open data for the 08:45 forecast: GIFT Nifty and NSE's pre-open auction

**Repository:** trading · **Lane:** 1 (new story; outside services NSE, Groww, Drive, Slack; a Claude routine) ·
**Branch:** `story/a22-preopen` · **Builder:** session_013u1Ac2N9eRQ8XCYPjwpaat · **Orchestrator:**
session_01VG1RqxLFUVdvvPuMRYZtDH · **Judge:** Judge F (session_01QLDqmpqUA7gAi7vcijnj5Y)

**Description:** As the forecaster and the F&O trader, I want the morning's first market signals, GIFT Nifty before
08:45 and NSE's pre-open auction result at 09:08, captured every trading day with the time they were seen, so the
08:45 and 09:30 forecasts (FL1) use what was knowable then and a failure is never silent.

**Context:** owner, 21 Oct 2026 (`docs/DESK_DECISIONS.md`): the engine forecasts NIFTY and BANKNIFTY at 08:45, 09:30
and 15:45; "Skip 08:45 until A22". GitHub starts this repository's crons 4-5 h late (judges 350, 351), so the capture
runs inside a Claude routine started at about 08:40 IST (the owner creates it from the prompt below).

## Step 0 (21 Oct 2026, 19:45 IST, from this container) [strong: direct reads]

| Data | Source | Read result | Terms |
|---|---|---|---|
| GIFT Nifty (NSE IX's NIFTY future) | NSE's homepage API `www.nseindia.com/api/NextApi/apiClient?functionName=getGiftNifty` (JSON, no cookie) | 200; `giftNifty`: last price, day change, contracts traded, expiry, `timestmp` "21-Oct-2026 19:46" (it trades into the night); also USDINR futures | NSE's terms page answers 403/404 to scripts, so the terms could not be read; NSE IX's site is a script page. Applied: the owner's 15 Oct personal-research rule (values in Drive only, never redistributed or shown publicly) [some] |
| Pre-open auction, F&O stocks | `www.nseindia.com/api/market-data-pre-open?key=FO` | 200, 213 stocks, each with IEP (equilibrium price), final quantity, previous close, `lastUpdateTime` 09:08:44 | as above |
| Pre-open, NIFTY 50 / BANKNIFTY constituents | `...market-data-pre-open?key=NIFTY` and `key=BANKNIFTY` | `{"data":[],"msg":"No Data Found"}` in the evening; whether they answer at 09:08 is **unknown until a morning read** | as above |
| Index pre-open result (NIFTY, BANKNIFTY) | Groww 1-minute index candles (A16b's read-only adapter): the close of the last pre-open candle is NSE's official open (A16 amendment 3, judged) | proven for NIFTY on 114 sessions (A16b); BANKNIFTY to be checked in step 0b | Groww: the owner's paid subscription, read-only; values in Drive only (owner decision) |
| Asia opens (Nikkei 225, KOSPI, Hang Seng) | none free and official in real time | not built | **Out:** JPX/KRX/HKEX real-time feeds are paid; delayed pages are scraping without a clear licence [reasoning] |

## Scope

In:
1. `python -m fno preopen record` (one command, run by the routine), on a trading day of NSE's calendar (A7;
   otherwise "not a trading day", exit 0):
   - **08:40-08:44 IST, GIFT Nifty:** one read, kept with our `seen_at` and NSE's `timestmp`. Stale when NSE's time
     is more than 15 minutes before `seen_at` or not today (GIFT Nifty trades from 06:30 IST).
   - **09:08:30-09:14 IST, pre-open:** NSE's `key=FO` list (and `key=NIFTY`, `key=BANKNIFTY` if they answer), and the
     Groww 1-minute candles 09:00-09:08 of NIFTY and BANKNIFTY; retried each minute until 09:14. Complete when NSE's
     `lastUpdateTime` is today's and the Groww index candles hold a pre-open close.
2. Storage: every raw answer write-once in Drive (`data/preopen/raw/...`, O9 `DataStore`), one derived row per day
   (`data/preopen/day/...`, O9 `PartTable`: GIFT Nifty level and time, NIFTY and BANKNIFTY pre-open closes, the
   number of F&O stocks with an IEP, `seen_at` of each); receipts committed. No value enters the repository.
3. Failures: one #fno-desk line per run naming every problem (`AlertSender` via `StepOutputAlerts` pattern), and one
   row per problem in O10's `research/ops/capture_errors.csv` (`python -m fno health record-error`, O10's writer for
   routines), committed by the run.
4. The routine prompt for the owner (below) and the CLAUDE.md section for it.

Out: Asia opens (above); using the values in a forecast (FL1's job: the 08:45 forecast can use only GIFT Nifty, since
NSE's auction ends at 09:08; the 09:30 forecast can use both); historical back-fill of GIFT Nifty (no free source).

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
3. Index pre-open: Groww candles with a 09:07 or 09:08 pre-open close give it; candles only from 09:15 are
   "no pre-open value" (A16's rule); BANKNIFTY proven in step 0b.
4. Windows: before 08:40 the GIFT read waits; after 08:44 it is "late" (alerted, still recorded with its time); the
   pre-open part retries until 09:14 and then reports incomplete; a non-trading day does nothing.
5. Storage and records: raw answers and the day row go to Drive with receipts; no value in the repository (test of
   the committed paths); each problem gives one O10 row and the run sends one alert.
6. The routine prompt and its CLAUDE.md section exist; the command runs end to end against fixtures in a test.
7. Real output sample: the first two live mornings' lines in the claims file.

## Gap list

| Requirement | Where |
|---|---|
| GIFT Nifty level and time (owner, 21 Oct) | criteria 1, 4 |
| NSE pre-open equilibrium for NIFTY, BANKNIFTY or constituents | criteria 2, 3 |
| Asia opens if cheap | Out (no free official real-time source) |
| Check every source's terms | Step 0 table; NSE's terms unreadable by script, stated |
| Inside a Claude routine about 08:40 IST | scope 4, criterion 6 |
| Failures alert and go to O10's capture_errors | criterion 5 |
| Point in time (`seen_at`), raw in Drive (O9) | criteria 4, 5 |

## Routine prompt (for the owner to create, 08:38 IST daily)

"Run the pre-open capture in CLAUDE.md, section 'Pre-open capture (story A22)'." The section: `sh tools/routine_setup.sh
--groww`, then `python -m fno preopen record`; commit and push only `receipts/` and `research/ops/capture_errors.csv`
(`git pull --no-rebase` first); if it prints "alert NOT sent", post its lines to #fno-desk with the Slack connector.

## Open questions

1. Step 0b (first trading morning after the text PASS, 09:08-09:15 IST): do `key=NIFTY` / `key=BANKNIFTY` answer, and
   does Groww give BANKNIFTY's pre-open candle? The design keeps whichever answers; criterion 3 needs one.
2. The owner confirms the personal-research rule covers NSE's GIFT Nifty and pre-open pages (same as the US closes, 15
   Oct).
