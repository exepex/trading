# Response 103: story A17, global cues (builder's claims for the judge)

Branch `story/a17-global-cues` (from `origin/main` 032665a). Lane 1 (new story; outside services Treasury, EIA, RBI,
FBIL and Drive).

## Verdict first

Built and run for real on 15 Oct 2026 (06:15 IST), **without the previous US closes**:

| Table | What it holds | Source |
|---|---|---|
| `us10y` | 4,950 days, 2007 to 14 Oct 2026 | US Treasury |
| `brent` | 4,992 days, 2007 to 6 Oct 2026 | EIA, weekly release |
| `usdinr_rbi` | 3,871 days | RBI; no data from 10 Jul 2018 to 11 Apr 2022 except 24 Jul 2018 |
| `usdinr_fbil` | 1,981 days, 10 Jul 2018 to 7 Oct 2026 | FBIL; its public site trails by a week |

RBI and FBIL agree on all 1,086 dates they share.

**S&P 500 and Nasdaq 100 are blocked: source terms.**
- S&P DJI answered 403.
- Nasdaq's terms of use forbid "any process, whether automated or manual, to capture data or content".
- Cboe's disclaimer forbids storing its index values "in a database or retrieval system" without permission.
- FRED, besides being refused by this environment's network policy, carries S&P's notice "Reproduction of S&P 500 in
  any form is prohibited except with the prior written permission of S&P Dow Jones Indices LLC" on SP500, and the tag
  "Copyrighted: Pre-Approval Required" on NASDAQ100. I read those FRED pages through a web fetch.

Every row before 15 Oct 2026 is labelled `backfilled`. Only two rows are `live`: the 14 Oct 2026 US 10-year and the
14 Oct 2026 RBI rate. All Brent rows are `backfilled`, because EIA publishes weekly.

## Per criterion (story A17, `docs/stories/A-data-foundation.md`)

| # | Criterion | Code | Tests | Evidence |
|---|---|---|---|---|
| 1 | Publisher, URL, time zone, publication lag and terms per cue, each with a label; a forbidden source is named and an alternative proposed | each source class (`treasury_source.py`, `other_sources.py`: `publisher`, `date_zone`, `max_age_days`, URL constants); README table "Sources, time zones, lags and terms" and "Blocked: source terms" | `test_sources.py` (each publisher's layout), `test_every_request_names_a_file_and_an_https_url` | URLs, time zones and lags: **strong** (observed 15 Oct). EIA public domain: **strong** (quoted). Treasury public domain: **some** (federal-works law, page not quoted). RBI: **reasoning only**. FBIL: **reasoning only, a risk** (the terms page could not be fetched; FBIL licenses its benchmarks). Nasdaq, Cboe and FRED notices: **strong** (quoted) |
| 2 | `first_seen_at` on every row; `backfilled` vs `live` by the first NSE open after the value date | `table.py` `provenance` and `merge`; `collector.py` fetch time taken after the last download; `wiring.py` `next_nse_session` (stops after the calendar's last year) | `test_live_only_when_seen_before_the_first_nse_open...` (09:14 live, 09:15 backfilled, weekend to Monday); `test_the_fetch_time_is_taken_after_the_last_download`; `test_after_the_calendars_last_year_the_label_is_never_guessed`; `test_committed::test_backfilled_rows_are_exactly_those_seen_after_their_first_nse_open` (recomputes every committed label) | strong |
| 3 | As-of rule: only a value dated before the India date; a US Monday holiday gives Tuesday the Friday value; live use needs `first_seen_at` before 09:15 IST | `as_of.py` `value_for` | `test_as_of_checks.py` (holiday, same date, live vs research, empty) | strong. Real sample below: 20 Jan 2026, after the US Martin Luther King Day holiday on 19 Jan, gives the US 10-year of Friday 16 Jan |
| 4 | Raw copies in Drive, never overwritten, logged; a change logged as a revision; a late value logged, never inserted; append-only | `collector.py` (one copy per fetch, `<HHMMSS>_<name>`); `snapshot_log.py`; `table.py` `merge` (both files checked before writing) | `test_collector_table.py` (archive and log; changed and late logged; logged once; prefix); `test_a_broken_revisions_file_writes_no_table_row_either`; empty and unterminated files | strong |
| 5 | Gaps listed, never filled; RBI and FBIL compared on shared dates; stale cues named | `checks.py`; `job.py` `CueChecks`, `_run_cue` (STALE) | `test_as_of_checks.py` (gaps, repeats, RBI/FBIL); `test_committed` (committed checks reproduce; no difference); stale test with its 7-day boundary | strong |
| 6 | A failed download, unreadable file, empty answer or refused save writes nothing to the table and is named; Drive or setup failure is one line and exit 1 | `collector.py` (`UNREADABLE`, `SAVE_FAILURES`, no values at all); sources' layout guards (Brent 5 cells, RBI row count, RBI `__VIEWSTATE`, FBIL USD rows); `job.py` `RUN_STOPPERS` (earlier cues still reported); `cli.py` `STOPPING_FAILURES` and a reversed range | `test_one_failed_download_or_unreadable_file...`; `test_failures.py` (save failure after 1 of 2 copies, empty answers, the new year's empty Treasury file, layout guards, stop midway, CLI) | strong |
| 7 | Rows equal the archived copies; `first_seen_at` not before its copy; `provenance` recomputed; duplicates, order and empty tables named | `verify.py`; `cli.py` `_verify` | `test_committed::test_recomputing_from_the_copies_finds_a_planted_change`; `test_verify_names_a_wrong_label...`; `test_verify_names_a_date_held_twice...`; the empty-table test | strong. Real `verify` against Drive: "every cue row equals the archived copy it names", exit 0 (values, timing and labels) |
| 8 | Interfaces with one composition root in CLAUDE.md; no frozen file; gates | `GlobalCueSource` (`source.py`); concrete classes only in `fno/global_cues/wiring.py`; CLAUDE.md +1 line; `fno/cli.py` +2 lines; `fno/storage/README.md` +1 row | full suite | strong: no FREEZE-listed file touched (`fno/constants.py`, `fno/composition.py`, `fno/research_data/*` untouched) |

The gap list (quality rule 2) is in the story text: every requirement of REPLAN's A17, design 2.1's row, outputs and
failure modes, and the orchestrator's brief, mapped to a criterion or marked out with a reason.

One point for the owner: design 2.1 asks for cues "as of 15:00", while the brief asks "known before 09:15". The 09:15
answer is safe for a 15:00 decision, but it leaves out the same day's USD/INR rate, published at about 13:00-13:30 IST.
A 15:00 variant is out until a forecast needs it.

## Builder self-review (quality rule 3)

Two independent review agents ran on the diff, one for correctness and one for silent failures.

### Fixed, each with a test

**Data integrity and labels:**
- The fetch time was taken *before* the downloads, so a slow fetch could be labelled `live` when it was not. It is now
  taken after the last download.
- The calendar fallback silently used "next day" for years after the calendar's last one. A run now stops and names
  the missing year.
- `merge` could write table rows and then lose their revision when `revisions.csv` was broken. Both files are now
  checked before either is written.

**Failures that were silent or tracebacks:**
- A failure in a later cue hid the lines of cues already written. They are now reported, and the checks still run.
- A malformed table, a Drive failure or missing settings gave a traceback. Each now gives one STOPPED line and exit 1.
- A save failure part-way through a cue's copies escaped. It is now named and the table is left alone.
- A publisher serving old data stayed silent. It is now named STALE, with a limit per source.
- On 1-5 January the new year's empty Treasury file failed the whole cue. That file is now valid, and only a cue with
  no values at all fails.

**Layout guards on the sources:**
- A Brent week row with a styled or missing cell would have shifted dates. It is now refused; `&nbsp;` counts as blank.
- An RBI row in another markup would have been dropped silently. It is now refused by counting rows.
- A changed RBI form with no `__VIEWSTATE` was blamed on the answer. It is now named as a changed form.
- An FBIL layout change looked like "no values". It is now named.

**Verify and checks:**
- `verify` now also checks `first_seen_at` and `provenance`, a date held twice, rows out of order, and each empty cue
  table.
- The RBI/FBIL comparison was full of the 895 dates inside RBI's hole. It now covers shared dates only and prints how
  many were compared.
- A reversed `--from`/`--to` is refused.
- The RBI dates in the docs are corrected (to 9 Jul 2018, plus 24 Jul).

### Not changed, by design or as a limit

- **A late value is never inserted** (A11's rule). The README now says so plainly.
- **A copy saved but its log row failing** (OSError on the repository disk) is not handled beyond the STOPPED line.
- **One copy per fetch.** Daily runs would store about 1 MB a day in Drive: the RBI and FBIL answers cover the asked
  range, and EIA's page is the whole history.

## Broken-code proof (quality rule 4)

The same planting script as for A15 ran with bytecode writing off. **29 of 29 mutations are caught**, each by a named
test.

| Criterion | Mutations |
|---|---|
| C1 | RBI form without `__VIEWSTATE` |
| C2 | live at exactly 09:15; the fetch time taken before the downloads; the calendar guessed after its last year |
| C3 | a same-date value used; live use ignoring `first_seen_at` |
| C4 | a held value rewritten; a late value inserted; a revision logged twice; the revisions file not checked first |
| C5 | weekday gaps, repeats or RBI/FBIL differences hidden |
| C6 | download failure unnamed; unreadable file saved; save failure escaping; no values accepted; empty answer accepted; zero rate accepted; shifted Brent week; dropped RBI row; silent FBIL layout change; stale cue not flagged; CLI letting a setup failure escape; reversed range |
| C7 | value difference, wrong label or empty cue table ignored by `verify` |

The first run let "reversed range" survive: the test passed only because Drive settings were missing. The test now
checks the message, and the mutation is caught.

## Cases per criterion (quality rule 5)

- **Good:** each publisher's real layout.
- **Bad:** error pages, other layouts, refusals, broken files.
- **Boundary:**
  - 09:14 vs 09:15;
  - 7 days old vs 8 (stale);
  - the new year's empty Treasury file;
  - a calendar year after the calendar's last one;
  - EIA's year-end week;
  - exactly 5 Brent cells.
- **Empty:** an empty answer, an empty table file, no rows for `value_for`, an empty cue table for `verify`.

## Real output (quality rule 6)

Made by the committed code from the committed tables on 15 Oct 2026. These are public reference data, not trade
output.

Rows and the copies they came from:
```
us10y      2026-10-14,5.19,bec74a6c…,2026-10-15T06:15:03+05:30,live
           copy us-treasury/rates/par-yield-curve/2026/10/15/061503_daily-treasury-rates_2026.csv
brent      2026-10-06,125.44,3089d97e…,2026-10-15T06:15:52+05:30,backfilled
           copy eia/petroleum/brent-spot-daily/2026/10/15/061552_RBRTED.htm
usdinr_rbi 2026-10-14,95.0317,177c7f49…,2026-10-15T06:16:11+05:30,live
           copy rbi/currency/reference-rate/2026/10/15/061611_reference-rate-usd_20070101_20261015.html
usdinr_fbil 2026-10-07,96.623,9640e871…,2026-10-15T06:16:31+05:30,backfilled
           copy fbil/currency/reference-rate/2026/10/15/061631_reference-rates_20180710_20261015.json
```

`value_for` on two India dates:
```
2026-10-15 us10y      live_only -> 2026-10-14 5.19
2026-10-15 usdinr_rbi live_only -> 2026-10-14 95.0317
2026-10-15 brent      live_only -> 2026-10-06 125.44
2026-01-20 us10y      research  -> 2026-01-16 4.24   (US Monday 19 Jan holiday: Friday's value)
2026-01-20 us10y      live_only -> None              (history was not seen live)
```

Brent's 6 Oct value is usable live on 15 Oct because it was first seen before 09:15 that day. It stays `backfilled`,
because it was not seen before its first open, on 7 Oct.

`python -m fno global-cues check`:
```
gaps: brent repeated_previous_value 55, brent weekday_without_value 164, us10y repeated_previous_value 365, us10y weekday_without_value 212, usdinr_fbil weekday_without_value 171, usdinr_rbi repeated_previous_value 44, usdinr_rbi weekday_without_value 1291
USD/INR RBI against FBIL: 1086 dates compared, no difference
```

`python -m fno global-cues verify` against Drive: `every cue row equals the archived copy it names`, exit 0.

## Things the owner must decide or know

1. **US closes:** the options are in the README.
   - Ask S&P DJI (its permissions address is on FRED's SP500 page) and Nasdaq for permission, then use FRED: allow `fred.stlouisfed.org` or
     add a FRED API key, and keep the values in Drive only.
   - Or go without US closes.
   - Or use a feed the owner already licenses.
2. **Four files in Drive** come from Nasdaq and Cboe, fetched once before their terms were read. None of them is in
   this repository. Delete or keep them; deleting needs the owner's OK.
   - `raw/cboe/indices/spx-history/2026/10/15/061445_spx-history.json`
   - `raw/cboe/indices/spx-history/2026/10/15/061718_spx-history.json`
   - `raw/nasdaq/indices/ndx-history/2026/10/15/061454_ndx-history_20070101_20261015.json`
   - `raw/nasdaq/indices/ndx-history/2026/10/15/061722_ndx-history_20260912_20261015.json`
3. **FBIL in a public repository** (`usdinr_fbil.csv`) may need FBIL's permission (reasoning only). It only fills
   RBI's 2018-2022 hole; it can be moved to Drive only if the owner prefers.
4. **The public repository holds derived tables** of RBI, EIA and Treasury data. EIA and Treasury are public domain;
   for RBI, reasoning only.
5. **Brent is never timely.** EIA publishes weekly, so for live use Brent is up to 9 days old. A timely Brent needs a
   licensed or exchange source: MCX answered 403 here, and ICE's terms were not checked.

## What the judge should test hardest

1. `python -m fno global-cues verify` with the Drive settings: values, `first_seen_at` against the copy's fetch time,
   and labels.
2. Read the Nasdaq, Cboe and FRED notices yourself, and EIA's reuse page.
3. Run `value_for` on India dates after a US holiday (20 Jan 2026, 27 May 2025) and on a date whose value was seen after 09:15.
4. Plant a changed past value and a late value in a fake run; the table must not change and both must be logged.
5. Confirm no S&P 500 or Nasdaq 100 data is in the repository:
   `git ls-files | grep -i -E "spx|ndx|sp500|nasdaq"` should list only code and tests.

---

## Addendum 1: the owner's decision on US closes (a927390) and both cutoffs (15 Oct 2026)

This addendum replaces the "blocked: source terms" status above. The quotes of the terms stay; the owner has decided
to use the sources anyway.

### What changed

1. **Private cues: S&P 500 (Cboe) and Nasdaq 100 (Nasdaq)**, under owner decision a927390.
   - **Storage.** Raw files and derived values are in the owner's Drive only. Rows, revisions and gaps are write-once
     CSV parts under `derived/global-cues/<cue>/{rows,revisions,checks}` (`row_log.py` `DrivePartsRowLog`, behind a
     new `RowLog` interface; the public cues keep `CsvRowLog` in the repository).
   - **What the repository holds:** code, the schema, the README and the copy logs only (path, URL, SHA-256, size).
     The tests use made-up values labelled fake.
   - **Downloads.** At most one download a day: a second one on the same IST date is skipped and said so
     (`collector.py`, `once_a_day`).
   - **History start.** The four copies kept in Drive were adopted at their own fetch times (`global-cues adopt`).
     sp500 has 4,977 days to 14 Oct 2026; nasdaq100 has 5,059 days to 13 Oct 2026. No value is quoted in this file.
   - **Display.** Nothing on the card or the dashboard until the owner approves. That is an open item, and no display
     code exists.
2. **Two cutoffs: 09:15 and 15:00.**
   - `value_for(rows, india_day, cutoff, live_only, available_at)` takes the cutoff explicitly (`OPEN`, `DECISION`).
   - Each source states when a value is published (`available_at`), using the time zone with daylight saving:
     - US closes: 16:00 US Eastern;
     - Treasury: 18:00 US Eastern, an assumption;
     - reference rate: 13:30 IST;
     - Brent: by the end of the 10th day after its date, an assumption.
   - The research view uses those rules. The live view (`live_only`) uses only the observed `first_seen_at` against
     the cutoff.
   - The `provenance` column keeps the 09:15 meaning. I chose not to add a column, so the committed tables stay
     append-only.
3. **FBIL's terms found** in its site's page code: "[FBIL does not authorize commercial use of the data available in
   its website without written permission]", plus an "as is" disclaimer. This use is personal and non-commercial:
   some evidence that it is allowed.

### Evidence (dates and counts only)

- **Adoption output:**
  - `sp500: 4977 dates added`, then `0 dates added` for the second, identical copy;
  - `nasdaq100: 5059 dates added`, then `0 dates added` for the one-month copy.
  - Copy logs: `research/data/manifests/global-cues/sp500.csv` and `nasdaq100.csv`, two rows each.
- **`verify`** against Drive, all six cues including the Drive-only tables: "every cue row equals the archived copy it
  names".
- **`value_for` on real tables (dates only):**

| India date | Cue | 09:15 | 15:00 |
|---|---|---|---|
| 15 Oct 2026 | sp500 | 14 Oct (live) | 14 Oct |
| 15 Oct 2026 | nasdaq100 | 13 Oct (Nasdaq lacked 14 Oct) | 13 Oct |
| 20 Jan 2026 | sp500 (after the US holiday of 19 Jan) | 16 Jan | 16 Jan |
| 20 Jan 2026 | usdinr_rbi | 19 Jan | 20 Jan |

### Self-review of the new parts (quality rule 3)

One independent agent reviewed the new parts. It found no route by which a private value is in git: no sp500 or
nasdaq100 table on any branch, none in `revisions.csv` or `gaps.csv`, and the fixtures are fake. Its findings, each
checked in the code:

**Fixed, each with a test:**
1. **An unfinished US close could have become a permanent `live` row.** A file read during the US session may hold
   the day's price so far. Now any value not final when its file was fetched is dropped
   (`collection.final_values`; test with a fetch at 21:00 IST).
2. **The Brent rule was too early** (date + 8 days, 00:00 IST, while EIA posts in US daytime). It is now the end of
   the 10th day. The live view no longer uses the rule at all; it relies on the observed `first_seen_at`.
3. **A failed table write on the day of the download could not be finished that day.** The once-a-day skip would
   have turned every `live` label into `backfilled` the next day. A second run the same day now reads the day's
   archived copy again (`archived_copies.reuse_today`; test).
4. **A failure while writing the checks hid every cue's result line.** Now it is reported below them (test).
5. **The private gaps log only grew** (each run appended the full list again, and cleared gaps never cleared). Each
   run now writes a full snapshot, and the newest is current (`DriveSnapshots`; test).
6. **`verify` printed private values** in its difference lines. It now prints "values differ (private cue: values
   never printed)" (test).
7. **Bad `adopt` paths** gave a traceback or a misleading message. A path that is not a copy path, sits in another
   cue's folder or has no matching request is now named (tests).
8. **Every read of a Drive table listed the folder again.** The Drive table now keeps its rows in step with its own
   appends, so it is read once per run, and a lagging Drive listing cannot show an old "last" date.

**Documented, not changed:**
- A failed or refused download saved nothing and may be retried that day.
- The once-a-day rule reads the copy log in the repository, so a run must start from a checkout that has pulled.
- Adopt the full-history copy first. A Nasdaq copy's `--from`/`--to` must match its name.
- `check` with the Drive settings writes the private gaps to Drive.

### Broken-code proof (quality rule 4)

**42 of 42 mutations caught.**
- **26 from the first set** still apply. Three of the first set no longer matched the refactored code and were
  replaced: the revisions log not checked first, and a same-date US close used in the research view.
- **14 new**, all caught:
  - an unfinished close kept;
  - a second download the same day;
  - an adopted copy logged twice;
  - adopt from another cue's folder;
  - private gaps written to the repository;
  - private gaps not written to Drive;
  - verify printing a private value;
  - the Drive table cache out of step;
  - an old gap snapshot read as current;
  - the US close time without its time zone;
  - the reference rate counted at the open;
  - a non-strict cutoff;
  - the live view using the rule;
  - a checks failure hiding the cue lines.
- Three of the 14 first survived because their tests were weak (they did not count log rows, used a path whose name
  also failed, and had no failing checks). I strengthened the tests, and all three are now caught.

### Cases (quality rule 5)

- **Boundaries:**
  - exactly at the publication time (not usable) and one minute later (usable);
  - US summer and winter time;
  - the same day's reference rate at 09:15 (no) and 15:00 (yes);
  - a fetch during the US session;
  - a second run the same day, and the next day.
- **Empty:**
  - a cleared gap snapshot;
  - a private table with no rows.

### Gates

- `tests/global_cues`: 58 passed.
- Real `check` and `verify` against Drive pass.

The full-suite count is in the commit report.
