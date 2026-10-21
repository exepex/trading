# Story A17e: global markets beyond the US

**Repository:** trading · **Lane:** 1 (outside services, Drive, a schedule) · **Size:** M · **Builder:** A16b/A17
builder (session 01MBnbVU) · **Judge:** F · **Claims:** response 297

**Description:** As the macro economist and the risk manager, I want the closes of the markets that move India before
09:15 IST, each from a source we may use, first-seen time recorded, so that the weather, the 08:45 forecast and GR1
stop reading the US alone (owner, 21 Oct 2026: "US market is not the only reason. Before the Indian market opens,
there is Australian market, Singapore, Hong Kong, Japan, South Korea, probably China too ... we fetch data for each and
every market that can affect the overall market in India ... don't consume US data only"; DESK_DECISIONS 21 Oct).

**Boundary (agreed with the A22 builder, 013u1Ac2, 21 Oct):** A22 owns GIFT Nifty and NSE's pre-open; A17/A17e own
every foreign index and the other global cues (US 10-year, Brent, USD/INR). An Asian intraday level before 09:15, if
one is ever usable, is A17e's code and data, called from A22's 08:36 routine (no second reader, no second routine).

## Step 0: every source tested (21 Oct 2026, 21:05-21:20 UTC; three research passes, the key ones re-run by me)

"Tested" = fetched; terms quoted from the URL given. Verdicts: **allowed** (terms permit automated, non-commercial
download and private storage), **restricted** (terms forbid automated download or storage; usable only under the
owner's personal-research exception, decision a927390, 15 Oct: Drive only, never a public repository or shared screen,
one small download a day), **none** (no free file found, or no usable endpoint).

| Index | Source tested | History found | Terms | Verdict |
|---|---|---|---|---|
| SSE Composite | CSIndex `csindex-home/perf/index-perf?indexCode=000001` (JSON, no key) | 2019-01-01 to 2026-10-21, 1,891 rows (re-run) | CSIndex disclaimer item 4: "any institution or person may browse and download the information of the website for any non-commercial use"; no reprint without permission | **allowed** |
| TAIEX | TWSE OpenAPI `indicesReport/MI_5MINS_HIST` (government open-data licence) | current month only; 20 Oct newest at 21:20 UTC (re-run) | TWSE terms s.8 exempt data released to the government open-data platform; automated download of the main site is forbidden (s.6) | **allowed going forward**; history needs TWSE's consent |
| KOSPI | KRX Open API `idx/kospi_dd_trd?basDd=` (free key, 1 year) | key needed (401 without) | KRX Open API terms (26 Dec 2025): "only for non-commercial purposes"; data not to be given to third parties | **allowed with the owner's key**; alternative Bank of Korea ECOS 802Y001 (key needs a Korean identity check) |
| Nikkei 225 | Nikkei Indexes CSV `nkave/historical/nikkei_stock_average_daily_en.csv` | 2023-01-04 to 2026-10-21 (re-run); no 2019-2022 | personal use allowed; "beyond personal use ... a license agreement ... is required"; file footer forbids copying without permission; machine input may be licensable "non-display" use [search snippet] | **restricted** |
| VIX | Cboe `delayed_quotes/charts/historical/_VIX.json` (A17's SPX parser unchanged) | 1990-01-02 to 2026-10-20 | Cboe terms: one copy "for your personal non-commercial use"; no storing in a retrieval system (same as SPX) | **restricted** (same terms as the S&P 500 the owner accepted) |
| Euro Stoxx 50, DAX | STOXX `HistoricalData/h_3msx5e.txt`, `h_3mdax.txt` | rolling 3 months only (full history 403, login) | STOXX conditions s.3.1 "strictly view-only", s.3.5 no automated access "regardless of your purpose, including research", s.3.4 no historical databases | **restricted**, and no back-fill possible |
| Straits Times | SGX chart API `indices/v1.0/charts/historic/pid/.STI/10y` | 2016-10-24 to 2026-10-21; duplicates and holiday-filled rows before mid-2019 | SGX: no storing in an electronic retrieval system; no automated scraping or bots | **restricted**, data not a clean official close |
| Hang Seng | hsi.com.hk (no public endpoint, 404); HKEX daily quotation pages (one month kept) | none usable | HKEX: storage only on a disk "not ... connected to a network"; no bots | **none** |
| S&P/ASX 200 | ASX (Markit) header JSON, no history endpoint | none | ASX: no spider, scraper or robot; "not to store ... the S&P index values" | **none** |
| FTSE 100 | LSEG: no free file found | none | LSEG website terms s.10: no automated tool "regardless of whether ... personal use" | **none** |
| FRED (NIKKEI225, VIXCLS) | site down for maintenance at both tests | untested | republishes owners' data under their copyright [reasoning] | untested; no cleaner licence expected |

**Pre-09:15 Asian levels: none usable** (tested): TWSE's live feed, ASX's delayed feed and KRX forbid automated
access in their terms; Nikkei's real-time page is behind a bot wall and needs a licence; Hang Seng and SGX have no
public index endpoint; SSE's quote host was unreachable. A22's "Asia opens: out" stands, now with evidence; GIFT Nifty
(A22) is the pre-open proxy.

## Scope

In (built without any owner decision: the **allowed** sources):
1. Three new `GlobalCueSource` classes behind A17's interface, one line each in `fno/global_cues/wiring.py`:
   - `CsindexShanghaiSource` (`sse_composite`): back-fill from 2019-01-01, then 31-day look-back. CSIndex inserts a
     fake row on the requested start date when it is not a session (copying the next session; tested on 2019-01-01
     and 2026-10-01): the parser drops a start-date row whose values equal the next row's.
   - `TwseTaiexSource` (`taiex`): the open-data month, daily; history starts the day the job starts (no back-fill
     until TWSE consents, owner decision 3).
   - `KrxKospiSource` (`kospi`): one call per day (`basDd`), back-fill from 2019 in the paced session (about 1,900
     calls once), key in `FNO_KRX_API_KEY` (GitHub secret and the environment; never in a file). Until the owner has
     the key the source reports "not configured" and the run names it (no failure loop).
2. Each value keeps A17's point-in-time rule: `first_seen_at` (the copy's fetch time), `available_at` from the market's
   close (Shanghai 15:00 Beijing, Taipei 13:30, Seoul 15:30 KST, each with its closing auction), and the as-of label
   at 09:15 and 15:00 IST. A same-day Asian close is never `live` at 09:15 (the session is still running); only the
   previous day's is.
3. A market calendar per cue from the source's own trading dates (A17's `us_trading_dates.csv` pattern), so a gap is a
   missing session, never a holiday.
4. Private by default: every A17e index value is kept in Drive only (A17d's private flag and `DrivePartsRowLog`); the
   repository gets the snapshot log rows (fetch time, path, SHA-256) and dates only. This also meets O9 (data in
   Drive, receipts in GitHub).
5. Schedule: the existing `global-cues.yml` runs (03:41 main, 04:41, 14:11 IST); no new workflow. The Asian closes
   of day d and Europe's (if decided) are out by 21:10 IST on d, so the 03:41 run of d+1 has them.
6. The A17 checks (gaps, stale) and the run's one #fno-desk line cover the new cues unchanged.

In only after the owner's decision (each a separate line in `SOURCES`, nothing else to build):
7. `CboeVixSource` (`vix_us`, A17's Cboe parser with the `_VIX` URL; back-fill from 1990): owner decision 1.
8. `NikkeiSource` (`nikkei225`, from 2023-01-04 only): owner decision 2.
9. Euro Stoxx 50 and DAX (STOXX 3-month files, forward only), Straits Times (SGX chart data, cleaned): owner
   decision 4. All restricted sources: `private`, `once_a_day` (the owner's condition).

Out: Hang Seng, ASX 200, FTSE 100 (no usable source; the report keeps "not checked" for them); any intraday Asian
level (none usable); paid data APIs (owner decision 5 if wanted); GIFT Nifty and NSE pre-open (A22).

## Owner decisions (asked through the orchestrator)
1. **VIX:** extend decision a927390 (personal research, Drive only, once a day) to Cboe's VIX file? Same publisher
   and terms as the S&P 500 already used. Recommended yes [reasoning: no new kind of risk].
2. **Nikkei 225:** use Nikkei's CSV under the same exception (personal use is allowed; machine input may need a
   licence), or email Nikkei first? History would start 2023 either way.
3. **TAIEX history to 2019:** ask TWSE for written consent (their FAQ exempts information "solely for the investor's
   own use")? Until then TAIEX starts on the job's first day.
4. **Europe and Singapore:** STOXX's and SGX's terms forbid automated access outright, "regardless of purpose,
   including research". Use them under the exception anyway (3 months of history only for STOXX), or leave Europe out
   until a licence? Recommended: leave out [reasoning: the terms are explicit and there is no history to test with].
5. **A paid data API** (one vendor whose terms allow automated personal use, covering Hang Seng, ASX 200, FTSE 100,
   DAX and the history gaps): worth a price check? Not built here.
6. **KRX key:** the owner registers at openapi.krx.co.kr (free, one year) and adds `FNO_KRX_API_KEY` as a GitHub
   secret.

## Acceptance criteria
1. Each new source parses its publisher's real answer (a saved fixture per source) and refuses an error page, an
   empty answer and a changed layout with a named `ValueError`; CSIndex's fake start-date row is dropped (fixture of
   2026-10-01) and a real start-date session is kept.
2. `available_at` per market, including daylight saving where it applies (none of the three Asian markets has it);
   the as-of label of a same-day Asian close at 09:15 IST is never `live` (test).
3. The KOSPI source without a key: the run line says "kospi: not configured (FNO_KRX_API_KEY)" and the run is not
   failed for it; with a key it never prints or stores the key (planted key test).
4. Private: no A17e value, date-and-value pair or price-sized number in any repository file (A16b's scan pattern).
5. The 2019 back-fills of SSE Composite and KOSPI run once by hand into Drive, with their snapshot logs committed;
   counts and first/last dates cited in the claims file; `global-cues verify` passes on them.
6. The first scheduled run after the merge is cited (run id, cues added, first-seen times before 09:15 IST).
7. Gates pass; no file or class over 350 lines; composition only in `fno/global_cues/wiring.py`.

**Known limits:** three of the owner's named markets (Hong Kong, Australia, UK) have no usable free source; Japan and
Europe depend on the owner's decision; TAIEX has no history until TWSE consents; no Asian level before 09:15 exists
for free. The 03:41 run lands at 05:30-06:40 IST (measured 17-21 Oct), well before 09:15.

**Depends:** A17 (merged), A17d (private cues), O9 (receipts) · **Status:** story text for judge F.
