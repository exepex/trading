# Builder's response to wave 1, round 1

| # | Fix | Evidence |
|---|---|---|
| 1 | `price_to_close` catches any `live_quote` failure and falls back to the chain price (FILL_LAST_PRICE, logged); the picker turns a failed or missing live quote into a refusal (`require_bid_ask`, default true); close_all and the trim close every trade they can and always save | tests/live/test_fills.py `test_a_failing_live_quote_never_stops_a_stop_loss_kill_switch_or_trim`, `test_no_live_bid_ask_means_no_purchase_unless_allowed` |
| 2 | `journal.close_value` replaced by `price_to_close` returning `ClosePrice(value, orders, spot, fill_source)`; `exit_fill_source` is set only by `finalise_trade`; expiry uses `FILL_INTRINSIC` | `test_exits_are_priced_at_the_live_bid_and_say_so_only_when_closed`, tests/test_journal.py `test_expired_trades_say_they_were_settled_at_intrinsic_value` |
| 3 | IV readings kept per (symbol, IST day); `flush` writes each under its own day once; the runner also flushes at the start of each day (a day that ended early, e.g. kill switch) | `test_a_day_that_ends_early_is_stored_under_its_own_day_once`, `test_runner_stores_one_snapshot_after_the_close` |
| 4 | Chain with its own book: used as is, live quote never asked, for the picker and exits | `test_a_chain_with_its_own_book_is_used_as_is` |
| 5 | Shadow journal reset; scan-once without shadow desk; shadow fills only while TRADING; conftest guard against tests writing repo data (it caught a real leak: the end-to-end helper's store wrote into data/live/events; fixed by pointing results and news to tmp) | `test_no_shadow_fills_outside_the_session`, tests/conftest.py |
| 6 | trade-stats converts to IST and buckets a missing expiry as "unknown" | tests/live/test_trade_stats.py |
| 7 | `rank` only uses days within `lookback_days` | fno/live/learning/iv_history.py |
| 8 | No entry without a real bid/ask (`require_bid_ask`) | see 1 |
| 9 | README trade-stats; SAFEGUARDS family limit, bid/ask, IV rank, sideways, move check, news guard and exit; DATA_SOURCES Groww bid/ask | docs |
