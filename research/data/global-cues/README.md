# Global cues (story A17)

Daily cues an NSE session may know at its 09:15 IST open or its 15:00 IST decision time. Derived tables; the raw
copies are in Google Drive (`fno-research/raw/<publisher>/...`, one copy per fetch, filed under the fetch time). First
fill: 15 Oct 2026, 06:15 IST.

**Story O9b step 1b: the public tables and checks are in Drive, with receipts.** The public tables (`us10y`, `brent`,
`usdinr_rbi`), the shared `revisions` log, `us_trading_dates` and `checks/{gaps,overlap_usdinr}` are write-once files
in Drive's `data/global-cues/` area. Each file has a SHA-256 receipt under `receipts/data/global-cues/`. A table is its
parts in name order (the first part is the moved file, and each later fill adds one); a report's newest snapshot is the
current one. Readers go through the verified cache (`python -m fno data-cache sync data/global-cues`). The files below
in this folder are the copies as moved. They stop updating at the step's merge (Drive is the record), and only
`global-cues move` reads them until their removal commit. The
following stay here: this README, `us_market_closures.csv` (hand-kept, sourced) and `checks/behind_alerted.txt` (alert
state, names only). The table below describes the public tables, wherever they live.

| Table | Cue | Rows | Dates | Source |
|---|---|---|---|---|
| `us10y.csv` | US Treasury 10-year par yield, percent a year | 4,950 | 2 Jan 2007 - 14 Oct 2026 | US Treasury |
| `brent.csv` | Europe Brent spot price FOB, US dollars a barrel | 4,992 | 2 Jan 2007 - 6 Oct 2026 | US EIA |
| `usdinr_rbi.csv` | USD/INR reference rate, rupees per dollar | 3,871 | 2 Jan 2007 - 14 Oct 2026, **none 10 Jul 2018 - 11 Apr 2022 except 24 Jul 2018** | RBI |

**FBIL's USD/INR reference rate is private too (story A17d, owner decision of 15 Oct 2026):** FBIL does not authorise
commercial use of its data without written permission, so its table, revisions and gaps are in Drive like the US
closes. Same conditions as below, except the US-only ones: FBIL is not limited to one download a day and has no
unfinished values (it publishes one rate a day, a week late). Until 15 Oct 2026 its table was public here
(`usdinr_fbil.csv`, 1,981 rows, 10 Jul 2018 - 7 Oct 2026); those copies stay in git history (known limit).

**Private cues: the previous US closes (S&P 500, Nasdaq 100) are in the owner's Drive only.** Owner decision of
15 Oct 2026 (`docs/DESK_DECISIONS.md`, commit a927390): use the Cboe and Nasdaq files for personal research despite
their terms (quoted below), with these conditions:
- raw files **and** derived values in Drive only, never in this public repository: no rows, no real values in test
  fixtures (the tests use made-up numbers labelled fake), claims files or logs. The repository holds code, the schema,
  this README, and counts and hashes only (`research/data/manifests/global-cues/sp500.csv`, `nasdaq100.csv`: path,
  URL, SHA-256 and size of each copy);
- at most one download a day: a second run on the same IST date downloads nothing and reads that day's archived copy
  again (so a run whose table write failed can finish with the copy's true `first_seen_at`). Failed attempts are
  capped too (story A17b): every attempt is logged with times and outcomes only, never a value, in
  `research/data/manifests/global-cues/attempts/<cue>.csv`: a `started` row before the download (so a run killed
  mid-download still counts) and its outcome after it (`saved`, `download_failed`, `not_publishers_file`, `no_values`,
  `save_failed`, or `stopped` for an unexpected failure). After 3 attempts or 1 saved copy on one IST date nothing
  more is downloaded that day (the run says so). Limit: both rules read logs in the repository, so run from a checkout
  that has pulled the last run's logs, and **commit and push the logs after every run, failed ones too**: a run whose
  attempt rows are lost resets the cap in the next checkout (`global-cues.yml` commits them on every run);
- a US index file read during the US session may hold the day's price so far: a value not yet final when the file
  was fetched (before 16:00 US Eastern on its date) never becomes a row;
- display (owner decision bcbbc454, 21 Oct 2026): the closes may be shown in the owner's Slack reports and private
  dashboard, never in this public repository (the 15 Oct hold is lifted for the S&P 500 and the Nasdaq-100).

| Private cue | Drive (derived area) | Days | Dates | Source |
|---|---|---|---|---|
| sp500 | `global-cues/sp500/rows`, `/revisions`, `/checks` | 4,977 | 3 Jan 2007 - 14 Oct 2026 | Cboe's SPX history |
| nasdaq100 | `global-cues/nasdaq100/rows`, `/revisions`, `/checks` | 5,059 | 2007 - 13 Oct 2026 | Nasdaq's quote API |
| usdinr_fbil | `global-cues/usdinr_fbil/rows`, `/revisions`, `/checks` | 1,981 | 10 Jul 2018 - 7 Oct 2026 | FBIL reference rates |

The history start is the four copies fetched once on 15 Oct 2026 before their terms were read, kept by the owner and
adopted with `global-cues adopt` at their own fetch times (06:14:45, 06:17:18, 06:14:54 and 06:17:22 IST). Since
story A17b, adopt also reads Drive's own `createdTime` of the copy and refuses it unless it falls within 10 minutes
after the time in its path (it names both times); a store that cannot give the time refuses every adopt. The four
copies were created 4 to 9 seconds after their path times (checked 15 Oct 2026). Adopt the
full-history copy first: a shorter copy adopted first would make every older date `late` (logged, never inserted).
A Nasdaq copy's name carries its request's dates, so `--from`/`--to` must equal them. Each private table is a
folder of write-once CSV parts (one per run that adds rows); its rows are the parts in name order. Its gaps are
written each run as a new snapshot in `<cue>/checks`; the newest is current.

## Columns

`value_date` (the publisher's date, in its own time zone), `value` (as published, never rounded), `source_sha256` (the
archived copy it came from; its path, URL and fetch time are in `research/data/manifests/global-cues/<cue>.csv`),
`first_seen_at` (IST, when that copy was fetched), `provenance`:
- `live`: first seen before 09:15 IST on the first NSE session after the value date: really known in time;
- `backfilled`: fetched later. **Every row before 15 Oct 2026 is `backfilled`** (2 rows are `live`: the 14 Oct 2026
  US 10-year and RBI rate, fetched at 06:15 IST on 15 Oct). Back-filled history was never known at the time by this
  tool; when it would have been known is an assumption (below), not an observation.

## Sources, time zones, lags and terms

| Cue | Publisher and URL | Date's time zone | When a value of date t is out | Terms (evidence) |
|---|---|---|---|---|
| us10y | US Treasury, daily par yield curve CSV per year, `home.treasury.gov/.../daily-treasury-rates.csv/<year>/all?type=daily_treasury_yield_curve` | US Eastern (New York business days) | Quotes near 15:30 ET on t; posted the same US evening, i.e. early morning IST on t+1 (reasoning only on the posting time: on 15 Oct 2026 the 14 Oct value was there at 06:15 IST) | US Government work, public domain (some evidence: US law for federal works; Treasury's own page not quoted) |
| brent | US EIA, Europe Brent Spot Price FOB (RBRTE) daily, `www.eia.gov/dnav/pet/hist/RBRTED.htm` | London trading days | **Weekly**: the page of 7 Oct 2026 ended on 6 Oct, next release 15 Oct. So a value is up to about 9 days old when published, never in time for the next open | EIA: "U.S. government publications are in the public domain ... You may use and/or distribute any of our data" (strong evidence, eia.gov/about/copyrights_reuse.php, read 15 Oct 2026). But EIA credits the Brent prices to Thomson Reuters (LSEG), and the same page says items licensed from others "may be protected": **some doubt** whether this series counts as EIA's |
| usdinr_rbi | Reserve Bank of India, reference rate archive (form), `www.rbi.org.in/Scripts/ReferenceRateArchive.aspx` | IST | Computed from about 13:00-13:30 IST quotes on t, i.e. after t's open: first usable on t+1 | Not found on RBI's pages; RBI is a public authority publishing it for the public (reasoning only) |
| usdinr_fbil | FBIL reference rates, `www.fbil.org.in/wasdm/refrates/fetchfiltered` | IST | Rate of t at 13:00 IST (13:30 before about 2025), but **FBIL's public site trails by about a week** (on 15 Oct 2026 it ended on 7 Oct) | FBIL's page text (found in its site's script, 15 Oct 2026): "[FBIL does not authorize commercial use of the data available in its website without written permission]", plus an "as is" disclaimer. This tool's use is personal and non-commercial (some evidence it is allowed; whether a public repository copy counts as "use" FBIL would object to: reasoning only) |
| sp500 (private) | Cboe, `cdn.cboe.com/api/global/delayed_quotes/charts/historical/_SPX.json` (whole history, about 1.7 MB) | US Eastern | 16:00 ET on t (01:30 IST t+1 in US summer time, 02:30 in winter); the file had 14 Oct at 00:09 UTC on 15 Oct | Cboe's disclaimer forbids storing index values "in a database or retrieval system, without the prior written permission of Cboe" (strong evidence, quoted). Used under the owner's decision a927390 |
| nasdaq100 (private) | Nasdaq, `api.nasdaq.com/api/quote/NDX/historical` | US Eastern | 16:00 ET on t; on 15 Oct at 06:00 IST it still lacked 14 Oct | Nasdaq's terms: users must "Not access or use the Service, or any process, whether automated or manual, to capture data or content from the Service" (strong evidence, quoted). Used under the owner's decision a927390 |

RBI's and FBIL's rates are the same benchmark: on all 1,086 dates both publish (24 Jul 2018 and 12 Apr 2022 on) they
are equal (`checks/overlap_usdinr.csv` lists only differences, by `date,kind`, never a rate: none). FBIL fills RBI's
2018-2022 hole. So RBI's public table carries FBIL's rate on those 1,086 dates anyway: only FBIL's 2018-2022 fill is
FBIL's alone (A17d known limit).

## The date rule (as-of): two cutoffs

`value_for(rows, india_day, cutoff, live_only, available_at)` (`fno/global_cues/as_of.py`) gives the newest value a
session may use at an explicit cutoff on its India date (design 2.1: "as of 15:00"; the orchestrator: both):
- `OPEN` 09:15 IST: known before the open, for overnight gaps;
- `DECISION` 15:00 IST: known at the desk's decision time. It adds the same day's USD/INR reference rate.

Research view (`live_only=False`, for back-filled history): a value is usable when its source's
`available_at(value_date)` is before the cutoff:
- US closes: 16:00 US Eastern on t, i.e. 01:30 IST on t+1 in US summer time, 02:30 in winter (computed with the time
  zone, daylight saving included). A US holiday has no row, so a Tuesday after a US Monday holiday gets Friday's
  close. A value dated on the India date itself is never usable (16:00 ET of d is after 15:00 IST of d).
- US 10-year: 18:00 US Eastern on t (**assumption**: the Treasury posts the day's curve that evening).
- USD/INR: 13:30 IST on t.
- Brent: by the end of the 10th day after t (**assumption**, on the late side: EIA's weekly release, posted in US
  daytime; its release dates are not archived). Research on Brent with the rule is therefore approximate.

Live view (`live_only=True`): a value is usable when this tool first saw it before the cutoff (`first_seen_at`), an
observation and exact (a value seen before it was final never became a row). The `provenance` column stays the 09:15
label (`live` when seen before the first NSE open after the value date); a 15:00 decision uses the live view.

Real answers (15 Oct 2026, dates only): on 20 Jan 2026 (after the US holiday of 19 Jan), the S&P 500 and the US
10-year give 16 Jan at both cutoffs; USD/INR gives 19 Jan at 09:15 and 20 Jan at 15:00.

## Readings: what a consumer must use (story A17b)

`value_for` is for research only. Every consumer (M1, the weather, forecasts) reads a cue through
`reading_for` (`fno/global_cues/reading.py`; `wiring.build_reader()`), which gives the row, its age in calendar days
from the India date, the date the source should have given by the cutoff (the expected date) and a status, decided in
this order:
- `none`: nothing usable;
- `current`: the expected date's value, whatever its age (after Hurricane Sandy, 26 Oct 2012 is current on 31 Oct);
- `ahead`: newer than the expected date (e.g. RBI on an NSE holiday): usable like `current`, flagged;
- `behind`: older than expected, age within the cue's limit;
- `stale`: older than expected and over the limit.
Callers refuse `stale` and `none`; a caller using `behind` states it in its own rules.

| Cue | Expected date from | Age limit (days) |
|---|---|---|
| sp500, nasdaq100 | `NyseCalendar`: NYSE's holiday rules, computed (weekend observance, Good Friday from Easter, Juneteenth from 2022, no Friday closure before a Saturday New Year), plus `us_market_closures.csv` (5 unscheduled closures since 2007, each with an https source) | 4 |
| us10y | Monday to Friday (simplification: it follows the bond-market SIFMA calendar, not NYSE's; a bond holiday reads `behind`, never wrongly `current`; a sourced SIFMA calendar is out for now) | 4 |
| usdinr_rbi | NSE's `regular` and `special` sessions (A7 calendar, no muhurat; Monday to Friday before 2017). Simplification: RBI's holidays are not NSE's, so a mismatch reads `behind` or `ahead` | 5 |
| usdinr_fbil | the same; **FBIL almost always reads `behind`** (its public site trails a week) | 14 |
| brent | none: age only (`behind`, `stale` or `none`) | 16 |

The NYSE rules are reasoning only (not NYSE's own list per year), checked in CI against `us_trading_dates.csv`: the
dates (never values) of the Drive-only S&P 500 table, with whether the Nasdaq 100 table has the date too
(orchestrator's decision, owner away: trading dates are exchange-calendar facts). `global-cues check` rewrites it when
the Drive settings are present. On 15 Oct 2026: 4,977 S&P 500 dates, every weekday since 2007 matching the calendar,
and 83 Nasdaq-only dates (Nasdaq's holiday rows: 82 repeat the previous close; the 83rd, 1 Jan 2007, is the table's
first row, with nothing before it to compare). Those holiday rows are skipped by readings, so the day after a US
holiday never reads `ahead` with a repeated value. Limit: an unscheduled NYSE closure not yet in
`us_market_closures.csv` counts as a session, so Nasdaq's repeated row that day reads `current` (the value is the true
last close; the S&P 500 reads `behind`), until the CI test names the mismatch at the next `check` with Drive and the
closure row is added.

**These dates make the private cues' gap lists public in effect**: the S&P 500's weekday gaps are the weekdays not
listed with `in_sp500=1`. The orchestrator's decision covers trading dates; that it also exposes the gaps the owner's
rule kept in Drive is an **open owner item** (keep, or keep only calendar mismatches public, which would drop the CI
check against the archived dates).

**USD/INR readings stop on 1 Jan 2027** (`CalendarError` naming the year) until NSE's 2027 holiday circular is added
to `research/data/calendar/nse_sessions.csv`, as the `live` label does: fail closed, never a guessed date. Add it in
December 2026.

## Rules

- Raw copies are never overwritten (each fetch is a new file); a later copy that changes a value already in a table
  is logged in `revisions.csv` (`changed`, old and new value, the copy and when) and the table keeps its first value;
  a value that appears late for a date before a table's last date is logged (`late`) and never inserted. This is
  A11's rule (both versions kept, nothing rewritten) applied to publishers that rewrite whole files every day.
- Tables are append-only: old bytes stay a prefix. Both a table and `revisions.csv` are checked before either is
  written, so a row is never added while its revision is lost.
- **A late value is never inserted.** If a publisher later fills a date before a table's last date (RBI back-filling a
  missing day, say), it is logged as `late` and the table keeps the gap for good; `value_for` keeps returning the
  older value for the dates after it. Deliberate (a table never changes behind its last date); read `revisions.csv`
  for such values.
- A run names a cue `STALE` (and exits 1) when its newest value is older than the source allows on the run's day:
  the age limits above (US closes and US 10-year 4 days, RBI 5, FBIL 14, Brent 16). The run counts age only, so a
  replay of an unscheduled closure (Sandy: 26 Oct read on 31 Oct, 5 days) says STALE where the reading says
  `current`; consumers use the reading.
- `first_seen_at` is the time after a cue's last download (a slow fetch is never labelled earlier than it ended).
- `provenance` needs NSE's session calendar: for a value dated after the calendar's last year the run stops and names
  it (add NSE's holiday circular to `research/data/calendar/nse_sessions.csv`) instead of guessing a label. The first
  NSE open after a value date is the first `regular` or `special` session: a muhurat session (one hour, no 09:15 open)
  is skipped (story A17b). Every committed label already was `backfilled` and recomputes unchanged.
- A failed download or a file that is not the publisher's writes nothing for that cue and is named; others still run.
- Gaps are listed, never filled (`checks/gaps.csv`): weekdays without a value (unverified: the gap list uses no
  holiday calendar, so holiday and gap are not told apart there; the NYSE calendar is checked by the CI test above)
  and values equal to the previous date's.

## FBIL in a public repository: closed by the owner

FBIL's site says it does not authorise commercial use of its data without written permission (quoted above). It was
public here from 15 Oct 2026 (orchestrator, judge 103 minor 2) until the owner's decision the same day moved it to
Drive (story A17d, `docs/DESK_DECISIONS.md`). Its past copies stay readable in git history; a history rewrite is out
(the owner keeps the repositories public).

## The terms of the US index sources, and why they are used anyway

Tried on 15 Oct 2026 from the cloud session:
- **FRED** (`fred.stlouisfed.org`, series SP500, NASDAQ100, and also DGS10, DCOILBRENTEU, DEXINUS): refused by this
  environment's network policy (the proxy closes the connection). FRED's API host answers but needs an API key.
- **S&P Dow Jones Indices** (`spglobal.com/spdji`): HTTP 403.
- **Nasdaq** (`api.nasdaq.com`): reachable, but its terms of use (nasdaq.com/legal) say users must "Not access or use
  the Service, or any process, whether automated or manual, to capture data or content from the Service".
- **Cboe** (`cdn.cboe.com` SPX history): reachable, but its disclaimer (cboe.com/global-disclaimers) says index values
  may not be "stored in a database or retrieval system, without the prior written permission of Cboe".

Both were downloaded once before their terms were read. The owner then decided (a927390, quoted above) to use them for
personal, non-commercial research, Drive only. This README records the terms honestly; the decision does not change
them.

**FRED is not a clean path either.** FRED's own series pages, read on 15 Oct 2026 through a web fetch (this container
cannot reach FRED):
- SP500: "Copyright © 2016, S&P Dow Jones Indices LLC. All rights reserved. Reproduction of S&P 500 in any form is
  prohibited except with the prior written permission of S&P Dow Jones Indices LLC" (FRED's page gives S&P's permissions
  address);
- NASDAQ100: "Copyright © 2016, NASDAQ OMX Group, Inc.", tagged "Copyrighted: Pre-Approval Required".

So FRED carries the same owners' restrictions. Reasoning only: no free source was found whose terms allow automated
storage of these index levels.

## Commands

```
python -m fno global-cues fill     # download, archive in Drive, extend the tables, rewrite checks (first run back-fills)
python -m fno global-cues check    # rewrite the checks and us_trading_dates in Drive from the tables (Drive settings)
python -m fno global-cues verify   # recompute every row from the archived copy it names (read-only)
python -m fno global-cues adopt --cue sp500 --copy <raw path> [--from] [--to]   # a copy already in Drive into its table
python -m fno global-cues move     # O9b: the files here into their Drive series, read back equal (a grown file caught up)
```

Every command needs the Drive settings: every table is in Drive (O9b).

`.github/workflows/global-cues.yml` runs `fill` at 03:41, 04:41 and 14:11 IST every day (A17 schedules, 16 Oct 2026); its
commits are a scheduled job's data (lane 3). A failed or stale cue posts one #fno-desk line naming it.

## World indexes (story A17e)

Asia-Pacific, Europe and VIX closes since 2019, plus the Asian levels before 09:15 IST (part B). Every value is
private: the tables, revisions, gaps and official/Yahoo comparisons are in Drive's derived area (owner rule
50a79a43). The repository gets only the snapshot log rows: fetch time, path, URL, SHA-256 and size.

| Index | Official cue (publisher) | Yahoo cue |
|---|---|---|
| Nikkei 225 | `nikkei225` (Nikkei Indexes CSV, from 2023-01-04) | `nikkei225_yahoo` |
| KOSPI | none yet (KRX's API needs the owner's key) | `kospi_yahoo`, unverified |
| S&P/ASX 200 | none | `asx200_yahoo`, unverified |
| Hang Seng | none | `hang_seng_yahoo`, unverified |
| SSE Composite | `sse_composite` (CSIndex, from 2019) | `sse_composite_yahoo` |
| Straits Times | none | `sti_yahoo`, unverified |
| TAIEX | `taiex` (TWSE open data, current month only) | `taiex_yahoo` |
| FTSE 100 | none | `ftse100_yahoo`, unverified |
| DAX, Euro Stoxx 50 | `dax`, `eurostoxx50` (STOXX three-month files) | `dax_yahoo`, `eurostoxx50_yahoo` |
| VIX | `vix_us` (Cboe, from 2019) | `vix_us_yahoo` |
| Nasdaq-100 | `nasdaq100` (A17) | `nasdaq100_yahoo` (Nasdaq's own close is a day late at 03:41: response 298) |

- **Reading:** one per index (`build_index_reader`). It takes the official value where that has the date and
  Yahoo's otherwise, and names the cue it came from.
- **Yahoo blocks:** any HTTP 401, 403 or 429, redirect, or non-chart answer stops that cue for the run. It is never
  retried another way.
- **Part B:** `python -m fno global-cues preopen` reads the newest 5-minute level of each Asian index. A22's 08:36
  routine calls it at about 08:50-09:05 IST.
