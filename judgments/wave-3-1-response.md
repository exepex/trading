# Builder's response to wave 3, round 1 (and wave 2 round 2 minors)

| # | Fix | Evidence |
|---|---|---|
| 1 | `prioritise` under the schedule's lock (shared with next_request/record); skips failing or refused sources (a refusal pause now also marks the source as failing); never earlier than 60 s (or the source's cache time) after its last request; never later than already due | fno/live/news/poll_schedule.py; `test_prioritise_never_breaks_a_limit` |
| 2 | `PriceWatch` class: a failing feed backs off 20 s doubling to 15 min and is reported once; unpriced symbols logged once a day | fno/live/price_watch.py; `test_a_failing_price_feed_backs_off_and_is_reported_once` |
| 3 | On a shock on a held name: cached chains of that name are dropped (`Provider.forget`, implemented by `CachedProvider`) and an extra review runs without moving the regular schedule | runner `_watch_prices_if_due`, `_review`; `test_a_shock_on_a_held_name_re_checks_open_trades_at_once_on_a_fresh_chain` |
| 4 | Backtester applies the desk's re-entry (30 min) and post-loss (45 min) pauses per name; disclaimer lists what is not modelled; re-run: 219 trades, -Rs 1.95 lakh (docs and log updated) | fno/backtest/simulator.py `Cooldowns`; `test_no_new_trade_within_the_re_entry_or_loss_pause`; reports/backtest-2026-10-12.md |
| 5 | services.py builders `build_clock`, `build_exit_policy` (config exit days), `build_view_builder`, `build_move_check`, `build_backtester` used by the desk, the backtest and calibrate | fno/live/services.py, fno/backtest/cli.py, fno/backtest/calibration.py |
| 6 | Stock strikes on NSE-like steps by price band | fno/backtest/option_model.py |
| 7 | Report prints sessions and unfinished trades; disclaimer covers the 0.2 grading filter, unknown holidays and the 8% sigma floor | fno/backtest/report.py |
| 8 | Priority sources from NSE_SOURCE/BSE_SOURCE/MARKETAUX_SOURCE; Groww check via `GrowwProvider.name` | runner.py, services.py |
| 9 | groww-check prints missing symbols with the raw answer keys and survives a failed price call | fno/providers/groww_check.py |
| 10 | Tests: prioritise, GrowwLivePrices batching, price-feed failure, no Groww -> no price watch, no look-ahead, pauses | tests/live/test_shock.py, tests/live/test_news_fixes.py, tests/test_backtest.py |
| 11 | Documented: the 20 s cadence waits for a running scan | docs/WAVES.md |
| W2 minor 1 | WAVES W2.2 text gives the measured call/put ranges | docs/WAVES.md |
| W2 minor 2 | `CALENDAR_DAYS_PER_TRADING_DAY` in constants; one `build_move_check` for desk and calibrate (configured take-profit) | |
| W2 minor 3 | calibrate prints "no data" and exits 1 when every source failed; `--range` limited to 5d/1mo/60d | fno/backtest/calibration.py |
| W2 minor 4 | calibrate output recorded in conversations/2026-10-12.md; NOT_MEASURABLE wording covers option sensitivity | |
