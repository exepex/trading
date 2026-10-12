# Wave 3 judgment, round 2 (2026-10-12)

Scope: HEAD 38ac221 (wave 3 fixes are in ef44310, diffed against 32b24fc). Verdict: **FAIL**: 0 blocking, 1 should fix, 5 minor. Nothing can enlarge a trade or get around a limit.

## Commands
- `git checkout --detach 38ac221` gives `38ac221 Fix the judge's round 3 findings for wave 0`.
- `python -m pytest -q`: 176 passed. `git status` is clean afterwards (conftest protects `data/live` and `journal`).
- `ruff check fno tests`: All checks passed. `ruff format --check`: 135 files already formatted.
- Line counts: largest are services.py 337, strategies.py 321, journal.py 320. html_report.py is 722 and exempt. No file over 350.
- `python -m fno backtest NIFTY --days 10 --out /tmp/bt`: exit 0. 8 trades, +Rs 7,650, 10 sessions, 1 unfinished. Exits: stop 4 + target 3 + trailing 1 = 8.
- 30-day, 9-name re-run through `build_backtester` (/tmp/judge/bt_probe.py):
  - Matches `reports/backtest-2026-10-12.md` exactly: 219 trades, -195,305, 270 sessions, 7 unfinished.
  - Exits 37 + 109 + 29 + 44 = 219.
  - Cooldowns were built from config: `Cooldowns(30, 45)`, stop 30 / target 60, hold 2 days, exit 1 day before expiry.
  - 0 re-entries inside 30 minutes of an exit (45 after a loss), checked per name.
  - Strikes sit on the grid, e.g. HDFCBANK 690/700/710, RELIANCE 1180/1200, BANKNIFTY in steps of 100.
- Fresh import of each of simulator, backtest.cli, calibration, services and runner: no import cycle. calibration imports services lazily.
- `calibrate --range 1y` is rejected: "choose from '5d', '1mo', '60d'".
- Calibrate with both sources stubbed to fail prints "no data (every source failed)" and exits 1. The same holds when NSE answers only "unavailable" lines.

## Round-1 findings
| # | Status | Evidence |
|---|---|---|
| 1 prioritise | CLOSED | The lock is shared with next_request/record. Probe: a source with a 180 s cache is moved to +180 s; a never-polled source is unchanged; a refused source stays at 1,100 s (failures=1); the daily cap still excludes Marketaux. 20,000 × 2 concurrent prioritise/next_request/record calls raised no errors. Covered by `test_prioritise_never_breaks_a_limit`. |
| 2 Groww retry storm | CLOSED (alert part: see N1) | 3 hours of failures make 17 calls, spaced 20, 40, 80, 160, 320, 640, then 900 s. `test_a_failing_price_feed_backs_off_and_is_reported_once`. |
| 3 shock re-check | CLOSED | runner.py `_watch_prices_if_due` calls `chain_source.forget(symbol)` and then `_review`, and leaves `last_review` alone. Probe on the real `CachedProvider.forget`: it drops only that name's chains and refetches. The test asserts 2 reviews, `forgotten == ["NIFTY"]` and an unchanged `last_review`. |
| 4 backtest re-entry | CLOSED | `Cooldowns` in simulator.py. 0 violations on real data. The test is not vacuous: 7 trades with gaps of exactly 45 min. Disclaimer updated. |
| 5 wiring outside services | CLOSED | backtest/cli.py and calibration.py use `build_backtester` / `build_move_check`. No `ExitPolicy(`, `MarketViewBuilder(`, `MoveCheck(` or `Backtester(` outside services.py. |
| 6 stock ATM = spot | CLOSED | `STOCK_STRIKE_STEPS` price bands; strikes from the real run listed above. |
| 7 report omissions | CLOSED | The report prints sessions and unfinished trades. The disclaimer covers 0.2, holidays, the 8% floor and portfolio limits. |
| 8 duplicated constants | CLOSED (residual: N4) | runner uses NSE_SOURCE, BSE_SOURCE and MARKETAUX_SOURCE; services uses `GrowwProvider.name`. |
| 9 Groww symbols / missing prices / check | CLOSED (residual: N2) | Unpriced symbols are logged once a day. The first price call in groww-check is guarded. Index symbols can only be verified with live credentials, and the code says to verify them with groww-check. |
| 10 test gaps | CLOSED | prioritise, batching 50/50/21, failure back-off, no Groww means no price watch, no look-ahead, and pauses are all tested. |
| 11 cadence during a scan | CLOSED | Documented in WAVES.md W3.1. |
| W2 minor 1 | CLOSED | WAVES W2.2 gives calls 0.83-1.51x and puts 0.67-1.21x. |
| W2 minor 2 | CLOSED | `CALENDAR_DAYS_PER_TRADING_DAY` is in constants. One `build_move_check` uses the configured take-profit: `MoveCheck(1.5, 2.8, 60)`. |
| W2 minor 3 | CLOSED | Exit code 1 on no data; `--range` choices enforced. |
| W2 minor 4 | CLOSED | The calibrate output is in conversations/2026-10-12.md; the NOT_MEASURABLE text says "...spot or option sensitivity". |

## Regression checks
- Before and after the builder refactor, the desk's view builder gets all 19 rules and all 7 configured guards, the same as the old inline code. Exit policy is 2 days, 1 day before expiry, trailing (30, 50, enabled). The move check matches config.
- The backtest keeps only `SidewaysDayGuard`.
- services.py importing backtest causes no cycle. services.py is now at 337 of 350 lines, so there is little headroom.
- Tests do not touch repo data.

## New findings
**N1 (should fix): the "live price feed failing" alert can be silently lost.**
- Cause: `PriceWatch._back_off` sets `_down_reported = True` before the rate-limited `report` call and ignores its return value. `_report_problem` returns False when another problem alert went out in the previous 15 minutes.
- Probe (/tmp/judge/probe2.py): another alert 1 minute earlier, then 3 hours of feed failure, gives 0 feed-down alerts sent. The owner never learns that the sudden-move detector is off.
- This is the same defect as wave-0 N11, which was rated should fix. It also contradicts the response's claim "reported once".
- Fix:
  - Change the line to `self._down_reported = report(now, FEED_DOWN.format(error=exc))`.
  - Type `report` as `Callable[[datetime, str], bool]`.
  - Add a test modelled on `test_the_dead_watcher_alert_is_not_lost_to_the_rate_limit`.

**N2 (minor): one unguarded call can lose all groww-check output.**
- In groww_check.py, the second `api.get_ltp(...)` (the raw diagnostic for missing symbols) is unguarded.
- If it raises, every line already collected is lost, because the function returns its list only at the end.
- Fix: wrap it in try/except and append the error as a line.

**N3 (minor): the backtest's post-loss pause is per name, but the desk's is account-wide.**
- `risk_gate._loss_cooldown` blocks every entry for 45 minutes after any losing exit. The backtest only blocks the same name.
- The disclaimer's "each name is simulated on its own" partly discloses this. The response and WAVES describe it as "the desk's ... pauses".
- Fix: say "the post-loss pause is applied per name, not account-wide" in DISCLAIMER and in WAVES W3.2.

**N4 (minor): news source names are still repeated as literals.**
- services.py:78 `SOURCE_CONFIG_KEYS` still spells out "NSE filings" and "BSE filings".
- Fix: key the dict on `NSE_SOURCE` and `BSE_SOURCE`.

**N5 (minor): the cooldown test only covers the 45-minute post-loss branch.**
- `test_no_new_trade_within_the_re_entry_or_loss_pause` uses a falling market, so every trade loses and the 30-minute after-exit branch is never exercised. Real data shows no violations.
- Fix: add a rally case that checks a gap of at least 30 minutes after a winning trade.

**N6 (minor): the missing-price log is keyed on the host date, not the IST date.**
- `PriceWatch` uses `now.date()` for the once-a-day log. This is harmless while the runner passes IST times.
- Fix: use `now.astimezone(IST).date()` for consistency.

## Verdict
**FAIL**. All 11 round-1 findings and all 4 wave-2 minors are closed. N1 (should fix) is open; fix it to pass.
