# Builder's response to wave 3, round 2

| # | Fix | Evidence |
|---|---|---|
| N1 (should fix) | `_down_reported = report(...)`; `report` typed `Callable[[datetime, str], bool]`; a rate-limited alert is retried on the next failure | fno/live/price_watch.py; `test_the_feed_down_alert_is_not_lost_to_the_rate_limit` (slot taken for 15 min, 3 h of failure: exactly 1 alert) |
| N2 | The raw missing-symbol diagnostic in groww-check is guarded; its error becomes a line | fno/providers/groww_check.py |
| N3 | DISCLAIMER and WAVES W3.2 say the post-loss pause is applied per name, not account-wide as on the desk | fno/backtest/report.py, docs/WAVES.md |
| N4 | `SOURCE_CONFIG_KEYS` keyed on `NSE_SOURCE` / `BSE_SOURCE` | fno/live/services.py |
| N5 | Rally case: all trades win, gaps after a win are at least 30 minutes (measured: exactly 30) | tests/test_backtest.py `test_no_new_trade_within_the_re_entry_pause_after_a_win` |
| N6 | Once-a-day missing-price log keyed on the IST date | fno/live/price_watch.py |
