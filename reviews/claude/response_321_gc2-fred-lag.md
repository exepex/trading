# Response 321: GC2, FRED's lag and values against our global-cue sources (measurement before any change)

A16b/A17 builder (session 01MBnbVU4sundxNjs5u4xCsP), 22 Oct 2026, for the orchestrator. Story GC2 (owner, DESK_DECISIONS
22 Oct row: "simplify the global market module with Fred"). Nothing has been replaced yet. No values appear here (owner
rule 50a79a43), only dates, times and counts.

## How it was measured

- **The key is not in this session.** `FNO_FRED_API_KEY` exists only as a GitHub Actions secret (DESK_DECISIONS row
  261). So nothing here used the API.
- **Values:** FRED's public, no-key CSV (`fred.stlouisfed.org/graph/fredgraph.csv`), 1 Aug to 22 Oct. It was compared
  date by date with a fresh download from each of our current source classes. Nothing went to Drive and nothing was
  committed.
- **Timing:** each series page's "Updated" time, read at 15:30 IST on 22 Oct. That is **one day** of timing evidence.
  ALFRED's vintages (the date each value first appeared) are not publicly downloadable: the CSV ignores
  `vintage_date`, and the ALFRED download answers 404/502. They need the API key.
- **Our side's timing:** the global-cues runs on 22 Oct landed at 06:12 and 07:02 IST.

## Values (strong evidence: 53-57 dates each)

| FRED series | Our source | Common dates | Equal | Only one side |
|---|---|---|---|---|
| DGS10 | Treasury par yield (us10y) | 55 | 55 exact | ours has 21 Oct, FRED not yet |
| DCOILBRENTEU | EIA Brent spot (brent) | 56 | 56 exact | none |
| SP500 | Cboe SPX (sp500) | 57 | 57 exact | none |
| NASDAQ100 | Nasdaq NDX (nasdaq100) | 57 | 57 exact | none |
| NIKKEI225 | Nikkei's official file (nikkei225) | 53 | 53 exact | ours has 22 Oct (FRED gets it in the evening) |
| VIXCLS | Cboe VIX (vix_us) | 57 | 57 exact | ours has 21 Oct, FRED not yet |
| DEXINUS | RBI reference rate | 50 | **0 exact**, 37 within 0.1%, worst 0.34% | ours 5, FRED 3 |
| DEXINUS | FBIL reference rate | 49 | **0 exact**, 36 within 0.1%, worst 0.34% | ours 2, FRED 4 |

- FRED is a mirror for DGS10 (Treasury's own numbers), Brent (EIA's) and the two US indexes.
- DEXINUS is a different number: the Fed's noon New York buying rate (H.10), not RBI's or FBIL's Mumbai reference rate.
  It is also weekly: on 22 Oct its last value was 16 Oct, updated Monday 19 Oct.

## Timing (some evidence: one day of each)

| Series | FRED updated (IST) | Value date it brought | Ours at the 06:12 IST run | At the 08:50 edition on 22 Oct |
|---|---|---|---|---|
| DGS10 | 22 Oct 01:59 | 20 Oct | Treasury: 21 Oct | **FRED one day behind** Treasury |
| DCOILBRENTEU | 21 Oct 22:48 | 20 Oct | EIA: 20 Oct | tie: both have 20 Oct (EIA is FRED's source) |
| SP500 | 22 Oct 05:31 | 21 Oct | Cboe: 21 Oct | tie, but FRED is only just in time for the first run (the 03:41 cron lands 05:30-06:40) |
| NASDAQ100 | 22 Oct 09:07 | 21 Oct | Nasdaq: 20 Oct (21 Oct by 15:30) | **neither in time**; only Yahoo's NDX had 21 Oct (by 06:12) |
| NASDAQCOM | 22 Oct 09:08 | 21 Oct | (not collected) | not in time |
| NIKKEI225 | 21 Oct 17:32 | 21 Oct (same day) | Nikkei: 21 Oct | tie: both in time |
| VIXCLS | 21 Oct 19:08 | 20 Oct | Cboe: 21 Oct | **FRED one day behind** Cboe |
| DEXINUS | 20 Oct 01:46 (Monday) | 16 Oct | RBI: 21 Oct | days behind, and a different rate |

The Nasdaq-100 comparison is weaker than it looks:
- Nasdaq's own file did not have 21 Oct at 07:02 IST, and had it by 15:30 IST.
- FRED had it at 09:07 IST.
- Which of the two came first is unknown.

## What this means (reasoning on the evidence above)

1. **US 10-year: keep Treasury.** FRED is one day later, the same lag every day: H.15 posts the previous business day's
   rate in the US afternoon. Strong reasoning, one day of data.
2. **USD/INR: keep RBI and FBIL.** FRED's DEXINUS is the wrong rate (noon New York, up to 0.34% apart) and weekly.
   Strong evidence.
3. **Brent: FRED can replace EIA.** The values are equal, they cover the same day, and a CSV/JSON answer is simpler than
   parsing EIA's HTML table. Neither gives yesterday's Brent by 08:50; that lag is EIA's own, and FRED does not change
   it. Values strong, timing one day.
4. **S&P 500: FRED is equal, but on time only by about 35 minutes for the first morning run.** Replacing Cboe gains
   little code and risks a later value on a slow FRED day. My recommendation is to keep Cboe unless 5 or more days show
   FRED before 05:00 IST. Reasoning, one day.
5. **Nasdaq-100: FRED does not fix M1's lag for the 08:50 edition.** It arrived at 09:07 IST. Yahoo's NDX, already
   read through IndexReader since A17e, is what has the previous session by 06:12 IST. FRED could replace the
   `api.nasdaq.com` scraper if a week shows it no later than Nasdaq's own file. Some evidence.
6. **Nikkei 225: FRED can replace Nikkei's own file, and it adds history.** FRED's NIKKEI225 is equal on all 53 dates
   and posts the same day (17:32 IST). It also reaches back before 2023, where Nikkei's own file starts, so the official
   series would cover 2019-2022 too (977 FRED dates, 4 Jan 2019 to 10 Jan 2023; today only Yahoo covers
   them). Values strong, timing one day.
7. **US VIX: keep Cboe.** VIXCLS is equal but one day behind Cboe's own file. One day of data.
8. **Other Asian and European indexes:** I found no FRED series for them. Not checked one by one: KOSPI, Hang Seng, ASX
   200, STI, FTSE 100, DAX and Euro Stoxx 50. They stay on the official sources plus Yahoo.

**Honest size of the simplification:**
- If Brent and Nikkei move, GC2 removes two scrapers: EIA's HTML table and Nikkei's file, with its row-length checks.
  It adds one FRED adapter and the key, which the workflow has and the routine side does not. The net code saving is
  small. The real gain is Nikkei's history before 2023 from an official mirror.
- If S&P 500 and Nasdaq-100 move too, it removes `us_index_sources.py` (84 lines) as well. That needs a week of timing
  evidence first.
- FRED does not make the module simpler where it matters most (Asia, Europe, the rupee).

## What is needed to finish the measurement

- **30 days of first-appearance dates (ALFRED vintages):** the FRED API with the key. The owner can add
  `FNO_FRED_API_KEY` to this cloud environment's settings (environment menu, Edit, as an environment variable or
  network secret); a new session reads it. These are date-level only. For DGS10 a date is decisive: a value first seen
  on the next US day can never reach 08:50 IST. For SP500 and Nasdaq-100 the time of day matters, and a date cannot
  give it.
- **The time of day for SP500 and NASDAQ100:** the series pages' "Updated" time read on 5 or more mornings (a plain
  public read, once a day, around 05:00-09:30 IST). This needs either a session alive on those mornings or a step in
  the existing global-cues workflow that logs FRED's "last_updated" (lane 1, judge F).

**Proposal:** add the key to the environment, run the ALFRED measurement for all six series, and log the morning
"Updated" times until Mon 26 Oct. Then decide Brent, Nikkei, S&P 500 and Nasdaq-100 on that evidence. Keep
Treasury, Cboe's VIX and RBI/FBIL now.

## Addendum 1 (22 Oct, after the orchestrator's decision): nothing to build

The orchestrator's decision:
1. Nikkei's 2019-2022 history from FRED, marked as source FRED.
2. Brent from FRED, only if it lets the EIA scraper be **deleted**.

Neither holds up once the code is read. No code was committed. The branch `story/gc2-fred` was deleted unpushed.

**Brent: the EIA parser cannot be deleted (strong evidence, from the code).**
- `global-cues verify` (`fno/global_cues/verify.py`, `_values`) recomputes every table row by parsing the archived copy
  the row names, with the cue's current source.
- All 4,992 recorded Brent rows name EIA's HTML copies. With FRED as the source, every one of them would fail "fails the
  publisher's check".
- Keeping them verifiable means keeping EIA's parser. The only other way is rewriting recorded rows, which loses their
  first-seen times and is never done.
- So both would stay, and by the decision's own condition Brent is skipped.

**Nikkei: a FRED cue would add code, and the need is met without it.**
- The same `verify` fact rules out replacing Nikkei's own source: its 928 rows name Nikkei's CSV copies.
- A history-only FRED source of the same cue ends in Jan 2023, so every run would mark it STALE. A separate live
  `nikkei225_fred` cue would need IndexReader changes. Both add code, the opposite of GC2's aim.
- The real value of FRED's history was checking Yahoo's 2019-2022 Nikkei, which IndexReader uses before Nikkei's own
  file starts. That needs one comparison, not a cue. **Done today:**
  - FRED and Yahoo have 976 common dates from 4 Jan 2019 to 10 Jan 2023: **all 976 exact**, none over 0.1%.
  - One date is FRED-only: 1 Oct 2020, the day the Tokyo Stock Exchange halted all trading after a system failure.
    FRED repeats 30 Sep's close there, a value that never traded. Yahoo correctly has no row.
  - So Yahoo's 2019-2022 Nikkei is verified against Nikkei's own figures as mirrored by FRED. FRED is the weaker of the
    two on a halted day.

**GC2's conclusion, for the story:** FRED is exact but mostly late. Adopting it for Brent or Nikkei would keep the old
parsers, because every recorded row must stay verifiable from its own archived copy. So it saves no code. FRED's one
use, checking Yahoo's 2019-2022 Nikkei, is done here as a one-off comparison. All 976 dates are equal; FRED's 1 Oct 2020
is a repeated value on a halted day. The global-cue sources stay as they are.

**A general lesson, from the code:** any source swap in this module keeps the old parser for as long as recorded rows
name its copies. A swap only removes code for a cue with no recorded rows.
