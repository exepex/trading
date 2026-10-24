# NSE session calendar: how it was built and its sources

`nse_sessions.csv` is read by `fno/research_data/calendar.py` (story A1). `exceptions.csv` lists sessions for which NSE never published a file (read by `fno/storage/coverage.py`). Research notes below are as compiled on 12 Oct 2026 (scripts and raw scan results were kept out of the repository).


Built 2026-10-12. Output: `nse_sessions.csv` (128 rows). All 28 source URLs return HTTP 200/206
(checked 2026-10-12) and every date was read from the PDF text with `pdftotext`, not from search snippets.
No press sources were needed.

## How it was built

1. **Circular index.** Pulled NSE's full circular list (`https://www.nseindia.com/api/circulars?fromDate=..&toDate=..`,
   Nov 2018 to 9 Oct 2026, 42,789 circulars), then filtered subjects for holiday / live session / muhurat / election /
   Saturday / Sunday. This finds amendments a web search would miss.
2. **PDFs.** Downloaded and read every F&O (FAOP) holiday circular, every amendment, every muhurat circular, every
   special-session circular, and all "Live trading sessions from DR site" circulars.
3. **Bhavcopy cross-check.** Every calendar day from 2019-01-01 to 2026-10-12 (2,842 days) was checked: old-format
   bhavcopy up to 2024-07-05, new format from 2024-07-06. Ranged GET (`-r 0-3`), not HEAD, because HEAD returned 200
   even for missing files. All requests got a clear 206 or 404 (no errors). Throttled to about 1.5 requests/second in
   total. Raw results: `scan.csv`, `scan2.csv`, `scan3.csv`; comparison: `compare.py`.

## Annual F&O holiday circulars

| Year | Circular | Date | URL |
|---|---|---|---|
| 2019 | NSE/FAOP/39613 (123/2018) | 07 Dec 2018 | https://nsearchives.nseindia.com/content/circulars/FAOP39613.pdf |
| 2020 | NSE/FAOP/42878 (119/2019) | 11 Dec 2019 | https://nsearchives.nseindia.com/content/circulars/FAOP42878.pdf |
| 2021 | NSE/FAOP/46625 (109/2020) | 11 Dec 2020 | https://nsearchives.nseindia.com/content/circulars/FAOP46625.pdf |
| 2022 | NSE/FAOP/50561 (101/2021) | 10 Dec 2021 | https://nsearchives.nseindia.com/content/circulars/FAOP50561.pdf |
| 2023 | NSE/FAOP/54759 (156/2022) | 08 Dec 2022 | https://nsearchives.nseindia.com/content/circulars/FAOP54759.pdf |
| 2024 | NSE/FAOP/59723 (188/2023) | 12 Dec 2023 | https://nsearchives.nseindia.com/content/circulars/FAOP59723.pdf |
| 2025 | NSE/FAOP/65588 (161/2024) | 13 Dec 2024 | https://nsearchives.nseindia.com/content/circulars/FAOP65588.pdf |
| 2026 | NSE/FAOP/71777 (212/2025) | 12 Dec 2025 | https://nsearchives.nseindia.com/content/circulars/FAOP71777.pdf |

2026 is also checked against `https://www.nseindia.com/api/holiday-master?type=trading` key `FO`, which returned 20
entries on 2026-10-12. They match the circular plus the 15 Jan amendment exactly (16 weekdays plus 4 weekend days,
counting 8 Nov).

## Amendments and extra closures (all FAOP or MSD circulars covering F&O)

| Date | Change | Circular |
|---|---|---|
| 2019-04-29 Mon | added: Lok Sabha election in Mumbai | NSE/FAOP/40537, 26 Mar 2019 |
| 2019-10-21 Mon | added: Maharashtra assembly election (CM, FO and CD closed) | NSE/MSD/42319, 07 Oct 2019 (no separate FAOP circular found; the MSD circular names Equity Derivatives explicitly) |
| 2023-06-28 → 06-29 | Bakri Id moved from Wed 28 Jun to Thu 29 Jun; June expiry brought forward to 28 Jun | NSE/FAOP/57286, 27 Jun 2023 (zip holding the PDF and the Maharashtra gazette) |
| 2024-01-22 Mon | added: public holiday under the Negotiable Instruments Act (Ayodhya Ram temple consecration); MIDCPNIFTY expiry moved to Sat 20 Jan | NSE/FAOP/60337, 19 Jan 2024 (zip) |
| 2024-05-20 Mon | added: Lok Sabha election in Mumbai | NSE/FAOP/61517, 08 Apr 2024 |
| 2024-11-20 Wed | added: Maharashtra assembly election | NSE/FAOP/64959, 08 Nov 2024 |
| 2026-01-15 Thu | added: Maharashtra municipal corporation election | NSE/FAOP/72262, 12 Jan 2026 |

No holiday was cancelled in the period. The one change of date was 2023 Bakri Id.

**Not F&O closures (checked, correctly left out):** 2022-02-07 (Lata Mangeshkar, NI Act holiday: debt segment only,
NSE/DS/51256), 2023-09-28/29, 2024-09-16/18 and 2025-09-05/08 (Eid-e-Milad NI Act changes: debt/MF circulars only).
The F&O bhavcopy exists on every one of these days. The twice-yearly "Live trading sessions from DR site" circulars
(2019-2024) and the unannounced DR sessions (MSD/70263, 73126, 76140) cover weekday trading from the DR site, plus
mock sessions on weekends. They add no sessions and close no days.

## Special (weekend live) sessions

| Date | What | Circular |
|---|---|---|
| 2020-02-01 Sat | Union Budget, normal 09:15-15:30 | NSE/FAOP/43291 |
| 2024-01-20 Sat | Planned as a short DR-switch special session (NSE/MSD/59999). On 19 Jan that plan was **withdrawn** and replaced by a full regular session on the primary site (NSE/MSD/60340), because 22 Jan became a holiday. The MIDCPNIFTY 22 Jan contract expired on 20 Jan. | NSE/MSD/60340 |
| 2024-03-02 Sat | Special live session with intraday switch to DR: F&O 09:15-10:00 primary site, 11:30-12:30 DR site, 5% futures operating range | NSE/MSD/60677 |
| 2024-05-18 Sat | Same format as 2 Mar 2024 | NSE/MSD/61893 |
| 2025-02-01 Sat | Union Budget, normal timings | NSE/FAOP/65730 |
| 2026-02-01 Sun | Union Budget, normal timings (pre-open 09:00-09:08) | NSE/FAOP/72352 |

Budget days that were **not** special sessions: 2019 (interim budget on Fri 1 Feb; full budget on Fri 5 Jul), 2021
(Mon 1 Feb), 2022 (Tue 1 Feb), 2023 (Wed 1 Feb) and 2024 (interim budget on Thu 1 Feb; full budget on Tue 23 Jul) all
fell on normal weekdays. No weekend live session was found in 2019, 2021, 2022 or 2023. The bhavcopy scan of all
weekends agrees: weekend F&O files exist only on the 9 dates listed in this file.

Mock-trading Saturdays (dozens, for example 2019-01-05 and 2023-09-09) are not sessions and are not listed. None of
them has an F&O bhavcopy.

## Muhurat sessions

| Date | Time (F&O) | Circular |
|---|---|---|
| 2019-10-27 Sun | 18:15-19:15 | NSE/FAOP/42404 (CM revision NSE/CMTR/42483 kept 18:15-19:15) |
| 2020-11-14 Sat | 18:15-19:15 | NSE/FAOP/46231 |
| 2021-11-04 Thu | 18:15-19:15 | NSE/FAOP/50049 |
| 2022-10-24 Mon | 18:15-19:15 | NSE/FAOP/54024 |
| 2023-11-12 Sun | 18:15-19:15 | NSE/FAOP/59126 |
| 2024-11-01 Fri | 18:00-19:00 | NSE/FAOP/64630 |
| 2025-10-21 Tue | 13:45-14:45 (afternoon, not evening) | NSE/FAOP/70320 |
| 2026-11-08 Sun | timings not yet notified | announced in NSE/FAOP/71777 only |

The 2021, 2022, 2024 and 2025 muhurat days are also listed as Diwali Laxmi Pujan holidays in the annual circulars. As
instructed, they appear only as `muhurat`.

## Bhavcopy cross-check result

Days checked: 2,842. The only mismatch is **2021-03-30 (Tue)**: the old-format F&O bhavcopy
(`fo30MAR2021bhav.csv.zip`) returns 404 on both nsearchives and archives. This day was a normal trading day: the CM
bhavcopy exists, the F&O market-activity zip `https://nsearchives.nseindia.com/archives/fo/mkt/fo30032021.zip` exists
(file time 30 Mar 2021 16:16, with real FUTIDX/OPTIDX trades), and no circular declares a holiday. Conclusion: a gap in
NSE's archive, not a holiday. It is deliberately **not** listed. A pipeline that uses "no bhavcopy" to mean "holiday"
will get this day wrong.

Every other day matched in both directions:
- every weekday 404 is a listed holiday;
- every listed past holiday is a 404;
- every weekend file is a listed special or muhurat session;
- every listed past special or muhurat session has a file.

Weekday 404s per year are 2019: 17, 2020: 12, 2021: 14 (13 holidays + 30 Mar gap), 2022: 12, 2023: 15, 2024: 16,
2025: 13, 2026 up to 12 Oct: 12.

## Confidence per year

- 2019-2025: **high**. Primary circular, every amendment read, and the bhavcopy agrees on every day except the
  30 Mar 2021 archive gap explained above.
- 2026 up to 12 Oct: **high**, on the same basis.
- 2026 after 12 Oct: **medium**. The rows for 20 Oct, 10 Nov, 24 Nov and 25 Dec (holidays) and 8 Nov (muhurat) are
  NSE's plan and cannot be checked against a bhavcopy yet. Mid-year additions such as election holidays usually come
  1-4 weeks ahead, so a late addition is still possible.

## Doubts and limits

1. **2026-11-08 muhurat** is listed from the annual circular alone. Its timing circular was not out on 2026-10-12.
   Re-check NSE circulars in late October.
2. **2024-03-02 and 2024-05-18** were live sessions with normal settlement, but very short: about 1 h 45 min in two
   blocks, with 5% futures operating ranges. Treat them as trading days for expiry and day-count purposes, but they are
   not normal days for intraday volatility or volume studies.
3. **2024-01-20** became a full regular session. The original DR-switch format was withdrawn the day before.
4. **2019-10-21** is sourced from the MSD circular (NSE/MSD/42319), which names F&O explicitly. The circular index has no
   FAOP-numbered circular for this date. A clearing-side circular (NCL/CMPT/42344, "Trading Holiday on Oct 21, 2019 -
   F&O") also exists but was not downloaded.
5. Two source URLs are `.zip` files (FAOP57286, FAOP60337), because NSE published them only as zips; the `.pdf` URL
   returns 404. Each zip contains the circular PDF, which was read.
6. **Not covered:** commodity segment evening sessions, currency derivatives, and partial-day halts such as the
   24 Feb 2021 outage (trading halted, then extended to 17:00; the bhavcopy exists, so it counts as a normal session
   here).

## TWSE closures (`twse_closures.csv`, story A17f)

Read by `fno/global_cues/market_closures.py` for part B of A17e (`global-cues preopen`): a listed weekday is
`market closed` for `taiex` and no request is sent. Columns `date,kind,description,source_url,sha256`; kinds:
- `covers`: one row per year the file is complete for (1 Jan of that year), with the SHA-256 of TWSE's holiday file
  (`https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule`) it was copied from. A year without it is not
  used: part B alerts "taiex: TWSE calendar has no <year>" (and, from 1 Dec, "... has no <next year> yet").
- `holiday`: TWSE's published weekday closures, copied by hand from that file. Its rows naming a first or last
  "交易日" (trading day) are trading days; settlement-only days ("市場無交易") are closures.
- `unscheduled`: a closure announced late (a typhoon day), with its own source.

Each new year: save TWSE's file as `tests/fixtures/twse/holiday_schedule_<year>.json`, add the `covers` row with its
SHA-256 and the year's `holiday` rows; `tests/global_cues/test_twse_closures.py` fails until the rows equal the parser's
reading of that file. 2026: fetched 24 Oct 2026, 27 rows, 18 weekday closures; 23 Oct 2026 added as `unscheduled`
(Typhoon Champi: TWSE's 5-second statistics for that day answer "no data").
