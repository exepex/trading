# Response 116: story A17b, guards before any consumer reads a global cue (builder's claims for the judge)

Branch `story/a17b-cue-guards`. Story text passed at 464f5ff (judge 116 addendum 1). Lane 1 (new story; Drive).

## Verdict first

Every reading now says how old it is, which date it should be, and whether it is that date. The real tables give
(dates, ages and statuses only; never a private value). Every cell is the research view (`live_only=False`) unless it
says otherwise:

| India date, cutoff | sp500 | nasdaq100 | us10y | brent | usdinr_rbi | usdinr_fbil |
|---|---|---|---|---|---|---|
| 15 Oct 2026, 09:15 | 14 Oct, current | 13 Oct, **behind** (expected 14 Oct) | 14 Oct, current | 2 Oct, behind (13 days; research view, which assumes Brent is out 10 days after its date; the live view gives 6 Oct, behind, 9 days: the copy fetched at 06:15 IST held it) | 14 Oct, current | 7 Oct, behind (8 days) |
| 15 Oct 2026, 15:00 | 14 Oct, current | 13 Oct, behind | 14 Oct, current | 2 Oct, behind | 14 Oct, **behind** (expected 15 Oct, not yet fetched) | 7 Oct, behind |
| 27 Nov 2026, 09:15 | 14 Oct, **stale** (44 days; expected 25 Nov, Thanksgiving skipped) | stale | stale | stale | stale | stale |
| 31 Oct 2012, 09:15 | 26 Oct, **current** at 5 days (Sandy) | 26 Oct, current | 29 Oct, behind (expected 30 Oct) | 19 Oct, behind | 30 Oct, current | none (FBIL from 2018) |
| 20 Jan 2026, 09:15 | 16 Jan, current (MLK 19 Jan) | 16 Jan, current | 16 Jan, **behind** (weekday rule expects 19 Jan) | 9 Jan, behind | 19 Jan, current | 19 Jan, current |

What the owner should know:
- **The US 10-year reads `behind` after every US bond holiday** (MLK above, Columbus Day, Veterans Day). That is the
  stated simplification (no SIFMA calendar): it never claims `current` wrongly, but a consumer that refuses `behind`
  loses the 10-year on those days. Reasoning only that this is acceptable; a sourced SIFMA calendar would fix it.
- **FBIL reads `behind` almost always** (its site trails a week), as the story says.
- The 15 Oct 15:00 RBI `behind` is real: the 15 Oct rate is published about 13:30 IST and no run fetched it.

## Per criterion (story A17b, `docs/stories/A-data-foundation.md`)

| # | Criterion | Code | Tests | Evidence |
|---|---|---|---|---|
| 1 | `reading_for` gives row, age, expected date and status in the order none, current, ahead, behind, stale | `fno/global_cues/reading.py` (`CueReading`, `reading_for`, `expected_date`, `CueReader`); `wiring.build_reader`; `holiday_rows` on `GlobalCueSource` (True for Nasdaq) | `test_readings.py`: nasdaq 15 Oct `behind`; 27 Nov `stale` with 25 Nov expected; Sandy `current` at 5 days; RBI on an NSE holiday `ahead` (and same-day 15:00 `current`); us10y Good Friday `current` and never `ahead` over 2023; age 4 `behind`, 5 `stale`; Brent only behind/stale/none (edge 16/17); empty `none`; Nasdaq holiday row skipped (sp500 keeps it, `ahead`); live view; muhurat day `ahead` for USD/INR | strong (tests and the real table above) |
| 2 | US calendar: MLK, Good Friday, Thanksgiving week, Juneteenth before/after 2022, weekend observance, each closure, US summer/winter time at both cutoffs; CI test against `us_trading_dates.csv`; us10y missing weekdays never sessions | `cue_calendars.py` (`CueCalendar`, `NyseCalendar`, `WeekdayCalendar`, `NseSessionCalendar`); `us_market_closures.csv` (5 rows, https sources); `trading_dates.py` + `check_files.py` (written by `global-cues check` with Drive) | `test_us_calendar.py`: each case; summer close 01:30 IST vs winter 02:30 at a 01:45 cutoff; every weekday 2007-01-01 to 2026-10-14 vs the 4,977 S&P dates: **0 mismatches**; the 83 Nasdaq-only dates are all non-sessions; every us10y missing weekday (212) is in `gaps.csv` and reads `behind`/`stale` with that weekday expected; the writer's output (dates and 0/1 flags only) | strong for 2007-2026 (checked against the archived dates). **Reasoning only for 2027 on**: computed rules, not NYSE's published list |
| 3 | `live` never uses a muhurat session as an open; committed labels recompute | `wiring.next_nse_session` skips `muhurat` | `test_guards.py`: value of 31 Oct 2024, muhurat 1 Nov: next open 4 Nov, seen 1 Nov 19:00 is `live`; `test_committed` recomputes every committed label (unchanged) | strong |
| 4 | `adopt` refuses a copy created before its path time or more than 10 minutes after, and a store that cannot give the time | `fno/storage/creation_times.py` (`CreationTimes`, `GoogleDriveCreationTimes`: Drive `createdTime`); `archived_copies.py` (`ADOPT_WINDOW`) | `test_guards.py`: at, +9 s and +10 min accepted; -1 s and +10 min 1 s refused naming both times, nothing logged; None and no store refused | strong. Real check: the four adopted copies were created 8.5, 4.1, 8.3 and 6.0 seconds after their path times: all within the window |
| 5 | Attempts logged (time and outcome only) and capped: a third failed attempt is the last; a saved copy ends the day | `attempt_log.py` (`MAX_ATTEMPTS` 3; a `started` row before each download, the outcome after); `collector.py`; `research/data/manifests/global-cues/attempts/<cue>.csv` | `test_guards.py`: 3 failures then refused (downloads stay 3), rows logged, header `attempted_at,outcome`, next IST day allowed; failure then save then reuse (2 downloads); no value in the log; a non-once-a-day cue logs nothing; a crash logged `stopped` and counted; a broken log lets no download by; 3 `started` rows without outcomes (a killed run) cap the day; a UTC clock counted on the IST date | strong. Limit: the log is a repository file, so a failed run must commit and push it too (README) |
| 6 | Judge 100's A15 minors | `fno/vix_history/wiring.py` (`_committed_fingerprints`, no `lambda`, no `noqa`); `research/data/vix/README.md` muhurat wording | `test_sweep.py::test_the_sweep_command_exits_1_when_an_original_is_missing` (and 0 when nothing is missing) | strong. The README now says evening until 2024 (18:15-19:15 IST 2019-2023, 18:00-19:00 in 2024), 13:45-14:45 IST on 21 Oct 2025; the 2017 and 2018 calendar rows give no times |
| 7 | FBIL decision in the data README as an open owner item | `research/data/global-cues/README.md` "Open owner item: FBIL in a public repository" | n/a | the orchestrator's decision quoted as such |
| 8 | Quality rules | below | | |

Also done (judge 116 addendum 1 minor): Nasdaq's rows on non-NYSE dates are skipped by readings. Real count: 83 rows
on non-NYSE dates since 2007, 82 repeating the previous close.

## Choices to check

- **One interface, not `UsSessionCalendar`.** The story names a `UsSessionCalendar` interface; the code has one
  `CueCalendar` interface (`is_session(day)`) with three implementations (NYSE, weekdays, NSE sessions), because the
  US 10-year and USD/INR need the same seam. A US-only interface would duplicate it. Say if the name matters.
- **Creation times sit behind their own interface** (`CreationTimes`), not inside `RawFileStore`: only adopt needs
  them, and the other stores (local folder, Drive area) would have to answer "unknown" otherwise. A store without one
  refuses adopt, as the story asks.
- **Age limits also tighten the run's STALE line**: US closes and us10y 4 days (were 7), RBI 5 (was 7). A run on the
  Tuesday after a US Monday holiday still passes (Friday is 4 days old).
- **`NseSessionCalendar` raises after the NSE calendar's last year** (as the `live` rule does): a USD/INR reading
  from 1 Jan 2027 stops and names the year until NSE's 2027 circular is added (tested; README says add it in
  December 2026).
- **Before 2017 the first NSE open is now the next weekday**, not the next day: `next_nse_session` became
  `NseSessionCalendar.next_open`, so the "regular or special, not muhurat" rule lives once (judge's DRY rule). Every
  row before 2017 was fetched in 2026, so every label is unchanged (`test_committed` recomputes them all).
- **Owner items opened by this story**: `us_trading_dates.csv` makes the S&P 500's weekday gaps derivable from public
  dates (the owner's rule kept private gaps in Drive); FBIL in a public repository (kept, the orchestrator's decision).

## Quality rules

- **Gap list (rule 2):** in the story text, judge 116 rows included; the Nasdaq holiday-rows minor is added above.
- **Self-review (rule 3):** two independent agents (a criterion-by-criterion review and an adversarial tester); their
  findings and what was done are in the self-review section below.
- **Broken-code proof (rule 4):** 44 planted mutations, all caught: 30 across criteria 1-6, then 5 and 9 for the two
  rounds of self-review fixes. The first 30, each run against `tests/global_cues` and
  `tests/vix_history`: **30 of 30 caught** after three tests were added for the first-run survivors (the Saturday New
  Year rule, a muhurat day in the USD/INR calendar, the trading-dates writer's Nasdaq column). A first run passed two
  test paths as one argument and so "caught" everything; it was found and re-run, and is not counted.
- **Cases (rule 5):** good, bad, boundary and empty per criterion (table above).
- **Real output (rule 6):** the table at the top, from the real Drive and repository tables; the adopt times; the
  trading-date counts. Dates, ages and statuses only. Re-run after the self-review fixes: identical output (the
  adopt check now through `GoogleDriveStore.metadata`).
- Gates on the merged tree: `python -m pytest -q` (3,876 passed on the merged tree with main), `ruff check fno tests
  tools`, `ruff format --check`, `python tools/check_imports.py`, code size (largest changed file 151 lines). No frozen
  file changed.

## Self-review: findings and what was done

Adversarial tester:

| # | Finding | Decision and evidence |
|---|---|---|
| 1 | An unexpected failure (parser crash, copy-log write error), a broken attempts file or a killed run left no attempt row: no cap | **Accepted, fixed**: a `started` row before the download (fails closed if the log is broken), the outcome in a `finally` (`stopped` for a crash); 4 tests; mutations caught |
| 2 | The cap's memory is a repository file | **Accepted as a stated limit**: README says to commit and push the logs after failed runs too; no scheduled job runs this yet |
| 3 | A corrupt attempts file raises | Kept: it fails closed (nothing downloaded), with Python's error |
| 4 | A row dated after the India date read `ahead` (usable) in the live view | **Accepted, fixed**: such rows are never usable; test |
| 5 | An unscheduled closure not yet listed makes Nasdaq's repeated row `current` | **Rejected as a code change**: the repeated value is the true last close, so the number used is right; the CI test names the missing closure at the next `check` with Drive. Coupling Nasdaq's reading to the S&P table costs more than this rare case buys. Stated in the README |
| 6 | A non-IST clock split the IST day | **Accepted, fixed** (times stored and counted in IST); test |
| 7 | A partial save on a multi-file once-a-day source is reused as the whole day | Kept: latent (both private sources are one file each); A17 behaviour |
| 8 | Adopt accepts odd path shapes; a Drive clock behind ours refuses a genuine copy | Kept: needs a planted path, or fails closed; A17 parsing |
| 9 | Readings past the NSE calendar raise | By design; now tested and in the README |

Criterion reviewer:

| # | Finding | Decision and evidence |
|---|---|---|
| 1 | `CueReading`'s `repr` printed the row with a private value | **Accepted, fixed**: `repr` hides the row; test |
| 2 | USD/INR readings raise from 2027, untested and unstated | **Accepted**: test and README |
| 3 | `us_trading_dates.csv` makes private gaps derivable | **Accepted**: stated in the README and `check_files.py`, opened as an owner item |
| 4 | The Drive creation-time adapter had no test and reached into the store's session | **Accepted, fixed**: `GoogleDriveStore.metadata`; adapter tests (area prefix, `Z` parsing, absent file or time) |
| 5 | A hard kill bypasses the cap | **Accepted, fixed** (the `started` row, above) |
| 6 | The muhurat rule sat in the composition root, duplicating `NseSessionCalendar` | **Accepted, fixed**: `NseSessionCalendar.next_open` |
| 7 | Cue names retyped as strings | **Accepted, fixed** in `wiring.py` and `trading_dates.py` (from the sources' `cue`) |
| 8 | A calendar with no session in 40 days silently fell back to age only | **Accepted, fixed**: it raises; test |
| 9 | Unlisted closure; the 83rd Nasdaq holiday row unexplained | README: the 83rd is 1 Jan 2007, the table's first row (nothing before it to compare) |
| 10 | `build_reader` for a private cue without Drive gave a bare KeyError | **Accepted, fixed**: the error names the Drive settings; test |
| 11 | Closure sources are second-hand | **Partly**: they meet "https source", and the archived S&P table has no row on any of the 5 dates; primary NYSE notices would be better and were not searched for in this round. Left as a minor |
| 12 | The run's STALE disagrees with readings on closure replays | **Accepted**: stated in the README; consumers use the reading |
| 13 | `UsSessionCalendar` name; creation times outside the store interface | Explained under "Choices to check", for the judge |
| 14 | Diff base; README long line; `positive()` printed a private close's text in errors | **Accepted**: the judge's diff base is `git merge-base origin/main HEAD`; line wrapped; private sources' errors name the date only (test) |

## Addendum 1: A17c minors (orchestrator, after judge 116 addendum 2)

Branch `story/a17c-minors` from `main` af96586.

1. **`expected_date` boundary test** (`tests/global_cues/test_us_calendar.py`): the expected date turns over strictly
   after the close is out. At 01:30:00 IST in US summer time (16:00 EDT) the previous close is not yet expected, and at
   01:30:01 it is; the same at 02:30 in winter (EST); across the US clock change of 8 Mar 2026. Broken-code proof:
   `<` changed to `<=` is caught. Strong.
2. **Sandy's closure source**: both rows now cite NYSE Euronext's own release "NYSE Euronext announces trading volumes
   for October 2012" (13 Nov 2012) on euronext.com: "The industry decision to close the U.S. markets for two trading
   days due to Hurricane Sandy". The same release is in ICE's investor-relations archive as a PDF. Limit: it says "two
   trading days" without naming them. NYSE Euronext's 28 Oct 2012 statement ("will close its markets on Monday,
   Oct. 29, 2012 and pending confirmation on Tuesday, Oct. 30, 2012") names the days, but I found it only reprinted by
   news sites, not on NYSE's or ICE's own pages. The archived S&P 500 table has no row on 29 or 30 Oct 2012, which pins
   the two days. Strong evidence together; the dates alone rest on the reprint and the archived table.
3. **Brent row of the real-output table**: it now names its view. Research view: 2 Oct, 13 days, `behind` (it assumes
   Brent is out 10 days after its date). Live view: 6 Oct, 9 days, `behind` (the copy fetched at 06:15 IST on 15 Oct
   held it). Both re-run on the public table today. Every other cell is the research view, now said above the table.
