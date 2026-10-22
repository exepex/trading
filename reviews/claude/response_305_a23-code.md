# Response 305: A23 code, FII/DII flow history (NSE participant volume, FII derivatives statistics, NSDL one-time)

Builder session_013u1Ac2N9eRQ8XCYPjwpaat, for Judge F. Branch `story/a23-flow-history`. Text:
`docs/stories/A23-flow-history.md` (judge 429 add. 1 PASS at fdc3b2b0; NSDL and xlrd added at 236389de from the owner's
answers, DESK_DECISIONS 195b3f0f, sent to you for a look).

## What is built

| Criterion | Where | Evidence |
|---|---|---|
| 1 Readers | `fno/research_data/fii_derivative_stats.py` (xlrd 2.0.2, pinned); participant volume through A8's `read_participant_oi` | 2019 layout (four groups, numbers as floats) and 2026 layout (per-index rows, numbers as text); title date, unknown rows, non-numbers, fractional contracts, short rows, empty, HTML and damaged bytes refused; per-index contracts must add up to their group within NSE's own rounding (2 contracts, A8's measure) (`tests/flow_history/test_readers.py`) |
| 2 Point in time | `fno/flow_history/availability.py`, `table.py` | evening file → next session; Friday → Monday; before a holiday → the session after it; a muhurat-only evening stepped over; written 09:15:00 at the next open is not rewritten, 09:15:01 is; no `Last-Modified` → rewritten (unknown); never the same day (`test_availability.py`, `test_table.py`) |
| 2b Rewritten share | the back-fill claims (below) | after the back-fill |
| 3 Back-fill | A9's librarian (`data-librarian participant-volume`, `fii-stats`), resumable, manifest rows | after your PASS (sequencing below) |
| 4 Daily | `.github/workflows/flow-history.yml` (21:30 IST, retry 07:15 IST), on capture-watch; O8 rows "A23 participant volume" and "A23 FII statistics" (`live_from` None), due 09:00 the next day | `test_workflow.py`; O8's boundary test (09:00:00 ok, 09:00:01 late) |
| 5 No value in the repository | manifests, receipts and the write-time logs (`research/data/flow_history/<name>_write_times.csv`: day, checked time, `Last-Modified`) only | values live in the Drive table `data/flows/history/<name>/` |
| 6 Real sample | first back-filled month and first daily run | after the back-fill |
| 7 NSDL | `fno/flow_history/nsdl.py`, `nsdl_backfill.py`, `python -m fno flows nsdl-backfill` | readers on the 2019 and 2026 layouts (rowspans, "Total" without a span, month/year totals and derivatives left out); pace ≥ 10 s between posts, one retry, a month failing twice listed and never tried again, resume, rows in the table, no value in printed lines, alerts or receipts (`test_nsdl.py`, `test_nsdl_backfill.py`); privacy test: only the flow-history package names the NSDL table (`test_privacy.py`) |

The derived table is long-form, one row per value: `session, dataset, last_modified, available_from, rewritten,
series, measure, value`. So a new index row in a later NSE file is one more series, never a new column. NSDL rows use
`session` = the reporting date (NSDL: the previous trading day's trades), `available_from` = the next session, and
`rewritten` = `publication_time_unknown`.

Both datasets join `DATED_SOURCES`, so A7's coverage check (criterion 4 of scope), A11's revision sweep (judge 429's
ask; the workflow runs it) and the NSE retry policy tests (now 26 classes) cover them.

## Real checks from this container (21-22 Oct 2026) [strong: direct reads]

- 24 sampled sessions, 3 a year (Jan, May, Sep), 2019 to Sep 2026, both files, through the production readers: all
  parse. One FII file, 12 Jan 2026, had index-option OI contracts 1 off its group total, which led to the 2-contract
  tolerance. FII statistics have per-index rows from May 2023 (8 rows), 10 from 2024 and 12 in Sep 2026.
- Day-level `Last-Modified` from the sample: most files were written on their own session day. Some were rewritten
  later: FII stats for 10 Jan 2019 on 6 Mar 2019 and for 10 May 2019 on 14 Aug 2019; participant volume for 10 Jan 2019
  on 17 Jan 2019 and for 11 Sep 2023 on 16 Sep 2023. The back-fill will give the full share (criterion 2b).
- NSDL: 3 form posts in all (2 Jan 2019, 15 Oct 2026, 30 Jun 2019, a Sunday, which works: 19 reporting dates, 190
  rows). The reader reads all three.

## Judge 429 add. 2's three asks

- Pacing test: `tests/flow_history/test_nsdl_backfill.py::test_one_post_per_month_at_least_10_s_apart_and_rows_in_the_table`
  and `::test_a_month_that_fails_twice_is_listed_and_never_tried_a_third_time` check that every gap between posts is
  at least 10 s, against the literal 10, not the constant; a mutant at 1 s is caught.
- No value in the repository, log or alert:
  `::test_the_command_prints_and_alerts_counts_and_months_only` checks every printed line, the alert and the
  committed receipts. After the real pass, a grep of the repository diff and the run's log for the pass's values goes
  in the addendum.
- The real post count and duration of the one back-fill: in the addendum after it runs.

## Choices beyond the text (the judge decides)

1. **Write times through A8's `LastWriteSweep` unchanged.** I give it a baseline below any write time, so it logs
   every day. A day whose write time could not be asked (NSE unreachable) waits for the next run rather than being
   entered as "unknown" forever, because the table is write-once. A day NSE serves without `Last-Modified` is entered
   as rewritten.
2. **O8's deadline is 09:00 the next calendar day**, not "the next session". It is stricter: a Friday file is due
   Saturday 09:00, which the 21:30 run and the 07:15 retry meet. It is the fifth health-owned deadline, and its test
   was updated.
3. **NSDL derivatives and the month/year totals are not kept.** The totals are sums of the days, and NSE's FII
   statistics already hold the derivatives.
4. **Command name `flows`** (`flows table`, `flows nsdl-backfill`), as the text names it.

## Sequencing after your PASS (no test exemption; orchestrator told)

The fingerprint test needs ≥ 250 manifest rows per dataset, so it fails on this branch until the back-fill (the one
expected failure; full suite otherwise 9,068 passed). After the PASS, I run from this container with the branch code:
`data-librarian participant-volume` and `fii-stats` (about 1,940 sessions each, about 35 minutes each at one request
a second), `flows table` for both, and `flows nsdl-backfill` (about 94 posts, at least 10 s apart, about 16 minutes).
The manifest rows and write-time logs are committed on this branch, then the merge goes through the full suite. The
claims addendum will carry criteria 2b, 3 and 6.

## Gates

`ruff check`, `ruff format --check`, `check_imports` and `check_records` are clean. Full suite: 9,068 passed, plus the
one expected fingerprint failure above. A23's tests: 60 in `tests/flow_history/`, plus O8's and the NSE retry
policy's. **Mutations: 13 of 13 caught.** Two survived at first: the "nothing new writes no part" test could not tell
an empty part from none, and the pacing test compared against the constant itself. Both tests are tightened. Every
file is under 350 lines.

## The owner's data rule (DESK_DECISIONS 50a79a43, after this round was written)

A source's redistribution terms no longer block a download for private research. Three guards stay: private Drive
only, never in the repository or a public place, with Slack showing only derived facts; no getting around logins,
CAPTCHAs or blocks; paced reads. The orchestrator also confirmed that the owner's private dashboard and Slack may show
it. I updated the text's scope 5, the NSDL docstrings and the privacy test's reason to that wording. Nothing in the
code changes: no NSDL value enters the repository or a log, and the privacy test still makes any new reader a judged
change. This also settles my earlier note on P8's dashboard figure, if the dashboard is private as the rule says.

## Addendum 1: the back-fill (judge 437 PASS; its merge condition)

All steps ran from this container on the judged branch code (446a18a9, then the two judged fixes cff14b5e/b5508fc5 and
28ce8c47), 21-22 Oct 2026. The pushes to main were refused by design while the branch differs from main, so every
manifest, write-time log and receipt is committed on this branch.

### Criterion 3: counts, first and last, gaps [strong: manifests and NSE's calendar]

| Dataset | Sessions archived | First, last | Calendar sessions | Gaps |
|---|---|---|---|---|
| participant volume | 1,934 | 2019-01-01, 2026-10-21 | 1,935 | 2019-03-18: sourced exception (NSE's file has fractional contracts, sixths) |
| FII statistics | 1,934 | 2019-01-01, 2026-10-21 | 1,935 | 2019-07-30: sourced exception (NSE serves an .xlsx under the .xls name; owner-approved xlrd reads only .xls; orchestrator: no openpyxl) |

Found and fixed on the way, each judged before use:
- 3 participant-volume files (15 Sep 2021, 14 and 18 Oct 2022) had stray unnamed rows. Unnamed rows are now ignored
  (judge 437 add. 1).
- The first table step crashed because the write-time log's folder did not exist in a fresh checkout. The sweep now
  creates it (28ce8c47).
- The first NSE job hit the container's 2-hour job limit during FII statistics (1,757 of 1,935). The librarian's
  resume path finished it: "1,757 already there and verified, 177 uploaded".

### Criterion 2b: rewritten count and share [strong: NSE's Last-Modified of every file]

| Dataset | Rewritten | By year (rewritten of sessions) | Session to available_from, rewritten days |
|---|---|---|---|
| participant volume | 104 of 1,934 (5.4%) | 2019: 94/244; 2020: 1; 2021: 3; 2022: 2; 2023: 1; 2024: 2; 2025: 1; 2026: 0 | median 21 days, max 367 |
| FII statistics | 164 of 1,934 (8.5%) | 2019: 144/244; 2020: 1; 2021: 3; 2022: 3; 2023: 2; 2024: 11; 2025: 0; 2026: 0 | median 53 days, max 163 |

Every archived session has a write time; none was entered as "unknown". For a study (statistician's view) [reasoning]:
2019's bytes are mostly later versions (39% and 59% rewritten), not what was public the next morning. Drop 2019's
rewritten rows or keep them labelled; from 2020 both series are clean point in time.

### Criterion 6: the first back-filled month (January 2019; counts only, the repository being public)

| Table (Drive, `data/flows/history/<name>/`) | All rows | Sessions | Jan 2019 | Jan 2019's dates |
|---|---|---|---|---|
| participant-volume | 108,304 (1,934 × 56) | 1,934 | 23 sessions, 1,288 rows, 28 series | all 23 rewritten (NSE rewrote them; 1 Jan available from 18 Jan) |
| fii-stats | 98,676 | 1,934 | 23 sessions, 552 rows, 4 series | all 23 rewritten (1 Jan available from 7 Mar 2019) |
| nsdl-fpi | 120,466 | 1,874 reporting dates | 23 dates, 943 rows, 11 series | `publication_time_unknown`; 1 Jan available from 2 Jan |

Every table part matched its receipt (Drive cache sync: 0 problems). The first daily run (flow-history.yml, 21:30
IST) happens after the merge and goes in addendum 2.

### NSDL, judge 429 add. 2's three asks

- Real post count and duration: 93 months (Jan 2019 to Sep 2026), 0 failed, 22:16:11 to 22:31:42 UTC (15 min 31 s).
  That is 93 gaps of 10 s, so no retries were needed; the code does not count posts, so the count is from the timing
  [some evidence].
- No value in the repository, the log or an alert: 3,860 distinct figures from three real answers (2019-01, 2023-06,
  2026-09) checked against the receipts commit (186 files, all under `receipts/data/`) and the run's log: 0 found.
- Pacing test: as listed above (literal 10 s; a 1 s mutant is caught).

### Gates on this branch after the back-fill

Full suite: **9,077 passed, 17 xfailed, with the fingerprint test green**. ruff, format, imports and record scan clean.
The merge to main follows your check (pull, full suite on the merged tree, check_numbers, push).
