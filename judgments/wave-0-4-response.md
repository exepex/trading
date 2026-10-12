# Builder's response to wave 0, round 4

| # | Fix | Evidence |
|---|---|---|
| N16 (should fix) | Rupee "hits" split by what it hits: "hits ... low(s)" is a fall, "hits ... high/peak/highest/strongest" a rise | fno/live/news/classifier.py `RUPEE_HITS_LOW`, `RUPEE_HITS_HIGH`; 5 new headlines in tests/live/test_news_fixes.py |
| N14 | The dead-watcher check runs before the reference retry in each tick, so the retry cannot take the alert slot | runner `tick`; `test_a_failing_reference_never_takes_the_dead_watcher_alert` (fails on the old order) |
| N15 | Kill bookkeeping (`_kill_reported`, `_last_kill_attempt`) moved out of DayState into the runner; reset only when the switch is released, so midnight neither re-runs close_all nor re-sends the alert | runner `tick`, `_handle_kill_switch`; `test_a_kill_switch_day_alerts_once_across_midnight_and_still_sends_its_summary` |
| N17a | A kill-switch day still sends its day summary after the close | same test |
| N17b | A reference outage is alerted once per outage (retried until sent), and only on a trading day before the close; other failures are logged. Retries every 5 minutes continue | runner `_load_reference_if_needed`, `_market_day_ahead`; `test_a_reference_outage_is_reported_once_and_never_overnight` (24 h from Monday 16:00: 1 alert, on Tuesday morning) |
