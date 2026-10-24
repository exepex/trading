# India VIX daily history (story A15)

**Since story O9b (step 1), the table and its checks are in Drive, not in this folder.** They are write-once files in
Drive's `data/vix/` area (`india_vix_daily/` parts, `checks/<name>/` snapshots), with one SHA-256 receipt each under
`receipts/data/vix/`. Read them through the verified cache (`python -m fno data-cache sync data/vix`). The files named
below kept their names and columns as moved (22 Oct 2026); git history keeps the old copies. The record scan refuses a
`.csv` committed here.

`india_vix_daily.csv`: India VIX daily open, high, low and close for every day NSE's history serves, **19 Jul 2010 to
30 Sep 2026** at the first fill (4,019 days). Derived data: the raw files stay in Google Drive.

## Source and terms

- **Publisher:** NSE (National Stock Exchange of India), its website's historical India VIX report
  (`https://www.nseindia.com/reports-indices-historical-vix`), which the page reads from
  `https://www.nseindia.com/api/historicalOR/vixhistory?from=DD-MM-YYYY&to=DD-MM-YYYY` (JSON).
- **Terms:** NSE publishes this report on its public website for anyone to view and download; its website terms of
  use were not re-read for this story. This is the owner's personal research tool, nothing is redistributed, and the
  same website endpoints are already used by P6/P8/A12. Reasoning only, not checked: we believe personal research
  use is within those terms; the owner may want to confirm. Requests are polite: one a second for the whole process
  (`fno/http_pacing.py`), one per month, 195 for the whole history.
- **Raw files:** one per calendar month, NSE's exact answer, in Drive at
  `fno-research/raw/nse/indices/india-vix-history/<YYYY>/<MM>/india-vix_<YYYYMM>.json`, each with its SHA-256 in
  `research/data/manifests/india-vix-history.csv` (the `url` column is the exact request).

## Columns and units

| Column | Meaning |
|---|---|
| `date` | the trading day (IST calendar date) |
| `open`, `high`, `low`, `close` | India VIX index points (annualised implied volatility in percent: 15.0 means 15%), NSE's values copied exactly, never rounded (NSE gives up to 4 decimals; VIX moves in 0.0025 steps) |
| `source_path` | the month file in Drive's raw area the row was copied from (always the first archived version) |
| `source_sha256` | that file's SHA-256, equal to its manifest row |
| `first_seen_at` | when this table first held the row (IST): **archive time, not a known-at time**. For all history it is the fill time (15 Oct 2026). Never use it as when a value was known in a backtest; use the rule below |

## When a day's value was known (use this in every backtest)

- A day's VIX open, high, low and close are known only **after that session's close (15:30 IST)**; NSE publishes the
  end-of-day values after the close.
- So a decision or forecast at **15:00 IST on day d may use VIX up to day d-1, never day d** (d's close comes after
  15:00). The earliest decision that may use day d is the next session's 15:00.
- `first_seen_at` is when this archive got the row; for history it says nothing about when the value was knowable.

## Which sessions the rows are (select through the A7 calendar)

The table holds every day NSE's history serves, not only regular sessions:
- **9 muhurat sessions** (one-hour Diwali sessions, 19 Oct 2017 to 21 Oct 2025: in the evening until 2024, e.g.
  18:15-19:15 IST from 2019 to 2023 and 18:00-19:00 in 2024, and 13:45-14:45 IST on 21 Oct 2025, per the circulars in
  the session calendar; the 2017 and 2018 rows give no times) and **5 special sessions** (weekend sessions in NSE's
  calendar from 2017, e.g. 20 Jan and 18 May 2024), all listed in `checks/gaps.csv` (`muhurat_session`,
  `special_session`);
- 9 weekend rows before 2017 (`weekend_row`; the calendar does not cover those years: special sessions such as budget
  days, not verified).

Daily changes, 5-session windows and the weather (G6, design v2) use **regular sessions only**: take a row only where
the session calendar (`research/data/calendar/nse_sessions.csv`, `fno/research_data/calendar.py`) says `regular`. A
muhurat session counted as a full day would distort any daily-change statistic.

## Rules

- **Point in time:** rows are only appended after the last day; a day present is never rewritten
  (`fno/vix_history/table.py`). A month is fetched only after it has ended, so a month file never grows.
- **Revisions (A11):** `python -m fno vix-history sweep` reads every month again; a valid answer with other bytes is
  kept in Drive's `revisions` area beside the original with a row in
  `research/data/manifests/revisions/india-vix-history.csv`, and its changes are printed day by day. The table is never
  changed by a revision. An error page or cut answer is never kept as a version.
- **Gaps are recorded, never filled; doubtful values are listed, never fixed** (`checks/`, rewritten by
  `python -m fno vix-history check`):
  - `gaps.csv`: a session in NSE's calendar with no row (`gap`), a row on a closed day; before 2017 (the calendar's
    first year) a weekday without a row is `unverified` (holiday or gap cannot be told apart) and a weekend row is
    listed (`weekend_row`: NSE's special Saturday and Sunday sessions).
  - `level_flags.csv`: a level that is not positive, or an open or close outside the day's low-high.
  - `overlap_index_close.csv`: every day from 2017 where this table's close and the India VIX close already in the
    repository (`research/data/nifty-panel/warmup_closes.csv`, from NSE's daily index-close files, A3/A10) disagree:
    `rounded` when the other value is this one rounded half-up to its decimals, `differs` otherwise, or a day only one
    of them has.
- `python -m fno vix-history verify` recomputes every row from the month files in Drive and checks their SHA-256 against
  the manifest (read-only).

## What the first fill found (15 Oct 2026)

- **No VIX before 19 Jul 2010 from NSE.** India VIX was launched in 2008, but NSE's history serves nothing earlier
  (every window from Nov 2007 to Jun 2010 answers `{"data":[]}`). NSE Indices' own VIX history page
  (`niftyindices.com`, `/BackPage/BindHistoricalIndiaVixData`) refused requests from the cloud session (HTTP 302 to an
  error page). **So the 2008 crash is not covered**; 2011, 2013, 2016, 2020 and 2024 are.
- **Agreement with the index-close files:** 0 real differences over 2 Jan 2017 to 30 Sep 2026. 1,488 days differ
  only by rounding (the index-close files give two decimals on many days from 2017 to 20 Feb 2025, this history four;
  largest gap 0.005). So `warmup_closes.csv`'s VIX, which F2 and the forecasts read, is rounded to 0.01 on those days. One day is only in the index-close
  files: **2 Mar 2024**, NSE's special Saturday session (disaster-recovery test), which NSE's history leaves out
  (`gaps.csv` lists it as a gap).
- **Doubtful values, kept as published:** open, high and low of 0 on 12 Feb 2021 and 30 Mar 2021 (close present);
  22 Aug 2013's close (27.68) is below its low (27.99).
- **The `open` is not a real opening level before 2025:** on 3,519 of 3,584 days from 20 Jul 2010 to 31 Dec 2024
  NSE's open equals the previous close (all days in 2010, 2014, 2016-2018, 2020, 2022-2023); from 2025 it is a real open (92 of 249 days
  equal in 2025). Do not use VIX open-to-close or overnight gaps before 2025.
- 90 weekdays before 2017 without a row (`unverified`, mostly exchange holidays) and 9 weekend rows (special sessions).
- The first-day close (20.71 on 19 Jul 2010) and the 2020 peak (close 83.6075 on 24 Mar 2020, high 86.635) match
  widely reported figures (reasoning only: not checked against a second official file).

## Commands

```
python -m fno vix-history fill     # archive missing ended months to Drive, extend the table, write the checks
python -m fno vix-history sweep    # look for later NSE versions (A11)
python -m fno vix-history check    # write new check snapshots in Drive from the table in Drive (Drive settings)
python -m fno vix-history verify   # recompute the table from Drive and list any difference
```

New days after 30 Sep 2026 come daily from the index-close files (O6, `warmup_closes.csv`, close only); a monthly
`fill` adds each ended month here: `.github/workflows/vix-history.yml` runs `fill` and `sweep` for the previous IST
month at 07:11 IST every day (A17 schedules, 16 Oct 2026), so a month is added on the 1st and retried while NSE is late.
Its commits are a scheduled job's data (lane 3); a `fill` run by hand stays **lane 1** (judge 100 (f)).
`verify` names any day of an archived month the table lacks, and any value or source that differs.
