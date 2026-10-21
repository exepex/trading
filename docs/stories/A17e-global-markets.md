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
