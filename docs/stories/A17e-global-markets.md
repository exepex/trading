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
   file starts, and the only source for Hang Seng, ASX 200, Straits Times and FTSE 100. One class
   `YahooChartSource(cue, symbol)`; dates in the exchange's own time zone from the answer's `exchangeTimezoneName`.
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
   14:30 IST, Europe by 22:10 IST) is in the 03:41 run of d+1, which lands 05:30-06:40 IST (measured 17-21 Oct).

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
   start date is a holiday, seen on 2019-01-01 and 2026-10-01) is dropped; a real start-date session is kept.
2. Yahoo dates: the date is the exchange's own (a 00:00 UTC timestamp of a Tokyo session is that Tokyo date); no
   weekend rows; a duplicate date in one answer is refused for that index (one ASX duplicate seen in the 2019 back-fill).
3. The reading prefers the official value; the overlap check lists the 2026-02-06 VIX difference and the two missing
   2019 SSE sessions when run on the real back-fill (cited in the claims).
4. The as-of label: a same-day Asian close at 09:15 IST is never `live` (test across each market's close time).
5. Private: no index value or price-sized number in any repository file (A16b's scan pattern over every file the run
   writes).
6. KOSPI without a key: one "not configured" line, no failure; with a key, the key never appears in output or files
   (planted-key test).
7. Part B: a planted 5-minute answer gives the level and its time; a stale level is marked; the command exits 0 on a
   closed market day (Asian holiday) with "market closed" for that index.
8. The 2019 back-fills run once by hand into Drive; counts, first and last dates, and the overlap check's findings in
   the claims file; `global-cues verify` passes. The first scheduled run and the first part B read are cited.
9. Gates pass; no file or class over 350 lines; composition only in `fno/global_cues/wiring.py`.

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
