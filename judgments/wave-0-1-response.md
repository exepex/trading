# Builder's response to wave 0, round 1

| # | Fix | Evidence |
|---|---|---|
| 1 | Overnight trim prices each trade in its own try (skips and logs one that fails); `review_open_trades` saves in `finally` | fno/live/paper_desk.py `_trim_overnight_exposure`, `review_open_trades`; test `test_square_off_trim_with_a_broken_chain_still_saves_the_other_exits` |
| 2 | Adverse-news exit moved to its own class `AdverseNewsExit` (fno/live/news_exit.py) with a per-trade try returning errors; the runner records, alerts and runs the kill-switch check in `finally` | tests `test_a_failing_news_exit_never_loses_exits_already_made`, `test_one_trade_that_cannot_be_closed_does_not_stop_the_news_exit` |
| 3 | Marketaux request errors re-raised as `"Marketaux request failed: <ExceptionType>"` from None (no URL, no token) | `test_the_marketaux_token_never_appears_in_connection_errors` |
| 4 | Watcher: any fetch error is a source failure with back-off; a malformed item is skipped; `run_forever` survives any error (logs, pauses 30 s); the runner reports a dead watcher thread once | `test_the_watcher_survives_unexpected_errors_and_keeps_polling`; runner `_check_news_watcher` |
| 5 | Outlet = the article link's publisher domain (`outlet_domain`); a re-served article never adds an outlet | `test_a_re_served_article_is_one_outlet_and_other_publishers_corroborate_it` |
| 6 | Classifier rewritten: every keyword whole-word; cost and rupee phrases ("crude surges", "rupee falls") scored for India and removed before scoring the rest | 7 parametrised cases in `test_headline_direction` (all the judge's headlines) |
| 7 | `major_unclear` judges importance before relevance; world news counts for indices, not single stocks; threshold 0.45 so corroborated macro news (0.49) can fire | `test_big_unclear_world_news_pauses_index_entries_but_not_single_stocks` |
| 8 | Automatic stop uses the current drawdown and only trades closed after the last manual release (`KillSwitch.released_at`) | `test_the_automatic_stop_judges_the_current_drawdown_and_restarts_after_a_review` |
| 9 | Shadow book: no overnight trim (`enforce_limits` False); adverse-news exit applied to it too | `test_the_shadow_book_ignores_the_overnight_cap_and_follows_the_news_exit` |
| 10 | `journal/shadow_trades.json` reset to `[]`; `scan-once` runs without the shadow desk; shadow fills only in `SessionPhase.TRADING`; a session-wide test guard fails the run if any test writes into `data/live` or `journal/` (tests/conftest.py) | `test_no_shadow_fills_outside_the_session` |
| 11 | Credentials must be a usable set (token, or key with TOTP/secret); `auto` falls back to NSE on a missing SDK or credentials | `test_a_key_alone_is_not_a_usable_groww_login_and_auto_falls_back` |
| 12 | Daily allowances saved in `data/live/state/news_usage.json` and reloaded | `test_daily_allowances_survive_a_restart` |
| 13 | `news-once` waits the configured gap between sources | fno/live/news/cli.py |
| 14 | The gap is now measured from when a request finished. NSE's own retry inside `PublicData.nse_json` (up to 3 tries with 1.5 s and 3 s pauses, after cookie warm-up) is unchanged: it is per-host paced at 1/s and only happens on a refusal; documented here rather than changed | fno/live/news/watcher.py `poll` |
| 15 | The runner loads today's reference data (holidays) before starting the watcher; if that fails, weekdays only | fno/live/runner.py `run_forever` |
| 16 | README, NEWS_FEED_PLAN, DATA_SOURCES (BSE), SAFEGUARDS (profile differences; go-live drawdown now `max_drawdown_pct: 10` of capital, implemented in `readiness_checks`) | docs |
| 17 | `ExitReason.PERFORMANCE_STOP` removed. `NewsWatcher.errors` stays as the de-duplication of warning logs (each source error is logged once until it changes) | |
| 18 | Weekly cap test now reaches the cap on a Friday and checks a new week resets it; trim tests added; Groww re-sign-in tested across 06:00; watcher thread/restart tests added | tests/live/test_safeguards.py, tests/test_groww_provider.py, tests/live/test_news_fixes.py |
| 19 | API news sources are now built in services.py; classifier constants named; adverse-news exit is its own class. Portfolio checks stay as methods of `PortfolioGate`: its ordered check list is the extension point and splitting each into a class adds indirection without a second implementation | |
| 20 | The NSE filings source has its own `PublicData` session (the pacer stays shared) | fno/live/services.py `build_news_watcher` |
