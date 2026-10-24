# Story A17e: global markets beyond the US

**Repository:** trading · **Lane:** 1 (outside services, Drive, a schedule) · **Size:** M · **Builder:** A16b/A17
builder (session 01MBnbVU) · **Judge:** F · **Claims:** response 297

**Description:** As the macro economist and the risk manager, I want the closes of the markets that move India before
09:15 IST, and their levels shortly before the open, each with its first-seen time, so that the weather, the 08:45
forecast and GR1 stop reading the US alone (owner, 21 Oct 2026: "US market is not the only reason. Before the Indian
market opens, there is Australian market, Singapore, Hong Kong, Japan, South Korea, probably China too ... we fetch
data for each and every market that can affect the overall market in India ... don't consume US data only").

**Data rule (owner, 21 Oct, DESK_DECISIONS 50a79a43):** a source's redistribution or reproduction terms no longer
block a download for the owner's private research; pick the best source. Kept: (1) the data lives in private Drive
only, never in this public repository or a public place, and Slack shows derived facts only; (2) no getting around
logins, paywalls, CAPTCHAs or technical blocks, no false identity; (3) paced, polite downloads.

**Boundary (agreed with the A22 builder, 013u1Ac2, 21 Oct; written into A22's story):** A22 owns GIFT Nifty and NSE's
pre-open; A17/A17e own every foreign index and the other global cues. A17e's pre-open Asian levels (part B) run as a
command that A22's 08:36 routine calls between its two windows (08:50-09:05 IST); no second reader, no second routine.

## Step 0: sources tested (21 Oct 2026, 21:05-21:40 UTC)

Three research passes fetched every candidate and read its terms (the terms are recorded for the owner, no longer a
blocker); the key results were re-run by me. "Official" = the index owner or its exchange.

**Official sources that answer without a login (tested):**

| Index | Official source | History it gives |
|---|---|---|
| SSE Composite | CSIndex `csindex-home/perf/index-perf?indexCode=000001` (JSON) | 2019-01-01 to 2026-10-21, 1,891 rows |
| TAIEX | TWSE OpenAPI `indicesReport/MI_5MINS_HIST` | current month only |
| Nikkei 225 | Nikkei Indexes `nkave/historical/nikkei_stock_average_daily_en.csv` | 2023-01-04 to 2026-10-21 |
| VIX | Cboe `delayed_quotes/charts/historical/_VIX.json` (A17's SPX parser) | 1990-01-02 to 2026-10-20 |
| Euro Stoxx 50, DAX | STOXX `HistoricalData/h_3msx5e.txt`, `h_3mdax.txt` (needs SSL.com's public intermediate certificate: STOXX's chain is incomplete; this completes TLS, it bypasses nothing) | rolling 3 months |
| KOSPI | KRX Open API (free key, 1 year) | key needed: not usable until the owner registers |
| Hang Seng, ASX 200, Straits Times, FTSE 100 | none without a login or a bot wall (hsi.com.hk 404, ASX header JSON has no history, SGX chart data duplicated and holiday-filled, LSEG pages script-only) | - |

**One source for all eleven (tested):** Yahoo Finance's public chart API
(`query1.finance.yahoo.com/v8/finance/chart/<symbol>`, no login, cookie or CAPTCHA): daily rows from 2019 to
2026-10-21 for ^N225 (1,900), ^KS11 (1,912), ^AXJO (1,978), ^HSI (1,919), 000001.SS (1,888), ^STI (1,962), ^TWII
(1,892), ^FTSE (1,972), ^GDAXI (1,985), ^STOXX50E (1,962) and ^VIX (2,036), each with its exchange's time zone; and
5-minute intraday levels with timestamps (^N225 on 21 Oct: 79 points from 05:30 IST).

**Is Yahoo right? Checked against the official files (strong):** Nikkei 225 equal on all 927 common days; SSE
Composite equal on all 1,887 common days, but Yahoo **lacks three real sessions** (2019-04-29, 2019-04-30 and the
newest day at test time); VIX equal on 1,960 of 1,963 days, **one large error** (2026-02-06: Yahoo 20.37, Cboe
17.76). So Yahoo is good but not clean: it is the source of last resort, never preferred over an official file.

**Pre-09:15 Asian levels:** the official live feeds are behind logins or bot walls, or have no public endpoint (TWSE's
MIS feed answers, but its terms bar automation; now recorded, not blocking). Yahoo's 5-minute chart gives every Asian
index that is open at 08:50 IST (Nikkei, KOSPI, ASX 200 and TAIEX from 05:30-06:30 IST; Hang Seng, SSE and STI from
06:30-07:00 IST). Its delay is not stated; part B measures it.

## Scope

**Part A, daily closes (one cue per index and publisher, A17's pattern; each a `GlobalCueSource` and one line in
`fno/global_cues/wiring.py`):**
1. Official cues: `sse_composite` (CSIndex, back-fill from 2019), `taiex` (TWSE OpenAPI, from the first run),
   `nikkei225` (Nikkei CSV, from 2023), `vix_us` (Cboe, from 2019), `eurostoxx50` and `dax` (STOXX 3-month files,
   from the first run), `kospi` (KRX, only once `FNO_KRX_API_KEY` exists; until then the run line says
   "kospi: not configured" and the run is not failed for it).
2. Yahoo cues, one per index, all eleven, back-filled from 2019 (`<index>_yahoo`): the history before each official
   file starts, and the only source for Hang Seng, ASX 200, Straits Times and FTSE 100. Amendment 1 (response 298):
   a twelfth, `nasdaq100_yahoo` (^NDX), because Nasdaq's own API publishes the close too late for the 03:41 run (the
   Nasdaq-100 was one US trading day late on every weekday morning, 17-21 Oct); A17's `nasdaq100` reading then takes
   Yahoo's value until Nasdaq has the date. One class
   `YahooChartSource(cue, symbol)`; dates in the exchange's own time zone from the answer's `exchangeTimezoneName`.
   **A block is a stop, never a puzzle (rule 2 of 50a79a43):** an answer of HTTP 401, 403 or 429, a consent or
   "crumb" page, or a CAPTCHA page stops that Yahoo cue for the run, writes nothing, and is named in the run's one
   alert line. The source never retries it with a cookie, a crumb, another user agent or another address; the next
   scheduled run tries once again, the same plain way. Hang Seng, ASX 200, Straits Times and FTSE 100, which have no
   official file to check against, are labelled `unverified (Yahoo only)` in every reading and check line.
3. One reading per index (A17b's `CueReader`): the official value where it has the date, the Yahoo value otherwise,
   with its publisher named in the reading. An official/Yahoo pair is compared in the checks, like A17d's RBI and
   FBIL overlap: a difference over 0.1 percent, or a session in one and not the other, is listed (counts only in the
   repository).
4. Point in time: each value's `first_seen_at` is its copy's fetch time; `available_at` is the market's close plus its
   publication lag; the as-of label at 09:15 and 15:00 IST. A same-day Asian close is never `live` at 09:15 (its
   session is still running); for the 09:15 open only the previous day's Asian and European closes count.
5. Private: every index value in Drive only (A17d's private flag and `DrivePartsRowLog`); the repository gets snapshot
   log rows (fetch time, path, SHA-256) and dates. Downloads paced (A17's `PacedSession`), Yahoo one request per
   index per run.
6. Schedule: inside the existing `global-cues.yml` runs (03:41, 04:41, 14:11 IST); every close of day d (Asia by
   10:40-14:30 IST, Europe by 22:10 IST) is in the 03:41 run of d+1, which lands 05:30-06:40 IST (measured 17-21 Oct).
   Same-day Asian closes for the 15:45 report: the 14:11 cron could hold them (Asia closes 10:40-14:30 IST), but
   GitHub started it 3 h 42 to 7 h 09 late on 17-21 Oct (17:54-21:21 IST), so it would miss 15:45 on every measured
   day. A call from the on-time daily desk run would serve it; whether the 15:45 report uses same-day Asian closes is
   FL1's decision, so that call is Out here and added when FL1 asks.

**Part B, pre-open Asian levels:**
7. `python -m fno global-cues preopen`: one Yahoo 5-minute read per open Asian index at A22's 08:50-09:05 slot; keeps
   the raw answer in Drive with `seen_at`, and a row (index, level time, level, the previous official close) in the
   private table. A level older than 20 minutes at `seen_at` is marked `stale`.
8. A22's routine calls it (one line in A22's CLAUDE.md section, agreed with its builder); a failure is one #fno-desk
   line and an O10 `capture_errors.csv` row (outside `daily run`).
9. Delay measured: for the first five sessions, each 09:00 IST level is compared with the same index's 5-minute
   official intraday where one is public (TWSE's MIS answer, read once by hand for the comparison only) and the lag is
   reported.

Out: GIFT Nifty and NSE's pre-open (A22); paid data feeds; FTSE 100 and Euro intraday (closed before 09:15); using the
values in any forecast (FL1, M1 and GR1 decide that).

## Acceptance criteria
1. Each source parses a saved real answer (one fixture per publisher) and refuses an error page, an empty answer and a
   changed layout with a named `ValueError`. CSIndex's fake start-date row (copied from the next session when the
   start date is a holiday; seen on 2019-01-01, and on 2026-10-01, which copies 8 Oct's 3811.9) never enters a table:
   every CSIndex request starts ten days before the first date wanted and every row before that date is dropped, so
   the request's first row is never kept, whatever its values (no equality guess: a real flat close two days running
   is kept; tests with a planted flat close and a planted holiday start).
2. Yahoo dates: the date is the exchange's own (a 00:00 UTC timestamp of a Tokyo session is that Tokyo date, and a
   timestamp one second before midnight local stays on its day); no weekend rows; a date given twice in one answer is
   left out and listed in the checks, never guessed (one ASX duplicate seen in the 2019 back-fill); a row with a null
   close is skipped; an answer with no timestamps is refused with a named `ValueError`.
3. The reading prefers the official value (amendment 1: the `nasdaq100` reading at 09:15 is Yahoo's previous close
   when Nasdaq's copy lacks it, Nasdaq's once it has it; tested with the 20-21 Oct copies); the overlap check lists the 2026-02-06 VIX difference and the two missing
   2019 SSE sessions when run on the real back-fill (cited in the claims).
4. `available_at` per market, tested at, one minute before and one minute after each boundary (IST): Shanghai 15:00
   Beijing = 12:30, Taipei 13:30 = 11:00, Seoul and Tokyo 15:30 = 12:00, Hong Kong 16:10 (after the closing auction)
   = 13:40, Singapore 17:00 = 14:30, Sydney 16:10 = 10:40 in Australian summer time and 11:40 in winter (both 2026
   clock changes tested: 5 Apr and 4 Oct), London 16:35, Frankfurt 17:35 and the Euro Stoxx 50 final value 17:50 in
   local time across both European clock changes (29 Mar and 25 Oct 2026). A same-day Asian close is never `live` at
   09:15 IST; the previous day's is. Empty case: a date with no row gives no label (missing, never stale).
5. Private: no index value or price-sized number in any repository file (A16b's scan pattern over every file the run
   writes).
6. KOSPI without a key: one "not configured" line, no failure; with a key, the key never appears in output or files
   (planted-key test).
7. Part B: a planted 5-minute answer gives the level and its time; a level exactly 20:00 minutes old at `seen_at` is
   not stale, one 20:01 old is `stale`; the command exits 0 on a
   closed market day (Asian holiday) with "market closed" for that index.
8. Blocks (rule 2): a planted 401, a planted 403, a planted 429, a planted consent page (HTTP 200 with Yahoo's
   consent form) and a planted CAPTCHA page each stop that cue with one named line, write nothing, and make exactly
   one request (the fake session counts requests: no retry, no cookie or header change); the other cues of the run
   still run. Readings of the four Yahoo-only indexes carry `unverified (Yahoo only)`.
9. The 2019 back-fills run once by hand into Drive; counts, first and last dates, and the overlap check's findings in
   the claims file; `global-cues verify` passes. The first scheduled run and the first part B read are cited.
10. Gates pass; no file or class over 350 lines; composition only in `fno/global_cues/wiring.py`.

## Gap list (quality rule 2)

| Requirement (owner, orchestrator, design rules) | Where |
|---|---|
| Australia (ASX 200) | scope 2 (Yahoo; no official source without a login); criterion 4 (10:40 / 11:40 IST boundary) |
| Singapore (Straits Times) | scope 2 (Yahoo); SGX's own chart data is Out (duplicated and holiday-filled, tested) |
| Hong Kong (Hang Seng) | scope 2 (Yahoo; no official source without a login or bot wall), labelled unverified; criterion 8 |
| Japan (Nikkei 225) | scope 1 (Nikkei, from 2023) and 2 (Yahoo, from 2019); criterion 3 (overlap) |
| South Korea (KOSPI) | scope 2 (Yahoo); scope 1 once the owner's KRX key exists; criterion 6 |
| China (SSE Composite) | scope 1 (CSIndex) and 2; criteria 1 and 3 |
| Taiwan (TAIEX) | scope 1 (TWSE, from the first run) and 2 |
| Europe (FTSE 100, DAX, Euro Stoxx 50) | scope 1 (STOXX: DAX, Euro Stoxx 50) and 2 (Yahoo: all three); criterion 4 |
| VIX | scope 1 (Cboe) and 2; criterion 3 (the 2026-02-06 difference) |
| A pre-09:15 level where possible | part B, scope 7-9; criterion 7 |
| Back-fill to 2019 | scope 1-2; criterion 9 |
| First-seen time (A17's point-in-time rule) | scope 4; criterion 4 |
| Private Drive only, never in this repository or a public place (50a79a43) | scope 5; criterion 5 |
| No getting around logins, paywalls, CAPTCHAs or blocks; no false identity | scope 2 (a block is a stop, never retried); criterion 8; Step 0 (only sources answering without a login); STOXX's certificate note; Out: Nikkei's bot-walled live page |
| Paced, polite | scope 5 (`PacedSession`, one request per index per run) |
| O9: data in Drive, receipts in GitHub | scope 5 (snapshot log rows with SHA-256) |
| A22 boundary | the Boundary paragraph; part B scope 8 |
| Failures alert and are recorded (owner, 16 Oct) | scope 6 (A17's run line and alert, O10's capture-watch on global-cues.yml); part B scope 8 |
| Quality rule 5 (good, bad, boundary, empty) | criteria 1, 2, 4, 6, 7 and 8 each name all four |
| Quality rule 6 (real output sample) | criterion 9: back-fill and first-run lines, counts and dates only (values private) |
| Quality rule 8 (end-to-end run after merge) | criterion 9: the first scheduled run and the first part B read, cited |
| Same-day Asian closes for the 15:45 report | Out (FL1 decides); scope 6 says why the 14:11 cron cannot serve it |
| Using the values in a forecast | Out (FL1, M1, GR1) |

## For the owner (no decision needed to start; each is a choice to improve the data)
- **KOSPI official:** register a free KRX Open API key (openapi.krx.co.kr) and add `FNO_KRX_API_KEY`; Yahoo serves
  KOSPI until then.
- **TAIEX and Nikkei official history to 2019:** official files reach only 2023 (Nikkei) and the current month (TWSE);
  Yahoo fills it, and it matched Nikkei exactly where both exist.
- Yahoo is not an official source: the overlap check is our only guard where no official file exists (Hang Seng,
  ASX 200, Straits Times, FTSE 100).

**Known limits:** Yahoo's delay for intraday Asian levels is unstated (part B measures it); its daily rows have rare
errors and gaps (two found in 1,963 and 1,891 days); European indexes have only 3 months of official history.

**Depends:** A17 (merged), A17d (private cues), O9 (receipts), A22 (the routine part B joins) · **Status:** story
text for judge F.

## Amendment 2 (21 Oct 2026, with the code; for judge F)
1. **Fixtures are made up.** Criterion 1's "saved real answer" would put real index values in this public repository,
   which criterion 5 and rule 50a79a43 forbid. So each test fixture copies its publisher's real layout with made-up
   levels (`tests/global_cues/world_fakes.py`). The parsers were run on the real answers in a dry run, which the
   claims file cites.
2. **KOSPI's official source (KRX) is deferred.** Its answer cannot be seen without the owner's key, so a parser
   written now would be a guess. `kospi_yahoo` serves KOSPI meanwhile. Criterion 6 moves to the story that adds KRX
   once a key exists.
3. **The Nasdaq-100 reading (amendment 1)** is A17e's `IndexReader` (`build_index_reader`), which prefers Nasdaq's own
   value and reads Yahoo's when Nasdaq's copy lacks the date. The weather (M1) reads the `nasdaq100` table directly;
   switching it to the index reading is M1's owner's decision (told), not done here.
4. **Calendars.** The new markets use A17's `WeekdayCalendar`, as the US 10-year does: a local holiday reads `behind`,
   never wrongly `current`. The US cues (VIX and both Nasdaq-100 cues) use A17's NYSE calendar.
5. **VIX holiday rows.** Cboe's VIX file has a row on 31 US market holidays from 2022 to 2026, the same pattern as
   Nasdaq's. `CboeVixSource.holiday_rows` makes readings skip them.
6. **Known limit, measured on 2 Nov.** TWSE's month file may be empty before the month's first session. The collector
   then reports "no values" for `taiex`, which could raise one false alert at a month's start.

## Amendment 3 (21 Oct 2026, the code round's changes; for judge F)
1. **Behind at 09:15** (judge 351 addendum 2). A name whose reading is `behind` at the open is alerted once per
   episode (`behind.py`, A20b's `OpenProblems`, names only). It covers only names with a real session calendar: the
   S&P 500, RBI's USD/INR, and the Nasdaq-100 and VIX index readings. The world indexes, the US 10-year and FBIL are
   left out, because a `behind` on a weekday calendar is as often a holiday as a late publisher.
2. **A block stops the host for the run** (code review). After the first Yahoo block, no other Yahoo cue of that run
   sends a request (one shared `YahooGate`). Yahoo's JSON error answer counts as a block too.
3. **Part B statuses.** `lunch break` is added for markets with a midday break: Tokyo 11:30-12:30 JST is 08:00-09:00
   IST, so A22's slot falls inside it; Shanghai's and Hong Kong's breaks start at 09:00 and 09:30 IST. A level is timed
   at its 5-minute bar's end. A morning where no open market is `live` (all `stale`) alerts and writes an O10 row. A
   failure while building the reader (Drive) alerts and writes an O10 row too.
4. **Maximum ages set from real closures:** STOXX 5 days (Easter Monday), KOSPI and TAIEX 10 days (Chuseok 2025,
   the Lunar New Year).
5. **Criterion 2's wording.** A date given twice is left out and shows in the checks as a gap
   (`weekday_without_value`), not under its own kind.
6. **Holiday rows on both sides.** Yahoo's VIX also had rows on two US holidays (25 May and 7 Sep 2026), so Yahoo
   cues skip non-session dates in readings, and the official/Yahoo comparison drops those dates on both sides.
7. **Part B's own window and commit** (agreed with A22's builder, 21 Oct). A22's `preopen record` holds the routine
   from about 08:36 to 09:11, so the routine starts `global-cues preopen` beside it, not after it. The command waits
   for 08:50 IST on its own clock and starts no read after 09:05; an index not reached by then is a failure. It then
   commits only its own files: its snapshot logs and, after a failure, O10's row. Each goes through A16e's
   owned-paths committer (pull `--no-rebase`, push retried), well before A22's push at about 09:11. A push that fails
   alerts and writes an O10 row.
8. **Yahoo finality** (judge 439): a Yahoo close is final 30 minutes after its market closes, for both the collector
   and the as-of labels. Part B checks NSE's calendar and reads nothing on a closed day; it writes its O10 row before
   its commit and sends one alert per run.

## A17f: an empty answer in part B (DR1 item 8; story text for the judge, 24 Oct 2026)

**Builder:** session_01E8AvLgNUPDyLRDEn2WT5Wi (A17e's owner from 24 Oct). **Branch:** `story/a17f-taiex-empty`.
**Lane:** 1 (an outside service, a recorded dataset, an alert). **Orchestrator:** session_01Mt6dcBU5kp2htdPN2KmiZH.
**Deadline:** the Monday-critical part (criteria 1-5) on `main` before Mon 26 Oct 08:30 IST.

### What happened on 23 Oct (checked against primary sources, 24 Oct)
- **Taiwan's market was closed on Fri 23 Oct: an unscheduled typhoon closure (Typhoon Champi), not a holiday.**
  Strong evidence: TWSE's own files, fetched 24 Oct about 19:20 Taipei time, have no 23 Oct session: the month's
  index history (`TAIEX/MI_5MINS_HIST`, rows 1-22 Oct, last 22 Oct), the daily market summary (`FMTQIK`, last row
  22 Oct) and the 5-second trading statistics for 23 Oct (`exchangeReport/MI_5MINS?date=20261023`: "沒有符合條件的資料",
  no data; the same call for 22 Oct gives 3,241 rows from 09:00). News of the closure: Insurance Journal and The Edge,
  23 Oct ("Taiwan shuts $5 trillion stock market as typhoon nears").
- **TWSE's published holiday schedule does not list 23 Oct** (OpenAPI `v1/holidaySchedule/holidaySchedule`, fetched
  24 Oct, 27 rows for 2026, SHA-256 `7644c1a8…2117`): a typhoon day is announced the evening before and never enters
  that list. So **a holiday list alone could not have explained 23 Oct**.
- **Mon 26 Oct is a scheduled TWSE closure** (same file: Retrocession Day falls on Sun 25 Oct, made up on Mon 26 Oct).
  Taiwan reopens Tue 27 Oct. Without this story, Monday's 08:50 read of `taiex` may fail again (Yahoo's answer on a
  closed day: empty on 23 Oct; on a scheduled holiday untested, as Yahoo answers HTTP 429 to this container today).
- **The mechanism** (strong, reproduced in code): Yahoo answered HTTP 200 with a chart whose quote object was empty.
  `chart_result` (`yahoo_source.py:121`) checks `["close"]`, so the read raised `ValueError: taiex: not Yahoo's chart
  answer (KeyError)`, the same error as a changed layout. A chart with empty arrays gives `no 5-minute level`
  (`preopen.py:67-68`). Either way it counted as "taiex failed"; the reason went to stdout only (the alert said "the
  routine's output names why"; O10's row says only "taiex failed"), and the raw answer was lost because `read`
  archives it only after parsing (`preopen.py:98-99`).

### The rule
1. **Closures calendar first.** `research/data/calendar/twse_closures.csv` (`date,kind,description,source_url,sha256`;
   `kind` is `covers`, `holiday` or `unscheduled`) holds every weekday TWSE does not trade, and one `covers` row per
   year it is complete for (below). Before reading `taiex`, part B asks
   it: a listed day gives the line `taiex: market closed (TWSE holiday: <description>)`, writes the private row with
   status `market closed` and reason `calendar: <kind>`, and **sends no request** (nothing to read; polite).
2. **An empty answer is not a failure.** An answer is *empty* when it is Yahoo's chart (`chart.result[0]` with
   `meta.exchangeTimezoneName` and `indicators.quote`) but has no timestamp, an empty quote object, or no non-null
   close. On a day the calendar does not list as closed, it gives status `no session data` with reason
   `empty answer: closed unannounced or a Yahoo gap`. Anything else that is not chart data (no `result`, no `meta`, no
   `indicators.quote`, mismatched lengths) stays a **changed layout: a failure**, as now.
3. **Closed vs data gap: told apart how.**
   - Same morning: a scheduled closure is known from the calendar (rule 1). An unscheduled one (typhoon) cannot be told
     from a Yahoo gap at 08:50 IST by any source we have tested; so the morning says `no session data`, never
     `market closed` and never `failed`.
   - Settled later, from the official close: each part B run first looks at its own `no session data` rows of the
     last 10 days and asks **only the index's official daily table**, never a Yahoo table (judge 588 finding 1: a
     Yahoo gap is likely missing from Yahoo's daily series too, so settling from it is circular). The official tables
     are A17e part A's: `taiex` (TWSE), `nikkei225` (Nikkei Indexes), `sse_composite` (CSIndex); the row is read
     straight from that cue's table, not through the official-else-Yahoo reading. The date **present** = `data gap`
     (Yahoo missed a real session); the date **absent while a later session is present** = `closed (unscheduled)`;
     neither yet (that table not fetched, or no later session) = still open, asked again next run; an open row older
     than 10 days is settled as `unsettled` and alerted once.
   - Each outcome is one appended row and one line. Its `seen_at` is **when the settlement ran** (never the original
     morning: no look-ahead, judge 588 finding 2); its `settles` column names the date it settles; `level_time` and
     `level` are empty.
   - **The other four indexes** (`kospi`, `asx200`, `hang_seng`, `sti`) have no official table (A17e step 0; KOSPI's
     KRX source waits for the owner's key). Their `no session data` row is **final**: never settled, never `unsettled`,
     no later alert (the morning's alert already named it). The morning line says so: `kospi: no session data (empty
     answer; no official table, not settled)`. Proposed: A17g adds their closures calendars.
4. **Where the reason goes (never stdout only).** Every row of the private table gets two new last columns, `reason`
   (empty for `live`, `stale`, `lunch break`) and `settles` (the date a settlement row settles, else empty); each
   Drive part has its own header; older parts have neither key, so the reader reads each with `""` as the default. The #fno-desk alert names each index and its reason (`taiex: no session data (empty answer)`,
   `nikkei225: failed (ValueError: changed layout)`), and so does O10's row (`kind` `incomplete` for `no session data`,
   `failure` for a failure, a `data gap` or `unsettled`). Index names, statuses and error classes only; never a level.
   The run exits 1 when any index is `no session data`, `failed`, `data gap` or `unsettled` (owner, 24 Oct: problems
   warn, never hidden); `market closed` by the calendar and `closed (unscheduled)` exit 0.
5. **Raw answer archived before parsing.** Every answer `download` returns (HTTP 200, chart data) is put in Drive with
   its snapshot-log row first, then parsed: an empty or broken answer keeps its bytes and SHA-256, and the row and
   alert name the SHA-256's first 12 characters. A block (401/403/429, consent, CAPTCHA, error JSON) still raises
   before any bytes and writes nothing (A17e criterion 8 unchanged).

### The holiday source and how it is kept current
- Source: TWSE OpenAPI `https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule` (JSON, no login; tested
  24 Oct: HTTP 200, 3,774 bytes, ROC year 115 = 2026). Its rows whose name contains "交易日" ("trading day": 2 Jan,
  11 Feb, 23 Feb) mark first or last trading days and **are not closures**; rows on Saturday or Sunday are dropped
  (weekends are closed anyway). "市場無交易，僅辦理結算交割作業" (12-13 Feb, settlement only, no trading) **is** a closure.
  2026 gives 18 weekday closures: 1 Jan, 12, 13, 16-20 Feb, 27 Feb, 3 Apr, 6 Apr, 1 May, 19 Jun, 25 Sep, 28 Sep, 9 Oct,
  26 Oct, 25 Dec; plus one `unscheduled` row, 23 Oct (typhoon), citing TWSE's `MI_5MINS` "no data" answer.
- Kept current by hand, like NSE's calendar (A7), but checked by code: one parser `twse_closures(data)` turns TWSE's
  file into rows; the year's TWSE file is a test fixture (public dates, no market values), and a test fails when the
  CSV's `holiday` rows for that year differ from the parser's output. `unscheduled` rows are added by hand with their
  source when a settlement says `closed (unscheduled)` (the settlement line says so).
- Coverage (judge 588 finding 4): a year is covered only by its `covers` row (`date` = 1 Jan of that year,
  `description` "TWSE holidaySchedule <year> (ROC <n>)", `source_url` TWSE's file, `sha256` that file's SHA-256). A
  test checks that each `covers` row has a fixture with that SHA-256 and that the year's `holiday` rows equal the
  parser's output on it. A `holiday` or `unscheduled` row in a year with no `covers` row is refused at load.
- **An uncovered year is a problem:** on a day of a year with no `covers` row, the `taiex` line says `taiex: TWSE
  calendar has no <year>`, `taiex` is still read from Yahoo as if no day were listed (rules 2-3 apply), the alert names
  `taiex: TWSE calendar has no <year>`, O10's row has kind `failure`, and the run exits 1. **From 1 Dec**, a missing
  next year gives the line `taiex: TWSE calendar has no <next year> yet`, named in the alert, O10 kind `incomplete`,
  exit 1 (TWSE publishes the next year's schedule late in the year; the warning gives a month to add it).
- **A broken calendar stops only `taiex`'s calendar** (judge 588 minor 2): a CSV row with an unknown `kind`, a
  malformed date or a missing `covers` row raises a named `ValueError` at load; that is a `taiex` failure (line, O10
  kind `failure`, alert naming `taiex: calendar refused (ValueError)`, exit 1); `taiex` is still read from Yahoo as for
  an uncovered year, and the other six indexes are untouched.
- Not used for the other six indexes: an earlier-day-only answer keeps A17e's `market closed`, inferred from Yahoo,
  not proven (known limit). An empty answer for any index follows rule 2.

### Acceptance criteria (each: good, bad, boundary, empty; each with the test that breaks when its code is broken)
1. **Calendar:** good: 26 Oct 2026 gives `market closed`, reason `calendar: holiday`, zero requests (the fake session
   counts them), exit 0; bad: a CSV row with an unknown `kind` or a malformed date is refused with a named
   `ValueError` at load, failing `taiex` only (the other six still read), exit 1; boundary: 27 Oct (the next day)
   reads Yahoo; a Saturday `holiday` row is ignored; 30 Nov 2026 gives no coverage warning, 1 Dec 2026 without a 2027
   `covers` row gives `TWSE calendar has no 2027 yet` (O10 `incomplete`, exit 1); empty: a day of 2027 with no 2027
   `covers` row reads Yahoo and gives `TWSE calendar has no 2027` in the line, the alert and O10 (`failure`), exit 1.
2. **Parser and CSV agree:** good: the 2026 fixture gives exactly the 18 weekday closures above; bad: a layout without
   `Date` or `Name` is a named `ValueError`; boundary: the "交易日" rows (2 Jan, 11 Feb, 23 Feb) are not closures, the
   settlement-only rows (12-13 Feb) are; empty: an empty list is refused (TWSE never publishes an empty year).
3. **Empty answer:** good: 200 with `quote: [{}]`, with empty arrays, and with all-null closes each give
   `no session data` with its reason, a private row, O10 `incomplete`, the alert naming it, exit 1; bad: no `meta`,
   no `indicators.quote`, or mismatched lengths stay `failed (ValueError)`; boundary: one non-null close among nulls
   is a level (`live`/`stale` as now); empty: a zero-byte 200 answer is a block (A17e criterion 8, unchanged).
4. **Reason recorded and alerted:** good: the alert and O10 row each name `taiex: no session data (empty answer)`;
   a failure names its error class; bad: no level appears in any line, alert, O10 row or committed file (A16b's scan
   pattern over the run's files); boundary: two problems in one run give one alert naming both; empty: a run with no
   problem (every index `live`, `stale`-but-not-all, `lunch break` or `market closed` by the calendar, and the
   calendar covering today and, from 1 Dec, next year) sends no alert and no O10 row and exits 0. An uncovered year is
   a problem (criterion 1), so it always alerts.
5. **Archive before parse:** good: an empty answer and a changed layout each leave one Drive copy and one
   snapshot-log row with the answer's SHA-256 before the status is decided; bad: a planted Drive failure on the put is
   a failure for that index (line, O10 row, alert), the other indexes still read; boundary: a block archives nothing
   and makes one request; empty: no answer (network error) archives nothing.
6. **Settlement** (may land after Monday; the orchestrator is told which commit holds it): good: an open `no session
   data` row of 23 Oct with TWSE rows for 22 and 27 Oct and none for 23 Oct settles `closed (unscheduled)`, exit 0;
   the settlement row's `seen_at` is the settlement run's time (a test: no settlement row has `seen_at` earlier than
   its run) and `settles` is 2026-10-23; bad: a row whose date TWSE has settles `data gap` with O10 `failure` and an
   alert; a `taiex_yahoo` table holding 27 Oct but not 23 Oct, with no TWSE copy, leaves the row open (never
   `closed (unscheduled)` from Yahoo); a `kospi` open row is never settled and never alerted again; boundary: TWSE's
   last row is the open date's previous session (no later session yet) leaves it open; a row exactly 10 days old is
   still asked, 11 days settles `unsettled` and alerts once; `nikkei225` and `sse_composite` settle from their own
   official tables the same way; empty: no open rows means no read of any daily table.
7. Gates pass; no file or class over 350 lines; the calendar and the reader are wired only in
   `fno/global_cues/wiring.py`.

### Plants the builder runs (each must turn a test red; restored with `git checkout -- <file>`)
P1 archive after parsing again; P2 an empty answer raised as a failure; P3 the calendar not asked (a request on
26 Oct); P4 the reason dropped from the alert; P5 the reason dropped from O10's row; P6 "交易日" rows kept as closures;
P7 an uncovered year read silently; P8 `no session data` exiting 0; P9 settlement's present/absent swapped; P10 the
10-day limit off by one; P11 settlement read through the official-else-Yahoo reading; P12 a settlement row stamped
with the original morning's `seen_at`; P13 an uncovered year exiting 0.

### Gap list (DR1 item 8 and the orchestrator's brief)
| Requirement | Where |
|---|---|
| The truth for 23 Oct from a primary source | "What happened" (TWSE's own files; holiday list checked) |
| Empty answer = "no session data" with its reason | rule 2; criterion 3 |
| Closed day vs data gap, told apart how | rules 1 and 3; criteria 1 and 6 |
| Reason recorded and alerted, not stdout only | rule 4; criterion 4 |
| Raw answer archived before parsing | rule 5; criterion 5 |
| TWSE holiday list, its source, kept current | "The holiday source"; criteria 1 and 2 |
| Monday 26 Oct (a TWSE closure) handled | criterion 1 (its own test date) |
| Good, bad, boundary, empty cases; plants | each criterion; plants P1-P10 |
| Private values never in the repository or Slack | rule 4; criterion 4 |
| Real output sample in the Claims | the Claims (a dry run on the committed code with fakes; counts and statuses only) |
| End-to-end after merge (rule 8) | Monday's 08:50 part B run, cited by the orchestrator |

**Out, with the reason:** closure calendars for the other six markets (one source each: JPX, KRX, ASX, HKEX, SSE,
SGX; not safely reachable before Monday; proposed as A17g); a same-morning official check of a Taiwan session (TWSE's
`MI_5MINS` gives a day's 5-second statistics, but whether it fills live during the session is untested and cannot be
tested before Tue 27 Oct 09:00 Taipei; a second live source at 08:50 also doubles what can fail); switching part A's
`taiex` cues from the weekday calendar to the TWSE calendar (part A already allows 10 days; no failure seen).

### Text round 2 (judge 588)
- SF1 accepted: settlement reads only official tables (rule 3); bad case and P11 added (criterion 6).
- SF2 accepted: a settlement row's `seen_at` is its run's time, `settles` names the date; test and P12 (criterion 6).
- SF3 accepted: `nikkei225` and `sse_composite` settle from their official tables; the four Yahoo-only indexes'
  rows are final, never settled (rule 3); cases in criterion 6.
- SF4 accepted: `covers` rows define coverage; an uncovered year is a problem (alert, O10 `failure`, exit 1), the
  1 Dec warning `incomplete`, exit 1; criteria 1 and 4 now agree; P13.
- Minor 1 partly accepted: `preopen.py:67-68` and `98-99` fixed. Not `yahoo_source.py:137`: on `main` at e2f115fab the
  shape check is line 121 (`git show origin/main:fno/global_cues/yahoo_source.py | grep -n 'quote"\]\[0\]\["close"\]'`
  prints 96 and 121; 121 is in `chart_result`), so the text keeps 121.
- Minor 2 accepted: a broken calendar fails `taiex` only, which is still read from Yahoo.
- Minor 3 accepted: older parts read `reason` and `settles` with `""` as the default.

### Claims (criteria 1-5; criterion 6, settlement, follows after Monday with its own verdict)
Code: `fno/global_cues/market_closures.py` (the file and TWSE's parser), `preopen_calendar.py` (the question before a
read), `preopen_outcome.py` (lines, status, problems with their O10 kind), `preopen.py` (empty vs changed layout,
archive before parse, rows with `reason` and `settles`), `preopen_cli.py` (the alert and one O10 row per kind),
`wiring.py` (the TWSE calendar for `taiex`; `settled` = taiex, nikkei225, sse_composite). Data:
`research/data/calendar/twse_closures.csv` (covers 2026, 18 holidays, 23 Oct unscheduled), its README section, and
TWSE's 2026 file as `tests/fixtures/twse/holiday_schedule_2026.json` (SHA-256 `7644c1a8…2117`, the `covers` row's).

| Criterion | Tests (`tests/global_cues/`) | Plant caught by |
|---|---|---|
| 1 calendar | `test_preopen_empty.py`: Monday 26 Oct (0 requests, exit 0), next day reads, uncovered year, broken calendar (taiex only, both read); `test_twse_closures.py`: 1 Jan covers + holiday, malformed rows, weekend row, 30 Nov / 1 Dec, one covers row stops the warning (judge note 1), refused file | P3, P7, P13, P14 |
| 2 parser = CSV | `test_twse_closures.py`: 18 closures, trading-day and weekend rows, settlement-only days, changed or empty file, committed CSV = parser on the fixture whose SHA-256 the `covers` row cites | P6 |
| 3 empty answer | `test_preopen_empty.py`: four empty shapes, six changed layouts, one close among nulls, earlier-day level (taiex vs nikkei225), kospi "not settled" | P2, P8, P15 |
| 4 reasons | the empty-answer test (line, alert, O10 `incomplete`), uncovered year (one alert, O10 `failure` then `incomplete`), no level in any line, alert, O10 row or snapshot log | P4, P5 |
| 5 archive first | empty and changed layouts archived with the SHA-256 in the snapshot log; Drive put failure raises before any parse or row (the CLI side: `test_world_preopen.py::test_a_failed_archive_write_alerts_and_the_next_indexes_still_read`); block and network error archive nothing, one request | P1 |

**Two choices the text did not spell out (for the judge):**
1. For a market with a calendar (taiex), an answer holding only an earlier day's levels on an unlisted, covered day is
   also `no session data`, reason `newest level from an earlier day: closed unannounced or a Yahoo gap` (the same
   ambiguity as an empty answer; for the six markets without a calendar it stays `market closed`, as A17e).
2. O10's message is cut at 200 characters (O10's `one_line`); the alert carries every problem in full.

**Self-review** (an independent review agent on the diff): no blocking. Fixed: a quote without a `close` list,
uneven lengths and non-list fields were read as empty (now changed layouts, five new cases, P15); a non-list field
let `TypeError` escape without a row or raw SHA (now a changed layout); the alert now says "changed layout"; a
`covers` row off 1 Jan or given twice is refused (P14). Taken as choice 1 above: the earlier-day level. Cited above:
the Drive-put failure at CLI level.

**Gates** (branch merged with `main` at 93fb86ee3): pytest 15,702 passed, 1 skipped, 15 xfailed (token kept); ruff check and format, check_imports, check_records (9,108 files), check_numbers: clean. **Plants:** P1-P8, P13-P15 all caught
(each by the test named above; each restored with `git checkout`); P9-P12 belong to criterion 6.

**Output sample** (the committed code; the real TWSE calendar; fakes for Yahoo, Drive, Slack and git):
```
--- 2026-10-26 08:55 IST: exit 0, Yahoo requests 0
taiex: market closed (TWSE holiday: 臺灣光復暨金門古寧頭大捷紀念日)
pre-open logs committed and pushed (1 file(s))
--- 2026-10-27 08:55 IST: exit 1, Yahoo requests 1
taiex: no session data (empty answer: closed unannounced or a Yahoo gap; raw 62f7e1473ea7)
pre-open logs committed and pushed (1 file(s))
alert sent
alert: Omenix F&O pre-open Asian levels: taiex: no session data (empty answer; raw 62f7e1473ea7)
O10: incomplete | taiex: no session data (empty answer; raw 62f7e1473ea7)
```
Not checkable before Monday: what Yahoo answers for ^TWII on a TWSE holiday (it answers HTTP 429 to this container);
on 26 Oct no request is sent, so it does not matter that day.
