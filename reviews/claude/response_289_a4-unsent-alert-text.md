# Response 289: the 3 pm quote commands print an unsent alert with its text (builder's claims)

Branch `story/a4-unsent-alert-text` (lane 1, judge D). A fix, no new story: O2's end-to-end outage days (orchestrator,
16 and 21 Oct) found that when Slack is down a 3 pm quote command printed only "alert NOT sent: <reason>", without
the alert's text, so the routine (told to post "alert NOT sent" lines) could not post it, and a "raw quote file NOT
saved to Drive" alert was lost. One builder agreed: the O1/O2 builder (014zYLf18PgCzR7YoHs1X5Dp) held it as a
fallback. Builder session 01MKtUHByHsR9cNwaP5KhFYH. Register row on main (4dfae31a).

## Root cause and fix

`fno/quotes/cli.py` `record_today` and `fno/quotes/indices_cli.py` `record_indices` did `print(alerts.send(text))`:
the sender returns only its outcome, so an unsent alert's text was printed nowhere. **Strong evidence** (the code, and
the new tests fail on the old code).

| File | Change |
|---|---|
| `fno/quotes/cli.py` | `cmd_quotes` builds the command's sender once as O1's `ReportedAlerts(build_alert_sender())` (`fno/daily/alerts.py`, unchanged): an unsent alert prints "alert NOT sent: <reason> \| <text>". Used by `record`, `record --source nse`, `record --window` and `record-indices` |
| `fno/alerts/output.py` (new) | `announce(alerts, text)`: prints a sent alert's outcome only, so no bare "alert NOT sent" line is left beside the reported one (shared by the three commands below) |
| `fno/quotes/cli.py`, `indices_cli.py` | every `print(alerts.send(...))` (4 in `record_today`, 2 in `record_indices`) becomes `announce(...)` |
| `tests/quotes/test_unsent_alert_text.py` (new) | through `cmd_quotes` with Slack down: the raw-file alert, the calendar stop and the index alert each print one line "alert NOT sent: <reason> \| <full text>"; with Slack up, the outcome once and no unsent line |

**My other child commands checked:** `record`, `record --source nse` and `record --window` all go through
`record_today`; `record-indices` through `record_indices`; `report` and `compare` send no alert. Covered.

**Also fixed, at the orchestrator's request (21 Oct; A16's builder told, A12 has no owner):** the same bare
`print(alerts.send(...))` in `fno/intraday/cli.py` (the stop, the silent-heartbeat alert, the calendar stop; the
dry-run sender is wrapped too) and `fno/filings/runs_cli.py` `_archive` (the Drive sign-in refusal and the run line).
Tests: `tests/alerts/test_unsent_alert_lines.py` (A16's calendar stop and A12's sign-in refusal with Slack down;
`announce` with Slack up and down).

**A privacy issue the fix would have opened, closed here (O1's file, its builder told):** the daily run keeps a
child's last 10 printed lines in the committed run record (`journal/runs/<date>.json`, public). Once an unsent alert
prints its text, the 3 pm raw-file alert's Drive error text (meant for Slack only: it can hold the private folder ID,
A4b's rule) could reach that record. `fno/daily/processes.py` `ChildProcess.lines()` now keeps no "alert NOT sent"
line; the routine still gets every one through `report`. Test: a child whose last line is such an alert with a fake
folder ID: reported, not kept (fails without the fix). Effect on O2's unmerged branch (its "already alerted" check
reads `lines`) sent to its builder.

**Still bare elsewhere (out of this fix's scope, phase-1 freeze; for their owners):** `fno/storage/librarian_cli.py:101`
(every librarian command, A12's day lists included), and outcome-only prints in `fno/forecast_scoring/cli.py`,
`fno/pipeline/cli.py`, `fno/budget/cli.py`, `fno/ai/cli.py`, `fno/nse_margins/`, `fno/fo_masters/job.py`.

## Broken-code proof

Each planted, the new tests run, the file restored: 4 of 4 caught for the quotes, 3 of 3 for A16 and A12 (A16's heartbeat sender not wrapped, A12's archive sender not wrapped, A16's calendar stop back to a bare print), and the run-record test fails without the `processes.py` change. Quotes (no `ReportedAlerts`
wrapper; `announce` printing every outcome, which leaves the bare line; `announce` printing nothing; the index alert
back to a bare print).

## O2's strict xfail

`tests/e2e/test_outages.py` (slack_down=True, `CHILD_ALERT_TEXT_GAP`) is on O2's branch, not on main. Once both are
on main it XPASSes and, being strict, fails the suite: the marker is removed then (O2's builder asked whether they do it
or I do).

## Gates

On the final branch (main 967eb7fd merged in): `ruff check`, `ruff format --check` (1,460 files), `check_imports` (1,550),
`check_records`, `forecast_live_golden` "unchanged": all clean. `pytest -n auto`: 8,111 passed, 2 failed, 18 xfailed.
The 2 failures fail identically on main itself (a fresh worktree of origin/main), in areas this fix does not touch:
`tests/forecast_scoring_v4/test_g7_series.py::test_v1_reads_only_the_a16_rows_it_is_given` and
`tests/market_read_models/test_forecast_history_page.py::test_every_point_is_the_reports_own_scored_count_and_mean_brier`
(reported to the orchestrator).
