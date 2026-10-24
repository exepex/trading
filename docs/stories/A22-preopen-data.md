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
     deadline `PREOPEN_RECEIPT_BY = time(9, 15)` (FL1's read; O8's owner, code review) and the receipt path pattern are A22's constants, imported by O8.
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
8. Witness: a planted trading day with no pre-open row gives O8's row `missed` from 09:15 and FL1's line "pre-open
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
| GIFT Nifty in the 08:50 morning edition (owner e70525ee4) | amendment 1: its own write-once file, pushed when the GIFT read ends |
| A missed early GIFT push noticed before 08:50 | amendment 1: FL1's "GIFT Nifty: missing" line; A22's alert at about 09:11 |

## Routine prompt (for the owner to create, 08:36 IST daily)

"Run the pre-open capture in CLAUDE.md, section 'Pre-open capture (story A22)'." (created for 08:36 IST so setup ends
by 08:40) The section: `sh tools/routine_setup.sh
--groww`, then `python -m fno preopen record`; commit and push only `receipts/` and `research/ops/capture_errors.csv`
(`git pull --no-rebase` first); if it prints "alert NOT sent", post its lines to #fno-desk with the Slack connector.

## Amendment 1: GIFT Nifty for the 08:50 morning edition (owner, 22 Oct 2026, DESK_DECISIONS e70525ee4)

The owner's morning edition posts by 08:50 IST, before the day row (pushed at about 09:11). As soon as the GIFT part
ends (fresh at 08:40, or after its last read at 08:44:59), A22 writes it in its own write-once file
`data/preopen/gift/YYYY/MM/<date>.csv` (the day row's GIFT cells with the date; a value only when `ok` or `late`) and
pushes the receipts at once, so the receipt is on GitHub by about 08:41-08:46. FL1 reads it through
`early_file("gift", day)` and `receipt_path(day, early_file("gift", day))`. A second run finds the file taken and
writes nothing; a failed save or push is a problem line in the run's one alert and an O10 row. That alert goes out
only at about 09:11, after the 08:50 edition, so the same-morning signal is FL1's: when the morning edition finds no
GIFT receipt for a trading day, it prints one line, "GIFT Nifty: missing", and posts without it (the contract FL1's
builder agreed for the day row, extended to this file; judge 445 minor 1). The day row is
unchanged (it still carries GIFT). N0, which needs the 09:09 pre-open price, goes in FL1's short 09:12 post instead.

Criteria: a good morning writes the GIFT file and pushes it at the GIFT part's end (08:40 on the injected clock),
before the pre-open window; a GIFT never fresh is written with its status, its reason and no value, pushed after
08:44:59; a failed push is named in the alert; a second run finds the file taken and pushes nothing.

## Open questions

1. Step 0b (first trading morning after the text PASS, 09:08-09:15 IST): do `key=NIFTY` / `key=BANKNIFTY` answer, and
   does Groww give BANKNIFTY's pre-open candle? The design keeps whichever answers; criterion 3 needs one.
2. The owner confirms the personal-research rule covers NSE's GIFT Nifty and pre-open pages (same as the US closes, 15
   Oct).

## Amendment 2 (A22d): the flat 09:15 candle is the live pre-open value (DR1 item 7, 24 Oct 2026)

**Lane:** 1 (Groww, the A22 routine's record). **Branch:** `story/a22d-flat-candle`. **Builder:**
session_012pfddFKS3kqy6dJQCJ3Z5i (A22's owner session 013u1Ac2 no longer exists). **Orchestrator:**
session_01Mt6dcBU5kp2htdPN2KmiZH. **Deadline:** on `main` before Mon 26 Oct 08:30 IST, the next live pre-open.

### The failure

23 Oct, the first live morning: "nifty incomplete / banknifty incomplete: no pre-open value: candles only from 09:15"
(O10 rows 12-13); the orchestrator's 24 Oct rehearsal (REH1c, the recorded answers replayed) gives the same. It will
fail every trading day: step 0b tested candles read from history (after the session), where 09:00-09:14 exist; read
live at 09:10, Groww serves none of them.

### Evidence (24 Oct, 19:40 IST; the archived raw answers through the verified Drive cache, A16's `ReadOnlyGroww` for history; differences only, no value) [strong, one session; rows marked * are the builder's
read of Groww's history, not replayable from the repository (no 23 Oct 1-minute archive); judge 589 reproduced the
others from Drive]

| Check, 23 Oct | NIFTY | BANKNIFTY |
|---|---|---|
| Live answer (`nifty_091059.json`, `banknifty_091101.json`): candles of the day | one, stamped 09:15 | one, stamped 09:15 |
| That candle: open = high = low = close; volume field | yes; `null` | yes; `null` |
| Its close minus NSE's official open (`ind_close_all`, Open Index Value) | 0.00 | 0.00 |
| Its close minus the 09:09 close Groww serves from history now * | 0.00 | 0.00 |
| The real 09:15 candle in history now: flat? its open minus the live candle's close * | no; 0.95 points | no; 14.65 points |

So before 09:15 Groww's one candle is a placeholder for the minute to come, holding the index's last value, which
from 09:08-09:09 to 09:15 is the pre-open result (step 0b: the close is final from the 09:08 or 09:09 candle on 21 of
21 sessions, and the 09:09 close is NSE's open on all of them). The real 09:15 candle replaces it later and differs.
Limits: one live session (22 Oct has no live answer: A22's first live morning was 23 Oct); only the last read of each
index (09:10:59) was archived, so the 09:10:00 and 09:10:30 answers are unseen; index candles carry `null` volume live
and in history, so "no volume" alone does not mark the placeholder. Hence the next-morning check below.

### The rule

`read_index_preopen` gets the read's `seen_at` (Groww's `received_at`, as today in `Answer`):
1. The day's 09:09 candle present: its close, as now (basis `candle_0909`). It always wins over rule 2.
2. Else, the value is the close of the day's 09:15 candle (basis `flat_0915`) only when all hold: it is the day's
   **only** candle; open = high = low = close; its volume is `null`, absent or 0; `seen_at` is from 09:10:00 (after the
   pre-open result is final, step 0b) and **before 09:15:00** (from 09:15 the candle may be a traded minute).
3. Anything else is not a value: a 09:15 candle read from 09:15:00, not flat, with a volume, or beside other candles
   of the day, or a candle stamped 09:14 (or any other minute), keeps today's outcomes ("no pre-open value: candles only
   from 09:15" or "no 09:09 candle yet", incomplete, retried to 09:10:59). No candle stays "no 09:09 candle yet".
   `source_time` of a `flat_0915` value is blank: the candle's 09:15 stamp is later than the read and is not the
   value's time; `seen_at` is.

The day row gains one column per index, `nifty_preopen_basis` and `banknifty_preopen_basis`: `candle_0909`,
`flat_0915_unverified` or `flat_0915_verified`, blank when there is no value. Nothing else in the row changes; the
receipt O8 reads and the GIFT file are untouched.

### How a wrong value is caught: the open check

- **When:** after `preopen record`'s own commits (about 09:11-09:12), as its last step on a trading day, so no Drive
  wait in it can move GIFT's 08:40 read (the 08:50 edition needs GIFT's receipt at about 08:41) or the 09:12 commit
  (judge 589 finding 1). Chosen over a hard stop before 08:40 because a stop between calls cannot bound one slow Drive
  call, and after the commit nothing waits on the check (no reader of the label until the next morning's row). It
  checks each of the last 10 sessions before today that has a day row with at least one index value and no check file
  yet; a row with no value (23 Oct's) is skipped. A day row written before A22d has no basis columns: its values are
  checked and its basis reads blank, so it never counts toward the label.
- **What:** each index's value against NSE's Open Index Value in that session's `ind_close_all`, read from the stores
  only (`build_stored_index_close_files`, never NSE, never a Drive write; A9's librarian archives it at 08:38 and
  through `index-closes.yml`). Match: at most one tick (0.05 points) apart, A16b's `beyond` (one rule, not a second).
  Its result goes write-once to Drive, `data/preopen/check/YYYY/MM/<date>.csv` (per index: basis, `match`, `mismatch`
  or `no value`, and the difference, in Drive only), with its receipt, committed by a second run of the run's own committers after the check. Its lines follow the
  capture's: "open check: <n> checked, <m> waiting for NSE's file", or "open check with problems: ..." with its own
  #fno-desk line (sent only then); either problem line makes the command exit 1.
- **No official file yet:** no check file is written; that session is checked again the next morning (a 10-session
  look-back covers a long weekend and a late archive). Never counted as a match.
- **Mismatch:** one problem line in the check's #fno-desk alert and one O10 row ("nifty open check mismatch:
  flat 09:15 candle differs from NSE's official open on <day>"; no value or difference in the alert or the repository).
  The day's row is not changed (write-once); its check file says `mismatch`.
- **Label, before 5 sessions are checked:** a `flat_0915` value is kept and labelled `flat_0915_unverified`, not
  blocked. Reason: blocking loses the only live pre-open value every day while the check can only run the next
  morning anyway; the evidence above is exact on the one live day and the mechanism matches 21 history sessions; the
  label lets FL1 (the only reader to come; it reads no pre-open value yet) show or skip it. A value is labelled
  `flat_0915_verified` when that index's 5 most recent checked `flat_0915` sessions are all `match`; any `mismatch`
  among them makes it `unverified` again (5 fresh matches needed). `candle_0909` values are checked too but are not
  part of the count. Today's label is set when the day row is written (09:11) from the check files already there, so
  it counts sessions up to the day before yesterday. Earliest `verified`: Tue 3 Nov's row (values of 26-30 Oct,
  the fifth checked on 2 Nov after that morning's row).

### Acceptance criteria (each with good, bad, boundary and empty cases; injected clock)

D1. Flat candle accepted: the 23 Oct shape (one flat 09:15 candle, `null` volume) read at 09:10:00, 09:10:59 and
    09:14:59 gives the value, basis `flat_0915`, blank `source_time`, status `ok`.
D2. Not accepted: read at 09:15:00 (boundary) and 09:16; read at 09:09:59 (boundary); a non-flat 09:15 candle read
    before 09:15; one with volume 1 (volume 0 is accepted); a flat 09:15 candle beside a 09:05 candle; a flat candle
    stamped 09:14; another day's flat 09:15 candle; no candle; an empty list. Each gives today's incomplete outcome,
    never a value.
D3. Precedence: an answer with the 09:09 candle and a flat 09:15 candle gives the 09:09 close, basis `candle_0909`.
D4. Day row: the two basis columns, filled as the rule says; blank for an index with no value; other columns
    unchanged (header test); a day row in the old header (23 Oct's, no basis columns) still reads.
D5. Open check: match at 0.00 and at 0.05 (boundary), mismatch at 0.06 and at -0.06; mismatch gives one alert line
    and one O10 row without a value; no official file writes no check file and is retried next morning; a session
    already checked is not checked again (write-once file taken); no day rows to check does nothing; an old-header row with a value is checked with a blank basis and does not
    count; a row with no value is skipped; the check reads
    only stored index-close files (a fake NSE that fails the test if called).
D6. Label: 4 matches then today gives `unverified`, 5 gives `verified`; 5 matches with a mismatch in the last 5
    gives `unverified`; no check file at all gives `unverified`.
D7. Timing: with a slow fake store (each check read takes 10 minutes on the injected clock) GIFT's first read is
    still at 08:40:00 and the capture's commit precedes the check; the check runs only after the capture's commits; a
    check failure (Drive down, unreadable file) is one problem line and exit 1, never a change to the capture's day
    row, files or commit.
D8. Real output sample in the Claims: the run's lines on the 23 Oct recorded answers through REH1c's rehearsal, and
    the first live morning's (26 Oct) lines.

### Gap list

| Requirement | Where |
|---|---|
| Accept the flat 09:15 candle read before 09:15 (DR1 item 7) | D1, D2 |
| Checked against `ind_close_all`'s open (DR1 item 7) | D5 |
| 5+ sessions before trusting; unverified rather than blocked (orchestrator) | D6 |
| Mismatch: what happens | D5 (alert, O10 row, check file, label reset in D6) |
| Cases: volume, non-flat after 09:15, no candle, 09:14 stamp (orchestrator) | D2 |
| No value in chat, alert or repository | D5, the record scan |
| Never delays the 09:12 commit | D7 |
| NSE's pre-open `key=NIFTY` as a second source (DR1 item 7: "possible") | Out: its layout is unverified (step 0: "No Data Found" in the evening; no morning read archived) and adding an unread source two days before the live morning adds a second unknown; the next-morning check already catches a wrong value. A later story may archive its raw answer for a layout probe |
| FL1 showing the label | Out: FL1 reads no pre-open value yet; its builder is told the column |

### Plants (builder's, each must fail a test)

1. Drop the flat test. 2. Drop `seen_at < 09:15`. 3. Drop the 09:10 lower bound. 4. Accept any volume. 5. Accept any
lone candle from 09:14. 6. Allow other candles beside it. 7. Prefer `flat_0915` over the 09:09 candle. 8. Count a
missing official file as a match. 9. Tolerance 0.10. 10. Label verified at 4 matches. 11. Ignore a mismatch in the
count. 12. Send the difference in the alert. 13. Check against NSE live instead of the stores. 14. Run the check before
the capture (at the start of `preopen record`).

### Claims (A22d)

None yet: code starts after the text PASS.
