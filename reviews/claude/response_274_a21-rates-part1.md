# Response 274: A21 part 1, RBI rates capture (builder's claims)

Story `docs/stories/A21-rates-first-seen.md` (text PASS, judge 355 addendum 1). Branch `story/a21-rates-code`, built on
O10's branch (`story/o10-capture-health`) for `CaptureErrorLog`, as the orchestrator directed; it rebases onto `main`
once O10 lands. Part 2 (announcements) waits for A16's `ObserverGroup`. Builder session 01XFXpbkyixX7SuXeQCp5EnX.
Labels: **strong evidence**, **some evidence**, **reasoning only**.

## Criteria (part 1)

| # | Criterion | Code | Tests |
|---|---|---|---|
| 1 | The 14 Oct 2026 release: 2026-10-14, 2026-2027/1325, 5.7281 / 6.2896 / 6.4891 | `fno/rates/pages.py` `parse_tbill_release` | `tests/rates/test_pages.py::test_the_14_october_release` |
| 2 | Home page: repo 5.50, 91-day 5.7281 | `pages.py` `parse_current_rates` | `test_the_home_page_box` |
| 3 | A changed layout or a refused page: the field named, one alert, one O10 row, no table row | `pages.py`, `capture.py` `_step`, `_finish` | `test_a_changed_*_layout_names_the_field`, `test_capture.py::test_a_refused_page_and_a_changed_layout_*`, `test_the_list_keeps_only_the_exact_title` |
| 4 | `RatesAsOf` never looks ahead: at the cutoff, ±1 s, no rows | `as_of.py` | `test_checks.py::test_as_of_never_looks_ahead` |
| 5 | A second run adds nothing; a changed repo rate adds one row and one information line | `capture.py` `_repo`, `rows.py` | `test_a_second_run_adds_nothing_*`, `test_no_change_notice_without_its_row` |
| 6 | Staleness: 8 days clean, 9 stale; 48 h clean, 48 h + 1 s stale; no table not stale | `checks.py` | `test_an_auction_8_days_old_*`, `test_a_home_read_48_hours_old_*`, `test_a_week_later_*`, `test_an_unreadable_home_page_never_counts_as_a_read` |
| 7 | Disagreement and the 24 h grace rule (23 h 59 min, 24 h, neither) | `checks.py` `disagreement` | `test_the_release_before_is_accepted_*`, `test_a_figure_matching_neither_*`, `test_a_disagreement_is_one_o10_row_and_one_alert` |
| 13 | Every page and the table write-once in Drive (O9) with receipts; no data file committed | `capture.py` `_read`, `_write`; `wiring.py` | `test_a_first_run_adds_the_release_*` (3 pages, 1 part, 4 receipts), `test_a_drive_conflict_is_a_named_store_failure` |
| 14 | `rates-daily.yml` watched by O10, only the Drive and #fno-desk secrets, one alert line on failure | `.github/workflows/rates-daily.yml`, `capture-watch.yml` | `tests/rates/test_workflow.py`, `tests/health/test_capture_watch_workflow.py` |
| 15 | No A12, A19, G13, S6, C2 or C4 file changed | (diff) | full suite |

Also covered: first-seen is the response's arrival, not the request time (judge 355 addendum 1):
`test_first_seen_is_the_arrival_of_the_response`. An unreadable history stops the run before any fetch:
`test_an_unreadable_history_stops_before_fetching_anything`. A release that failed once is retried while a newer one is
kept: `test_a_release_that_failed_once_is_retried_*`.

## Broken-code proof (quality rule 4)

Each mutation below was applied alone. `pytest tests/rates` failed every time, so all 14 were caught.
1. Loose title match.
2. 8-day rule `<=` changed to `<`.
3. 48 h rule `<=` changed to `<`.
4. 24 h grace `<` changed to `<=`.
5. As-of `<=` changed to `<`.
6. Clock read before the request.
7. Repo dedupe removed.
8. History stop removed.
9. Retry rule changed back to "newer than the newest".
10. Unreadable page stored under the normal name.
11. Notice kept when the table write fails.
12. Only the first O10 row of a run kept.
13. Layout error without the field name.
14. Workflow push failure exiting 0.

## Builder self-review (quality rule 3)

One independent review agent read the diff. Its findings and what I did:
- **Blocking: a failed receipts push went unnoticed, and the next run would re-record values with later times.**
  Fixed: the workflow now commits the receipts and the O10 rows in one step and exits 1 if the push fails, so
  capture-watch records and alerts. The CLI no longer commits. The risk itself stays as a Known limit: a receipt that
  never reaches `main` lets the next run record again, but now never silently.
- **A failed older release was never retried.** Fixed: the rule is "listed, not recorded, newer than the first
  recorded".
- **An unreadable home page reset the 48 h clock.** Fixed: a page is parsed before it is stored, and one that does not
  parse is stored as `_unreadable`, which never counts as a read.
- **The change notice was posted when its row was not written.** Fixed.
- **Missing tests for the arrival time, the end-to-end disagreement, the retry and the Drive conflict.** Added.
- **`--as-of` without an offset raised TypeError.** It is now refused with a message.
- **The table path differed from the text.** The text now says `rates/table/...`, the code's path.
- **One O10 row per kind hid the step.** Changed to one row per failure (step and kind).

## Real output (quality rule 6) and a first live run (rule 8)

`python -m fno rates capture --dry-run` on 16 Oct 2026 at 18:04 IST, in this session. It used RBI's live pages and the
committed code, with a local folder standing in for Drive (`work/rates-dry-run/`, git-ignored). Nothing was posted or
committed. Output:

```
added: tbill_91d_cutoff 5.7281% (2026-10-14, first seen 2026-10-16T18:04:54.611372+05:30)
added: tbill_182d_cutoff 6.2896% (2026-10-14, first seen 2026-10-16T18:04:54.611372+05:30)
added: tbill_364d_cutoff 6.4891% (2026-10-14, first seen 2026-10-16T18:04:54.611372+05:30)
added: policy_repo 5.50% (2026-10-16, first seen 2026-10-16T18:04:51.192977+05:30)
```

A second run three seconds later added nothing (exit 0). Its stored pages and table part:

```
data/rates/rbi/2026/10/16/180451_home.html
data/rates/rbi/2026/10/16/180452_list.html
data/rates/rbi/2026/10/16/180454_release_63803.html
data/rates/rbi/2026/10/16/180457_home.html
data/rates/rbi/2026/10/16/180457_list.html
data/rates/table/2026/10/2026-10-16.20261016T123448Z-c9b77f.csv
```

Table part:

```
rate,value_date,value_pct,release_no,source_url,source_sha256,first_seen_at,provenance,note
tbill_91d_cutoff,2026-10-14,5.7281,2026-2027/1325,https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63803,4bed29d7...,2026-10-16T18:04:54.611372+05:30,live,prid=63803
policy_repo,2026-10-16,5.50,,https://www.rbi.org.in/,285ab726...,2026-10-16T18:04:51.192977+05:30,live,as shown by RBI's home page
```

(the 182-day and 364-day rows are as above with 6.2896 and 6.4891). The live Drive run is the workflow's first run
after the merge (rule 8, the orchestrator's step). I did not run it here, because it writes to the owner's Drive and
posts to #fno-desk.

## Known limits

- A receipt whose push fails means the next run records again with a later time. The run fails loudly; it does not
  repair itself (reasoning only).
- GitHub's crons start up to about 5 h late (judge 351). That only delays the first-seen time, never falsifies it.
- The home page gives no effective date for the repo rate; its row is dated by first sight. An MPC change is
  effective the same day (judge 355 note).
- Part 2 (announcements) is not in this round.
