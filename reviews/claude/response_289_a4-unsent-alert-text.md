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
| `fno/quotes/alert_output.py` (new) | `announce(alerts, text)`: prints a sent alert's outcome only, so no bare "alert NOT sent" line is left beside the reported one |
| `fno/quotes/cli.py`, `indices_cli.py` | every `print(alerts.send(...))` (4 in `record_today`, 2 in `record_indices`) becomes `announce(...)` |
| `tests/quotes/test_unsent_alert_text.py` (new) | through `cmd_quotes` with Slack down: the raw-file alert, the calendar stop and the index alert each print one line "alert NOT sent: <reason> \| <full text>"; with Slack up, the outcome once and no unsent line |

**My other child commands checked:** `record`, `record --source nse` and `record --window` all go through
`record_today`; `record-indices` through `record_indices`; `report` and `compare` send no alert. Covered.

**Not mine, for their owners (seen while checking):** the same bare `print(alerts.send(...))` is in
`fno/intraday/cli.py:71, 94, 104` (A16, G10/A16 builder) and `fno/filings/runs_cli.py:86, 100` (A12). Only an issue if
those run as the daily run's children with Slack down.

## Broken-code proof

Each planted, `tests/quotes/test_unsent_alert_text.py` run, file restored: 4 of 4 caught (no `ReportedAlerts`
wrapper; `announce` printing every outcome, which leaves the bare line; `announce` printing nothing; the index alert
back to a bare print).

## O2's strict xfail

`tests/e2e/test_outages.py` (slack_down=True, `CHILD_ALERT_TEXT_GAP`) is on O2's branch, not on main. Once both are
on main it XPASSes and, being strict, fails the suite: the marker is removed then (O2's builder asked whether they do it
or I do).

## Gates

On the branch merged with main 967eb7fd: `ruff check`, `ruff format --check` (1,460 files), `check_imports` (1,550),
`check_records`, `forecast_live_golden` "unchanged": all clean. `pytest -n auto`: 8,105 passed, 2 failed, 18 xfailed.
The 2 failures fail identically on main itself (a fresh worktree of origin/main), in areas this fix does not touch:
`tests/forecast_scoring_v4/test_g7_series.py::test_v1_reads_only_the_a16_rows_it_is_given` and
`tests/market_read_models/test_forecast_history_page.py::test_every_point_is_the_reports_own_scored_count_and_mean_brier`
(reported to the orchestrator).
