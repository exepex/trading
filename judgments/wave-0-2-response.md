# Builder's response to waves 0 and 1, round 2

| # | Fix | Evidence |
|---|---|---|
| N1 | Kill switch: one alert, honest when trades stay open (`KILL_PARTIAL` names them); `close_all` retried every review interval while trades remain open; each retry reports the trades left open | fno/live/runner.py `_handle_kill_switch`, fno/live/alerts.py; test `test_kill_switch_keeps_retrying_a_trade_it_cannot_price` |
| N2 | Reference data is loaded before the day state changes; a failure keeps the previous state, alerts, and retries every 5 minutes; scans wait until reference data exists | `_start_day_if_needed`, `_scan_if_due`; test `test_a_failed_morning_reference_load_is_retried` |
| #6 | Cost and rupee phrases only when the move word directly follows the subject (optional "prices/futures/index", numbers or adverbs in between); "eases/cools/softens/retreats" count as falls for costs | fno/live/news/classifier.py; 5 judge headlines + 2 more in `test_headline_direction` (14 cases) |
| N4 | Each usage entry parsed in its own try; a damaged entry resets only that source | `test_a_damaged_usage_file_only_resets_that_source` |
| N5 | `closed_at` now stored with seconds; a zone-less release marker is read as IST | `test_a_loss_closed_seconds_after_a_release_counts` |
| N6 | SAFEGUARDS: automatic stop judges the current fall from the best point, restarts after `live resume`, retries unpriceable trades; go-live drawdown 10% of capital | docs/SAFEGUARDS.md |
| N7 | conftest compares new, changed and deleted files; `FNO_TESTS_BESIDE_LIVE_DESK=1` skips the guard when tests run beside a live desk | tests/conftest.py |
| N8 | Shadow-book news-exit errors are logged | `_review_shadow_book` |
| N9 | Test for the dead-watcher alert (once) | `test_a_dead_news_watcher_is_reported_once` |
