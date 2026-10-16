# A20. Point-in-time market rules and dates: F&O master files, NSE/SEBI circulars, macro calendar

**Repository:** trading · **Lane:** 1 (new story; outside services NSE, SEBI, MOSPI, the Fed, Drive, Slack; a
workflow) · **Branches:** text `story/a20-rules-and-dates`; code in three parts `story/a20a-fo-masters`,
`story/a20b-circulars`, `story/a20c-macro-calendar`, each judged on its own · **Builder:**
session_013u1Ac2N9eRQ8XCYPjwpaat · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH

**Description:** As the risk manager, the options strategist and the macro economist, I want the rules NSE and SEBI
set (ban list, lot sizes, F&O circulars) and the dates of the big macro releases kept exactly as they
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
| SEBI circulars | `www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0` (HTML) | 200; the latest 25 circulars with dates (10 Jul to 15 Oct 2026; longest gap between two of them 22 days) | Partly, as above |
| NSE circular cadence | the same API, 1 Jan to 16 Oct 2026 | 5,665 items; **every one of the 196 sessions had at least one circular** (A7 calendar); 13 non-session days had some too | basis of the NSE stale rule |
| India CPI, IIP, GDP dates | MOSPI Advance Release Calendar PDF, found through `www.mospi.gov.in/api/documents/get-latest-release-calender` | 200; today's file `ARC_2026_27_Sept_2026.pdf` (8 pages, text extractable) lists CPI on the 12th, IIP, GDP dates to March 2027. MOSPI's calendar API lists **past** releases only, so the PDF is the only forward source | `announced_on` only, when entered the day it is seen |
| US FOMC dates | `www.federalreserve.gov/monetarypolicy/fomccalendars.htm` | 200; meeting dates per year in fixed HTML classes | as above |
| US CPI, payrolls dates | `www.bls.gov/schedule/news_release/cpi.htm`, `empsit.htm`, `bls.ics` | **403 "Access Denied" from BLS** to this container with a browser or plain user agent | as above; see open question 1 |

## Scope

In:
- **A20a** ban list and lot sizes: the ban list under the trade date it names, as early as NSE writes it; lot sizes
  once per trading day. The contract master is out: NSE keeps it dated (Step 0), so it is not lost daily; a later
  story back-fills it when something needs it.
- **A20b** NSE and SEBI circular lists with metadata and our first-seen time; the files of F&O-relevant circulars.
- **A20c** India CPI, IIP, GDP and US FOMC, CPI, payrolls release dates with `announced_on` = the day we first saw
  each date, in A6's event model.
- Workflows `fo-masters.yml` (A20a), `circulars.yml` (A20b), `macro-calendar.yml` (A20c); every failure or stale
  source gives a #fno-desk line and O10's watcher commits the error row (Design 4).

Out, each with its reason:
- News, SEBI's RSS and RBI press releases: A19 (agreed with A19's builder, 16 Oct).
- General-election result days: already in A6's hand-kept `events.csv` (type `election_result`, ECI sources).
- State-election dates: no F&O design row, check or forecast uses them [reasoning only]; ECI announces schedules
  irregularly, so they would be hand rows, which is A6's process, not a capture.
- Index-heavyweight results dates: A12's filings archive already keeps NSE's board-meetings list every day
  (`filings-archive.yml`, manifest `board-meetings.csv`); picking the heavyweights' dates from it is a consumer's
  step, not a second capture [some: the list's field meaning is A12's].
- Reading what a circular says (kept, not interpreted).
- Changing any consumer of `events.csv` (M1 weather, F3 features, the desk packs): wiring macro dates into M1 or a
  forecaster changes a scored forecaster and is a separate decision for its owner and the protocol.
- The contract master (Step 0: archived by NSE).

## Design (reuse first)

1. **A20a: its own small job on P6's snapshot machinery.** Two new `SnapshotSource` classes (`FoBanListSource`,
   `FoLotSizeSource`), each with a content check in `content_checks.py`, saved to Drive with a manifest row like every
   NSE file. Not in P6's market archive run: that run files snapshots under the previous session, while the ban list
   names the session it applies to. NSE writes the next session's ban list about 18:12 IST (Step 0), and GitHub
   starts this repository's morning crons 4-5 h late or drops them (judges 350, 351). So `python -m fno fo-masters`
   runs at 07:45, 11:15 and 18:45 IST, every day:
   - **ban list** (`SessionFiledTaker` variant): filed under the trade date it names when that date is the run day's
     own session or the next session (A7 calendar); a copy for an earlier session is refused as stale and one further
     ahead as from the future; nothing is written in either case. A session's first copy is kept.
   - **stale** = on a trading day, no ban list archived for that day's session by the end of the run (whatever the
     run's time); on other days only the taking runs.
   - **lot sizes**, on trading days only (`regular` or `special`; a muhurat-only day is not one): one full copy per
     day under that day's folder. NSE gives no date, so an identical copy is still stored again as a new file
     (about 48 KB a day): the daily proof of what was valid that day.
   - `wiring.py` is at 348 lines, so the source tuples move to `fno/storage/source_lists.py` (no behaviour change).
   - First-seen time = the day folder plus the manifest row's commit time (git); these are daily rules.
2. **A20b `fno/circulars/`.** Port `CircularFeed.fetch(since, until) -> list[Circular]`; adapters `NseCircularApi`,
   `SebiCircularList`. `Circular` = source, number, date, departments, category, subject, link.
   - **Relevance** (strategy `FnoRelevance`): NSE department "Futures & Options" (NSE Clearing's F&O margin
     circulars carry it too: NCL/CMPT/76975, 16 Oct), or an F&O subject word (lot size, position limit, MWPL, ban
     period, F&O, equity or index derivative); SEBI: a subject word (derivative, margin, lot size, position limit,
     expiry, F&O, index option). The flag never drops a row.
   - **One row per circular:** NSE lists a circular once per department it concerns (70 items, 63 circulars on
     15-16 Oct); its items merge into one with every department.
   - **Listed at first sight.** Every new circular (link not in earlier parts) is a row with `first_seen_at` (UTC,
     the run's clock) and `file` = `saved`, `failed` or `not_kept` (not relevant). A failed file is retried by later
     runs for 3 days; the retry writes a new row for the same link, with the first row's `first_seen_at` and the new
     status (`saved`, or `abandoned` after 3 days). Readers take the earliest `first_seen_at` and the latest `file`.
     Rows are one O9 `PartTable` part per run (`circulars/list/<YYYY>/<MM>/<date>.<run_id>.csv`, Drive `data`
     area, receipts in `receipts/`); files under `circulars/files/<source>/<YYYY>/<MM>/<file name>`.
   - **Window: a fixed 14 days on every NSE run** (judge 353 SF4 asked for "since the last successful run, capped").
     A fixed window needs no stored state and covers every gap up to 14 days the same way; a longer outage is caught
     by the stale rule below and by O8/O10's freshness rows long before. Cost: about 320 items (100 KB) per run.
   - **Stale, by NSE's calendar:** no NSE circular dated the previous session (A7) is stale (2026: 196 of 196
     sessions had one). SEBI: the newest circular on its page older than 45 days is stale (twice the longest gap in
     its latest 25). SEBI's page shows only 25: if none of the previously seen SEBI circulars is on it, the run alerts
     a possible gap.
   - Hourly 08:00-22:00 IST, every day (NSE and SEBI also publish on holidays).
3. **A20c extends A6** (`fno/research_data/events.py`). New `MACRO_TYPES` = india_cpi, india_iip, india_gdp, us_fomc,
   us_cpi, us_payrolls, kept apart from A6's hand-kept `TYPES` so `events.csv` and its consumers do not change. Port
   `ReleaseCalendar.dates() -> list[(type, date, source_url)]`; adapters `MospiArcCalendar` (PDF through `pypdf`,
   approved by the orchestrator, pinned), `FedFomcCalendar` (HTML), US CPI/payrolls per open question 1. Each run
   writes the parsed calendar as a PartTable part `macro-calendar/...`; a reader builds A6 `Event`s: `announced_on`
   = the first part that held the date; a date that vanishes later gets `first_withdrawn_on` = the first part
   without it, so A6's `known_on` works unchanged. Days before our first capture are honestly "late bound" (A6's own
   rule). Daily at 07:30 IST.
4. **Failures (O10's design).** Each job prints one line per source (`ok`, `stale`, `failed: <reason>`) and exits 1
   if any source is not ok; O10's `capture-watch.yml` writes the committed error row for every non-success run (A20's
   workflows are on its list; agreed with O10's builder). Alerts:
   - each job posts its own one line naming every problem, through `StepOutputAlerts`; the workflow's `failure()`
     line speaks only when the job could not post (a crash);
   - **hourly circulars alert once per episode:** a committed file `research/ops/alerts/circulars_open.txt` (O8b's
     `calendar_horizon_alerted.txt` pattern) holds the open problems' keys; a new key alerts, a known one does not
     (the step still marks itself as having spoken, so no second line), and a cleared key posts one "recovered" line.
   - Macro calendar stale: the last future date under 30 days ahead (MOSPI's ARC ends in March: a new FY file is
     due); a parser finding fewer or more than the expected rows (MOSPI: 12 CPI dates per financial year).

## Gap list (design requirements to criteria)

| Requirement | Where |
|---|---|
| Audit A3 #6: ban list and lot sizes daily, point in time | criteria 1-3 |
| Audit A3 #6: contract master | Out (Step 0: NSE archives it) |
| Audit A3 #2: NSE and SEBI circulars, metadata, first-seen time, files | criteria 5-8 |
| Audit A3 #5: India CPI/GDP/IIP, US FOMC/CPI/payrolls with `announced_on` on the day seen | criteria 10-12 |
| Audit A3 #5: election dates, index-heavyweight results dates | Out (reasons above) |
| Owner 16 Oct: up to date; stale detected | criteria 2, 7, 11 |
| Owner 16 Oct: every failure alerted and recorded | criteria 4, 9, 13, 14 |
| Owner 16 Oct: no over-engineering | design reuse (P6, O9, A6, O10); fixed window instead of stored state (Design 2) |
| CLAUDE.md design for change: ports, adapters, composition roots | criterion 15 |
| O9: data write-once in Drive, receipts or manifest rows only in GitHub | criteria 3, 8, 14 |
| A6: point-in-time `known_on` unchanged; `events.csv` consumers unchanged | criterion 12 |
| JUDGE.md quality rules 5, 6, 8: boundaries, real output sample, first live run | every criterion; criterion 16 |

## Acceptance criteria

Each criterion has good, bad, boundary and empty cases in its tests.

1. **A20a ban list.** Filed under its trade date when that date is the run day's session or the next session; the
   boundaries: a run on Friday 16 Oct with a list for 16 Oct (today) and for 19 Oct (next session, across a weekend)
   are both taken; a list for 15 Oct (previous session) is refused as stale; one for 20 Oct (two sessions ahead) as
   from the future; nothing written on a refusal; a session's first copy is kept. A header-only list (no securities)
   is valid; an empty file, HTML, a broken numbering and a stray line are refused.
2. **A20a stale.** On a trading day, a run that ends with no copy for that day's session fails with "no ban list for
   today's session" (also at 18:45, when the file already shows the next session); on a weekend or holiday no stale
   check runs.
3. **A20a lot sizes.** Taken on a trading day under that day; not on a weekend, a holiday or a muhurat-only day; a
   404 is a failure, never "ok"; damaged layouts (header, a non-number, a row of the wrong width, no NIFTY row) are
   refused.
4. **A20a job.** Every step runs after a failure; one alert names every failure; exit 1; the manifest rows of what was
   taken are still committed; manifest rows not committed is a failure; a clean run sends nothing.
5. **A20b feeds.** Today's real NSE and SEBI answers parse whole (63 NSE circulars, 25 SEBI); a 403, HTML instead of
   JSON, an item without its fields, a JSON without `data`, an unreachable host and a SEBI page without rows are
   `FeedFailed`, never an empty list; `{"data": []}` is read as empty and judged by criterion 7.
6. **A20b relevance and merge.** The 4 F&O circulars of 15-16 Oct are flagged and none of NSE's commodity or
   currency "derivatives" ones; NSE/CMTR/76963 keeps both its departments.
7. **A20b stale.** NSE: a run whose window holds no circular dated the previous session is stale; boundaries: a run
   on a session day, on a holiday and on a weekend each judge the previous session; one circular dated it is enough.
   SEBI: newest circular 45 days old is fine, 46 days stale; a page with nothing seen before alerts a possible gap.
8. **A20b rows and files.** A new circular is listed in the run that first sees it, with `first_seen_at` and its file
   status; a second run with the same list writes no part; a link that fails twice and then works gives `failed`,
   no new row, then `saved` with the first `first_seen_at`; still failing after 3 days gives `abandoned`.
9. **A20b alerts once per episode.** A new problem alerts once; the same problem in the next run does not alert but
   the run still exits 1 and marks the step as having spoken; a cleared problem posts one "recovered" line; the state
   file holds keys only (no URLs, values or log text).
10. **A20c MOSPI.** The real ARC PDF of Sept 2026 gives 12 CPI dates for FY 2026-27 (11 or 13 is refused as a
    layout change), its IIP and GDP dates; a PDF without text is refused.
11. **A20c Fed and stale.** The real FOMC page gives each year's 8 decision days; a calendar whose last future date
    is 30 days ahead is fine, 29 days stale; an empty page is refused.
12. **A20c event model.** `announced_on` is the first part's day; a removed date gets `first_withdrawn_on`; A6's
    `known_on` returns them correctly before, on and after those days; `events.csv` and A6's `TYPES` are unchanged.
13. **Workflows** (read by a test from the YAML): each A20 workflow has its crons as above, `contents: write`, its
    alert step on `failure() && steps.<id>.outputs.posted != 'true'`, no secret value; each is on O10's
    `capture-watch.yml` list once O10 is merged.
14. **No data file in the repository:** jobs commit only manifest rows (A20a), receipts and the alert-state file
    (A20b, A20c); a test checks the committers' paths.
15. **Ports and roots:** every outside service and store sits behind its port and is wired only in
    `fno/fo_masters/wiring.py`, `fno/circulars/wiring.py` and A20c's wiring file; tests never touch the network.
16. **Real output and first live run:** each claims file shows the job's real lines from a run against NSE, SEBI,
    MOSPI or the Fed (a local folder in place of Drive), and, once merged, the first scheduled run's log and its
    manifest rows or receipts.

## Test plan

Offline fixtures cut from today's real files (ban list, lot sizes, one NSE API answer, one SEBI page, the ARC PDF,
the Fed page); failure fixtures (403, HTML instead of JSON, empty table, stale date); the boundaries named in each
criterion. Gates: the full suite, ruff, `check_imports.py`, `check_records.py`. Builder self-review agents and a
broken-code proof per criterion (quality rules 3 and 4) in each claims file.

## Judge verifies

Each criterion with a test and the code line; that no consumer of `events.csv` changed; that "nothing new" can never
hide a failed fetch; that no data file is committed; the real-run samples and, after merging, the first live run.

## Open questions (orchestrator, owner)

1. **US CPI and payrolls dates: BLS refuses this container (403).** Orchestrator, 16 Oct: test from a GitHub runner
   first; only if refused, the owner is asked for a free FRED API key (St. Louis Fed's release-dates API) as a secret.
2. Settled: O10's builder lists A20's workflows in `capture-watch.yml`; whichever merges second adds the names.
3. Settled: `pypdf` approved (free, pinned version).
