"""`python -m fno backtest`: replay the desk's rules on the last weeks of 5-minute prices."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..config import ROOT, load_config
from ..constants import BENCHMARK_UNDERLYING
from ..live.contract_picker import ExitLevels
from ..live.exit_policy import ExitPolicy, TrailingStop
from ..live.feeds.nse_feed import NseLiveFeed
from ..live.feeds.price_feed import YahooPriceFeed
from ..live.market_clock import MarketClock, SessionTimes
from ..live.market_view import MarketViewBuilder, ViewThresholds
from ..live.signals.registry import build_guard_rules, build_signal_rules
from ..models import IST
from .option_model import OptionModel
from .report import format_report
from .simulator import Backtester

DEFAULT_SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN"]
MAX_DAYS = 59  # Yahoo keeps 60 days of 5-minute prices
PRICE_GUARDS = ("sideways_day",)  # guards that can be judged from prices alone


def add_backtest_parser(subparsers) -> None:
    p = subparsers.add_parser("backtest", help="replay the rules on recent 5-minute prices (an approximation)")
    p.add_argument("symbols", nargs="*", help=f"default: {' '.join(DEFAULT_SYMBOLS)}")
    p.add_argument("--days", type=int, default=MAX_DAYS)
    p.add_argument("--out", default=str(ROOT / "reports"))
    p.set_defaults(func=run_backtest_command)


def run_backtest_command(args) -> int:
    cfg = load_config(args.config)
    live, holding = cfg.get("live", {}), cfg.get("holding", {})
    clock = MarketClock(
        SessionTimes.from_config(holding, live.get("signals", {}).get("opening_range", {}).get("minutes", 15))
    )
    exits = ExitLevels.from_config(cfg.get("exits", {}).get("long_option", {}))
    guards = {k: v for k, v in live.get("guards", {}).items() if k in PRICE_GUARDS}
    builder = MarketViewBuilder(
        build_signal_rules(live.get("signals", {})),
        build_guard_rules(guards),
        ViewThresholds.from_config(live.get("thresholds")),
    )
    policy = ExitPolicy(
        clock, holding.get("max_days", 2), 1, TrailingStop.from_config(cfg.get("exits", {}).get("trailing_stop", {}))
    )
    tester = Backtester(
        builder, clock, policy, OptionModel(), exits.stop_loss_pct, exits.take_profit_pct, cfg.get("charges", {})
    )
    days = min(args.days, MAX_DAYS)
    feed, lots = YahooPriceFeed(), _lot_sizes(cfg)
    benchmark = feed.candles(BENCHMARK_UNDERLYING, f"{days + 1}d")
    results = {}
    for symbol in [s.upper() for s in args.symbols] or DEFAULT_SYMBOLS:
        try:
            candles = feed.candles(symbol, f"{days + 1}d")
        except Exception as exc:  # noqa: BLE001 - one missing symbol must not stop the report
            print(f"skipped {symbol}: {exc}")
            continue
        results[symbol] = tester.run(symbol, candles, lots.get(symbol, 1), benchmark)
    report = format_report(results, days)
    out = Path(args.out) / f"backtest-{datetime.now(IST):%Y-%m-%d}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nSaved {out}")
    return 0


def _lot_sizes(cfg: dict) -> dict[str, int]:
    try:
        return NseLiveFeed().lot_sizes()
    except Exception:  # noqa: BLE001 - fall back to the configured lot sizes
        return {k: int(v) for k, v in cfg.get("lot_sizes", {}).items()}
