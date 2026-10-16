# A20. Point-in-time market rules and dates: F&O master files, NSE/SEBI circulars, macro calendar

**Repository:** trading · **Lane:** 1 (new story; outside services NSE, SEBI, MOSPI, the Fed, Drive, Slack; a
workflow) · **Branches:** text `story/a20-rules-and-dates`; code in three parts `story/a20a-fo-masters`,
`story/a20b-circulars`, `story/a20c-macro-calendar`, each judged on its own · **Builder:**
session_013u1Ac2N9eRQ8XCYPjwpaat · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH

**Description:** As the risk manager, the options strategist and the macro economist, I want the rules NSE and SEBI
set (ban list, lot sizes, contract master, F&O circulars) and the dates of the big macro releases kept exactly as they
were known on each day, so that no backtest, check or forecast ever uses a rule or a date it could not have known then.

**Context and why:** gap audit `docs/CORE_ENGINE_GAP_AUDIT.md` Part A3 #2, #5, #6 and Part B2 items 10, 12, 13; owner
decision 16 Oct 2026 (`docs/DESK_DECISIONS.md`, last row): external data up to date, every failure alerted and
recorded, no over-engineering. Users: C2/C4 (lots, margins), STR1 and stock-option ideas (ban list), M1 and the macro
analyst (event in window), A14 (margin method changes).

## Step 0: sources checked live (16 Oct 2026, 16:00-16:40 IST, from this container) [strong: direct reads]

| Data | Official source | Read result | Lost daily if not kept? |
|---|---|---|---|
| Ban list | `nsearchives.nseindia.com/content/fo/fo_secban.csv` | 200; first line names its trade date ("Securities in Ban For Trade Date 16-OCT-2026"), 3 symbols | **Yes**: overwritten daily, no dated archive found |
| Lot sizes | `.../content/fo/fo_mktlots.csv` | 200, 47.7 KB; one row per underlying, one column per expiry month | **Yes**: overwritten, no date in name or body |
| Contract master | `.../content/fo/NSE_FO_contract_DDMMYYYY.csv.gz` | 200 for 15 Oct 2026, 1 Sep 2026 and 1 Oct 2025 (1.7-1.8 MB); today's file is 404 until NSE posts it | **No**: NSE keeps a dated archive at least a year back |
| NSE circulars | `www.nseindia.com/api/circulars?fromDate=DD-MM-YYYY&toDate=DD-MM-YYYY` (JSON) | 200 without a session cookie; each item has date, number, department ("Futures & Options"), category, subject, file link | Partly: the list stays online; our first-seen time does not |
| SEBI circulars | `www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0` (HTML) | 200; the latest 25 circulars with dates (back to 7 Sep 2026 today) | Partly, as above |
| India CPI, IIP, GDP dates | MOSPI Advance Release Calendar PDF, found through `www.mospi.gov.in/api/documents/get-latest-release-calender` | 200; today's file `ARC_2026_27_Sept_2026.pdf` (8 pages, text extractable) lists CPI on the 12th, IIP, GDP dates to March 2027. MOSPI's calendar API lists **past** releases only, so the PDF is the only forward source | `announced_on` only, when entered the day it is seen |
| US FOMC dates | `www.federalreserve.gov/monetarypolicy/fomccalendars.htm` | 200; meeting dates per year in fixed HTML classes | as above |
| US CPI, payrolls dates | `www.bls.gov/schedule/news_release/cpi.htm`, `empsit.htm`, `bls.ics` | **403 "Access Denied" from BLS** to this container with a browser or plain user agent | as above; see open question 1 |

## Scope

In:
- **A20a** ban list and lot sizes: one copy per day fetched; contract master: one dated copy per session.
- **A20b** NSE and SEBI circular lists with metadata and our first-seen time; the files of F&O-relevant circulars.
- **A20c** India CPI, IIP, GDP and US FOMC, CPI, payrolls release dates with `announced_on` = the day we first saw
  each date, in A6's event model.
- One workflow `rules-and-dates.yml`; every failure or stale source gives one #fno-desk line and a committed error
  record (through O10's port once it exists; see Design 4).

Out: news (A19); state elections and company results dates; reading what a circular says (it is kept, not
interpreted); changing any consumer of `events.csv` (M1 weather, F3 features, the desk packs). Wiring the macro dates
into M1 or a forecaster changes a scored forecaster and is a separate decision for its owner and the protocol.

## Design (reuse first)

1. **A20a extends P6's market archive, no new job.** Two new `SnapshotSource` classes (`FoBanListSource`,
   `FoLotSizeSource`, `fno/storage/snapshot_source.py`) and one dated `NseArchiveSource` (`NseFoContractSource`,
   `raw_source.py`), each with a content check in `content_checks.py`. They join `SNAPSHOT_SOURCES` /
   `DATED_SOURCES`, so `python -m fno market archive` (market-publish.yml, 07:10 IST) fetches, checks, saves to Drive
   with its manifest row, and its existing failure line alerts. `wiring.py` is at 348 lines, so the source tuples move
   to a new `fno/storage/source_lists.py` (no behaviour change). Checks: the ban list's trade date must be the day's
   session (else "stale ban list" and nothing saved); lot sizes need `SYMBOL` and at least one expiry column with
   NIFTY present; the contract master must be NSE's gzip CSV with its header. First-seen time = the day folder plus
   the commit time of the manifest row (git); the content is a daily rule, so a day is the right grain.
2. **A20b `fno/circulars/`.** Port `CircularFeed.fetch(since: date, until: date) -> list[Circular]`; adapters
   `NseCircularApi`, `SebiCircularList`. `Circular` = source, number, date, department, category, subject, link,
   first_seen_at (UTC, the run's clock), `fno_relevant`. Relevance is a strategy `FnoRelevance`: NSE department
   "Futures & Options" (NSE Clearing's F&O margin circulars carry it too: NCL/CMPT/76975, 16 Oct, "Additional
   Exposure Margin on Securities under MWPL"), or a subject keyword (lot size, margin, derivative,
   F&O, expiry, contract, ban, position limit, STT); SEBI: subject keyword. Every item is kept (the flag never drops
   a row). New items (link not in earlier parts) are written as one O9 `PartTable` part per run
   (`circulars/<YYYY>/<MM>/<date>.<run_id>.csv`, Drive `data` area, receipt in `receipts/`); the file of each relevant
   circular goes to the same store under `circulars/files/<source>/<file name>`. Runs hourly 08:00-22:00 IST; each
   NSE run asks yesterday to today, so a missed run loses nothing but timing precision. SEBI's page shows the latest
   25: if none of the previously seen SEBI items is on it, alert "SEBI list may have skipped items".
3. **A20c extends A6** (`fno/research_data/events.py`). New `MACRO_TYPES` = india_cpi, india_iip, india_gdp, us_fomc,
   us_cpi, us_payrolls, kept apart from A6's hand-kept `TYPES` so `events.csv` and its consumers do not change. Port
   `ReleaseCalendar.dates() -> list[(type, date, source_url)]`; adapters `MospiArcCalendar` (PDF through `pypdf`, a new
   free pure-Python dependency), `FedFomcCalendar` (HTML), US CPI/payrolls per open question 1. Each run writes the
   parsed calendar as a PartTable part `macro-calendar/...`; a reader builds A6 `Event`s: `announced_on` = first part
   that held the date; a date that vanishes later gets `first_withdrawn_on` = the first part without it, so A6's
   `known_on` works unchanged. Days before our first capture are honestly "late bound" (A6's own rule). Daily run
   07:30 IST in the same workflow.
4. **Failures.** Each part prints one result line per source (`ok`, `stale`, `failed: <reason>`). Any non-ok source:
   one #fno-desk line through `AlertSender` (`FNO_SLACK_BOT_TOKEN`) naming all failing sources, and one committed error
   row. Stale means: ban list trade date not today's session; contract master missing after 21:00 IST of the session;
   a macro calendar whose last future date is under 30 days ahead (MOSPI's ARC ends in March: a new FY file is due);
   a parser that finds fewer than the expected rows (MOSPI: 12 CPI dates per FY). The error record's format and file
   are O10's; until O10 merges, A20 writes `research/ops/capture_errors.csv` only if O10's builder agrees, else it
   waits on O10's port (open question 2).

## Acceptance criteria

1. A20a: `market archive` saves the ban list, lot sizes and contract master with manifest rows; a ban list whose trade
   date is not the day's session is refused with "stale ban list" and alerted; a fixture of each real layout passes
   its check and a damaged one fails. No file over 350 lines (`wiring.py` split).
2. A20b: offline fixtures of both feeds produce `Circular` rows; a second run with the same items writes no part; a
   new item gets its own first_seen_at; F&O-relevant items' files are saved, others are not; a non-JSON or 403 NSE
   answer and a SEBI page without the table are failures, alerted once, never "no new circulars".
3. A20c: fixtures of the ARC PDF and the Fed page give the expected dates; `announced_on` is the first part's day;
   a removed date gets `first_withdrawn_on`; `known_on` returns them correctly; `events.csv` and A6's `TYPES` are
   unchanged; a calendar under 30 days ahead or with too few rows is "stale" and alerted.
4. Every external service and store sits behind its port and is wired only in `fno/circulars/wiring.py` and
   `fno/research_data/macro_wiring.py` (A20a uses P6's wiring); tests never touch the network.
5. The workflow runs on schedule, commits receipts and error rows only, and never pushes data files to the repository.

## Test plan

Offline fixtures cut from today's real files (ban list, lot sizes, 1 KB of the contract master, one NSE API answer,
one SEBI page, the ARC PDF's text pages, the Fed page); failure fixtures (403, HTML instead of JSON, empty table,
stale date). Gates: the full suite, ruff, `check_imports.py`, `check_records.py`.

## Judge verifies

Each criterion with a test and the code line; that no consumer of `events.csv` changed; that "nothing new" can never
hide a failed fetch; that no data file is committed; that the first live run's lines and alert (or receipts) exist.

## Open questions (orchestrator, owner)

1. **US CPI and payrolls dates: BLS refuses this container (403).** It may also refuse GitHub's runners. Options:
   (a) test from a runner in A20c's first step; (b) if refused, a free FRED API key (St. Louis Fed's release-dates
   API; needs the owner to register, no cost) as a GitHub secret; (c) BLS with a contact address in the user agent
   (BLS asks for this; the address would be a secret, never in files). Recommendation: (a), then (b). Reasoning only
   until (a) is run.
2. **O10's error record:** who is O10's builder, and is its port merged? A20 uses it rather than a second error file.
3. **P6's market archive owner** agrees to A20a's three sources joining its run (one job, one manifest folder).
4. **`pypdf` dependency** for MOSPI's PDF (free, pure Python). Alternative: MOSPI's rule "CPI on the 12th, next
   working day if a holiday" computed in code; rejected because it is a rule, not an announcement we saw.
