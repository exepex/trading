# Response 56: story A12, company filings archive (sample first, then the builder's claims)

**Status: built, tested, real 2-company run in Drive; the full backfill is running in GitHub Actions (started 13 Oct
2026). Awaiting the judge.** Builder: Claude. Story: `docs/stories/A-data-foundation.md#a12`, issue exepex/trading#87.
Research data only: nothing here places, changes or cancels an order.

## Part 1. The measured sample (20 Nifty 500 companies, 13 Oct 2026)

Method: for each company, NSE's three filing lists (classic results list, integrated-filing list, shareholding list)
plus its 3-year announcement and board-meeting lists, then every listed results and shareholding XBRL file made public
since 13 Oct 2023, all from this cloud through the shared polite session (one request per second per host). 865
requests, 987 seconds. Scratch script and raw downloads stayed out of the repository (research data in Drive only).

| Company | Industry | Results files | Results MB | Shareholding files | Shareholding MB | Announcements (3 y) | Board meetings (3 y) | Requests | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| RELIANCE | Oil Gas & Consumable Fuels | 24 | 21.8 | 13 | 8.1 | 768 | 26 | 42 | 42 |
| TCS | Information Technology | 24 | 17.8 | 12 | 8.7 | 580 | 24 | 42 | 42 |
| HDFCBANK | Financial Services | 24 | 7.3 | 14 | 3.8 | 553 | 31 | 44 | 136 |
| SBIN | Financial Services | 24 | 2.0 | 13 | 3.1 | 707 | 42 | 43 | 42 |
| BAJFINANCE | Financial Services | 24 | 4.1 | 15 | 7.3 | 402 | 37 | 44 | 43 |
| LICI | Financial Services (insurer) | 13 | 3.8 | 13 | 2.3 | 557 | 28 | 32 | 31 |
| MARUTI | Automobile and Auto Components | 24 | 3.4 | 13 | 5.3 | 487 | 28 | 42 | 41 |
| SUNPHARMA | Healthcare | 25 | 9.3 | 12 | 4.1 | 423 | 25 | 45 | 51 |
| ITC | Fast Moving Consumer Goods | 24 | 5.4 | 13 | 3.7 | 392 | 26 | 43 | 42 |
| LT | Construction | 28 | 16.4 | 12 | 3.2 | 561 | 29 | 52 | 66 |
| ULTRACEMCO | Construction Materials | 25 | 2.0 | 13 | 4.4 | 671 | 31 | 44 | 64 |
| NTPC | Power | 24 | 3.7 | 12 | 2.8 | 492 | 29 | 42 | 42 |
| DLF | Realty | 24 | 15.1 | 13 | 4.8 | 313 | 25 | 42 | 41 |
| PIDILITIND | Chemicals | 24 | 2.1 | 13 | 5.7 | 496 | 27 | 43 | 43 |
| PERSISTENT | Information Technology | 24 | 2.1 | 13 | 3.9 | 837 | 35 | 43 | 43 |
| POLYCAB | Capital Goods | 24 | 2.2 | 12 | 4.4 | 460 | 23 | 41 | 40 |
| FEDERALBNK | Financial Services | 26 | 2.8 | 13 | 4.6 | 783 | 36 | 45 | 44 |
| IRCTC | Consumer Services | 24 | 1.9 | 13 | 2.8 | 332 | 24 | 43 | 42 |
| VEDL | Metals & Mining | 24 | 8.7 | 13 | 5.5 | 794 | 60 | 43 | 42 |
| IDEA | Telecommunication | 26 | 3.2 | 18 | 6.4 | 432 | 34 | 50 | 50 |

Per company on average: 23.9 results files (6.75 MB), 13.2 shareholding files (4.74 MB), 552 announcements and 31
board-meeting notices in 3 years. Results file sizes: median 56 KB, 90th percentile 392 KB, largest 7.0 MB (a
standalone file with long notes). Shareholding files: median 328 KB, largest 1.3 MB. (HDFCBANK's 136 s includes one
60-second NSE read timeout, retried.)

### Earliest date available on NSE, per filing type (strong evidence: NSE's own lists)

| Filing type | Where NSE lists it | Earliest in the sample |
|---|---|---|
| Results XBRL, up to the December 2024 quarter | classic results list (`/api/corporates-financial-results`) | quarter ended 31 Mar 2005 (older companies); IRCTC 2019, POLYCAB 2019 (listing dates) |
| Results XBRL, March 2025 quarter onwards | integrated-filing list (`/api/integrated-filing-results`, "Integrated Filing- Financials", paged 20 a page) | 31 Mar 2025 quarter (SEBI's integrated filing began then) |
| Shareholding XBRL | `/api/corporate-share-holdings-master` | 30 Sep 2021 for every company listed by then (the list holds about 20 quarters) |
| Announcements, board meetings | per day for all companies (`/api/corporate-announcements`, `/api/corporate-board-meetings` with one date) | 3 years answered in full (13 Oct 2023 onwards); older not measured (not needed) |

**Finding 1 (strong evidence): NSE's classic results list stops at December 2024.** For all 20 companies the newest
classic entry is the December 2024 quarter; every later quarter is only in the integrated-filing list. A downloader
reading only the classic list would silently miss 7 quarters. The archive reads both.

**Finding 2 (strong evidence): the insurer LICI has no classic results entries at all** (0 rows), so its results
before March 2025 are not on NSE's lists we read. It appears as "no file for the quarter" in coverage, with that
reason. Other insurers in the Nifty 500 are likely the same (reasoning only, to be confirmed by the full run).

**Finding 3 (strong evidence): NSE's shareholding list shows a revised pattern in place of the original.** TCS's March
2026 pattern was revised on 16 Sep 2026; the list shows only the revised file (made public 17 Sep 2026). The original
(April 2026) is no longer listed, so a 3-year backfill cannot recover it: for decisions between April and September
2026 the point-in-time table correctly returns the December 2025 pattern, not the March one. From now on the daily
run archives each version as it appears, so future revisions keep both.

**Finding 4 (strong evidence): NSE serves some listed links as a web page.** Two Larsen & Toubro revision links
(March 2025) answer HTTP 200 with "The file you are trying to access doesn't appear to exist", and one Sun Pharma link
ends in "-". Both are recorded as gaps with that reason, never saved as data.

**Finding 5 (strong evidence): some 2023 bank XBRL files are broken.** HDFC Bank's September 2023 files reference
contexts (`OneD`, `FourD`, `OneI`) the file never defines, and declare no start dates, so the period of every figure
is unknown. The raw file is archived as NSE serves it; the parser returns no figures for it rather than guess which
context is the quarter. Federal Bank's September 2023 files are the same.

**Finding 6 (strong evidence): NSE's pre-2025 files mislabel the year-to-date context.** In TCS's September 2024 file
both duration contexts carry July to September dates, while the facts inside the second declare April to September
and hold the half-year cash flow. The parser takes each context's period from its own declared start and end facts
(tested), so the half-year cash flow is not mistaken for a quarter's.

### The claim "balance sheet and cash flow come only every half year" (strong evidence: true, with one exception)

Parsed from every sampled results file:

| Period end | Companies with results | With balance sheet and cash flow |
|---|---|---|
| 31 Dec 2023, 30 Jun 2024, 31 Dec 2024 | 19 | 0 |
| 30 Jun 2025, 31 Dec 2025, 30 Jun 2026 | 20 | 1 (LICI: insurers report a balance sheet every quarter) |
| 30 Sep 2023 | 18 (window started 13 Oct; TCS filed 11 Oct; LICI none) | 16 (HDFCBANK, FEDERALBNK files broken, finding 5) |
| 31 Mar 2024, 30 Sep 2024 | 19 (LICI none) | 19 |
| 31 Mar 2025, 30 Sep 2025, 31 Mar 2026 | 20 | 20 |

So the balance sheet and the cash flow come with the September and March results (SEBI LODR 33(3)(f) and (g)); the
June and December files hold only the profit and loss. Cash flow is year to date: 6 months in September, 12 in March.
Because TCS filed its September 2023 results on 11 Oct 2023, the backfill starts at **1 Oct 2023**, not 13 Oct.

### Does NSE answer from here, from GitHub's runners, and BSE?

- This cloud: NSE answered every list and file (one read timeout in 865 requests, retried). The day lists answer
  without a cookie warm-up.
- GitHub's runners: **NSE answers.** The workflow's probe-only run (run 38412093102, 13 Oct 2026) read TCS's
  integrated list (14 filings in 3 years) and shareholding list (12). Its classic results list failed on my bug, not on
  NSE: rows from 2005-07 carry no broadcast time, and the index parsed every row before filtering. Fixed (rows ending
  more than 400 days before the window are not parsed; a row with only NSE's filing minute uses it; tests), and the
  probe now answers all three lists here.
- BSE (`api.bseindia.com`): **refused from this cloud, HTTP 403 "Access Denied" (Akamai), twice**, with and without
  browser headers. Not needed while NSE answers; see the BSE claim below.

### Projection for the Nifty 500 (501 rows in NSE's list, including NSE's placeholder `DUMMYHEG`), 3 years

| | Files | Size | Requests at 1 per second |
|---|---|---|---|
| Results XBRL | about 12,500 | 3.4 GB | 12,500 |
| Shareholding XBRL | about 6,600 | 2.4 GB | 6,600 |
| Filing lists (per company) | (not stored) | | 2,000 |
| Announcements, board meetings (one file per day, all companies) | 2,192 | about 0.35 GB | 2,192 |
| **Total** | **about 21,300** | **about 6.2 GB** | **about 23,300 (6.5 hours of requests)** |

Measured end to end with Drive uploads (real run below): 63 seconds per company, so about **8.8 hours** for the XBRL
files plus about **1.2 hours** for the day lists: **about 10 hours**, i.e. two scheduled runs of 5.5 hours. Both are
under the stop limits (20 GB, 24 hours), so the build went ahead. Drive has room: the owner's Drive reports a 429.5 GB
limit with 3.5 GB used (checked with the owner sign-in, 13 Oct 2026). Daily cost after the backfill: about 2,000 list
requests (35 minutes) plus the new filings.

## Part 2. What was built

`fno/filings/` (every file under 350 lines), behind the existing interfaces:
- `index.py`: `FilingIndex` with `NseLegacyResultsIndex`, `NseIntegratedResultsIndex` (paged) and
  `NseShareholdingIndex`; `filed_at` is the later of NSE's broadcast and dissemination (or creation) times.
- `sources.py`: `NseFilingFileSource` (a `RawFileSource` for XBRL files; NSE's "not found" page counts as not
  published), `NseAnnouncementsSource` and `NseBoardMeetingsSource` (one all-company list per calendar day).
- `archive.py` + `manifest.py`: a file is saved only if it reads as XBRL, and its row (`filed_at`, `first_seen`,
  SHA-256, Drive's MD5, size, balance sheet yes/no, cash flow yes/no) is appended in the same operation to
  `research/data/manifests/filings/<type>.csv`; a different SHA-256 for a known link is refused.
- `librarian.py`: resumable (only links without a row are fetched), stops at its deadline or at once when NSE refuses
  us, records gaps with reasons (`gaps.csv`) and failures; `runs.csv` logs each run.
- `xbrl.py` + `results_parser.py`: revenue (banks: total income), profit before tax, net profit, EPS, total debt,
  cash, total assets, equity (banks: capital plus reserves), operating, investing and financing cash flow, with the
  cash-flow months. `results_table.py`: the point-in-time table, read only from Drive, checking each file's SHA-256.
- `coverage.py` + `coverage_cli.py`: `python -m fno data-coverage --filings`.
- `wiring.py`: the filings composition root (BSE or another store would be one class plus one line here).
- Day lists reuse A9's `RawDataLibrarian` and `FingerprintingStore` with a calendar of every day.
- Stores gained `checksums(folder)` (Drive: one listing with Drive's MD5s; local folder; area).
- `.github/workflows/filings-archive.yml` and `docs/stories/A12-owner-checklist.md`.

## Part 3. Claims per acceptance criterion

1. **Sample report: done.** Part 1 above: counts, sizes and earliest dates per filing type for 20 companies across 18
   industries, with the projection in GB and hours (strong evidence: measured).
2. **Full backfill in Drive: running, not yet complete. Built and proven on 2 companies.**
   Real run on 13 Oct 2026 (IRCTC, POLYCAB): 74 XBRL files saved to Drive in 2 min 7 s, manifest rows committed and
   pushed by the run itself (commits `788e583`, `1dc1395`). The full backfill (about 10 hours) does not fit one short
   run here, so it is left to the workflow, as instructed; the repository secrets were already there, so I started
   the workflow (its runs then continue every 6 hours). The judge checks this criterion once `runs.csv` shows a
   complete run over 501 companies. `data-coverage --filings` prints per type: companies
   covered of 501, files, present, damaged, unfingerprinted, gaps, and every quarter without a file with its reason
   (tests: `tests/filings/test_filings_coverage.py`, including a changed copy reported damaged and a planted file
   reported unfingerprinted).
3. **Point-in-time: done (tested).** A planted read one second before `filed_at` returns nothing; a revised filing
   keeps both files, and each moment gets its own version; a changed copy in the store is refused
   (`tests/filings/test_filings_results_table.py`). Revisions get their own link from NSE, so they are new rows, never
   overwrites; the same link with other bytes is refused (`RawFileConflict`).
4. **Polite and resumable: done.** Every NSE request goes through the shared `PacedSession` (test), whose pacer spaces
   a planted burst of 10 requests on each NSE host to at least 1 second apart (test). Resume: a run stopped by its
   deadline, restarted, fetches only what was missing (test), and on real data the second IRCTC/POLYCAB run fetched
   nothing (10.8 s, 0 saved, 74 already there).
5. **Runs without AI: done, except one owner step.** The workflow runs every 6 hours (`--daily` makes it one full check a
   day once a complete run exists over the whole list), commits its rows, and alerts #fno-desk on a refused sign-in,
   NSE refusing us, a failed list or file, or a failed job. The owner's one-time steps are the checklist
   `docs/stories/A12-owner-checklist.md`: the five secrets were already set (the probe run's log shows each as set,
   never its value), and the run is started. **Still open for the owner: publish the Google OAuth app** if it is in
   "Testing", or the refresh token expires 7 days after it was made and every run stops with an alert. I cannot see
   the app's status from here. The archive job reads the Nifty 500 list with the owner sign-in, so it needs no
   service-account secret (that one is needed only to run `data-coverage --filings`, which this environment has). No secret value
   is in any file or log: the workflow reads them as `secrets.*`, the record scan is clean, and the commands print no
   setting values.
6. **Half-year balance sheet and cash flow, 90% for each of the last 6 half-years: not provable before the backfill.**
   The sample says 5 of the 6 half-years should pass (19 or 20 of 20). **September 2023 is at risk**: in the sample,
   17 of 20 with the 1 Oct start (LICI has no file; HDFC Bank's and Federal Bank's files are broken, finding 5), i.e.
   85%. `data-coverage --filings` prints each half-year's share and, for any below 90%, every company with the reason
   ("no results file" or "results file without a readable balance sheet and cash flow"), which is the explanation
   with NSE's own data the criterion asks for. September 2026 is not yet counted: its deadline is 14 Nov 2026.

## Part 4. What I did not do, and why

- **No BSE adapter.** BSE refuses this cloud (HTTP 403, Akamai), so nothing written for it could be tested against
  reality, and NSE answers. The `FilingIndex` and `RawFileSource` interfaces take a BSE class plus one line in
  `fno/filings/wiring.py`. Owner decision needed only if NSE stops answering from the runners.
- **No full backfill here**: about 10 hours (instructions: workflow). Started in GitHub Actions instead.
- **Not recovered**: originals NSE replaced with a revision before today (finding 3), and figures from broken files
  (finding 5). Both are listed, not hidden.
- The company list is NSE's Nifty 500 list archived on 13 Oct 2026 (501 rows: 500 companies and NSE's placeholder
  `DUMMYHEG`, which shows as a gap "no filings"). Companies that left the index during the 3 years are not included
  (survivorship: fine for an archive, not for a backtest universe; the statistician should note it).

- **Two differences from what the owner was told in chat (13 Oct afternoon):** (a) the Drive layout is
  `raw/nse/equities/filings/<type>/<SYMBOL>/<file>`, without a `<YYYY>` level: about 38 files per company folder, so
  one Drive listing checks a whole company and nothing is gained by a year level; the filing date is in the manifest
  (`filed_at`). Changing it now would leave the 74 files already uploaded in old folders (nothing in Drive is ever
  deleted), so I ask before changing it. (b) The progress record is `research/data/manifests/filings/runs.csv` in
  GitHub (committed each run), not a file in Drive: the manifests the coverage check reads live there too. Each run
  that does work posts one line to #fno-desk (companies checked, files saved, gaps, complete or continuing, or the
  problem).

## Desk view (short)

- Statistician: the table is point-in-time by `filed_at` (later of NSE's two times), but the archive's history of
  revisions starts today; any backtest using shareholding before 13 Oct 2026 sees only NSE's final versions.
- Analyst: P&L every quarter; debt, cash and cash flow only twice a year; cash flow is year to date (difference the
  March and September values for the second half).
- Risk manager: NSE answering is the single point of failure; the probe step alerts on day one if the runners are
  refused.
