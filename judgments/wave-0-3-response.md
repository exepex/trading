# Builder's response to waves 0 and 1, round 3

| # | Fix | Evidence |
|---|---|---|
| N10 | A new date always starts a new day state (and flushes IV readings); reference data loads separately (`_load_reference_if_needed`, retried every 5 min); scans need reference data loaded today (`_reference_today`) | `test_a_new_day_with_failing_reference_data_scans_nothing_but_still_sends_its_summary` |
| N11 | `_report_problem` returns whether it sent; the dead-watcher flag is set only once the alert really went out | `test_the_dead_watcher_alert_is_not_lost_to_the_rate_limit` |
| N12 | Kill-switch retries only during market phases (no prices overnight) | `_handle_kill_switch(now, phase)` |
| N13 | Start-up `_start_day_if_needed` wrapped again | `run_forever` |
| classifier | "up/down" count as moves after a cost or the rupee; the tail ("3%", "20 paise", "to a 16-year high", "from record low") goes with the matched phrase; "recovers" is a rise | 8 more cases in `test_headline_direction` (22 total) |
