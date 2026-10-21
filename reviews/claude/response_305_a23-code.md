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
