"""`python -m fno calibrate`: re-measure the numbers behind two wave-2 thresholds, so anyone can check them.

- path efficiency of 5-minute moves (sideways_day guard): whole day vs rolling last hour, and the share of hours
  at or above the configured minimum;
- move needed vs move likely (move check) for near-the-money calls and puts on live option chains.
"""

from __future__ import annotations

from datetime import datetime

from ..analytics import bs_greeks
from ..config import load_config
from ..constants import OrderSide
from ..live.feeds.price_feed import YahooPriceFeed
from ..live.move_check import MoveCheck
from ..live.signals.day_type import path_efficiency
from ..models import IST
from ..providers import get_provider
from .simulator import sessions_of

EFFICIENCY_SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "HDFCBANK", "INFY", "SBIN", "ICICIBANK", "DMART", "PERSISTENT"]
MOVE_SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE"]
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
WINDOW = 12
MIN_SESSION_BARS = 40
STRIKES_EACH_SIDE = 3


def quantiles(values: list[float]) -> list[float]:
    ordered = sorted(values)
    return [round(ordered[int(len(ordered) * q)], 2) for q in QUANTILES] if ordered else []


def efficiency_report(history_range: str, minimum: float) -> list[str]:
    feed, whole, hourly = YahooPriceFeed(), [], []
    for symbol in EFFICIENCY_SYMBOLS:
        try:
            sessions = sessions_of(feed.candles(symbol, history_range))
        except Exception as exc:  # noqa: BLE001 - a missing symbol only shrinks the sample
            print(f"skipped {symbol}: {exc}")
            continue
        for bars in (s for s in sessions if len(s) >= MIN_SESSION_BARS):
            whole.append(path_efficiency(bars))
            hourly += [path_efficiency(bars[i - WINDOW : i]) for i in range(WINDOW, len(bars))]
    share = sum(v >= minimum for v in hourly) / len(hourly) if hourly else 0.0
    return [
        f"sessions: {len(whole)}",
        f"whole-day efficiency p10/25/50/75/90: {quantiles(whole)}",
        f"last-hour efficiency p10/25/50/75/90: {quantiles(hourly)}",
        f"share of hours at or above {minimum}: {share:.1%}",
    ]


def move_report(cfg: dict, check: MoveCheck) -> list[str]:
    provider, lines, today = get_provider("nse", cfg), [], datetime.now(IST).date()
    min_days = cfg.get("live", {}).get("min_days_to_expiry", 4)
    for symbol in MOVE_SYMBOLS:
        try:
            expiry = next(e for e in provider.expiries(symbol) if (e - today).days >= min_days)
            chain = provider.chain(symbol, expiry)
        except Exception as exc:  # noqa: BLE001 - NSE may refuse; report and carry on
            lines.append(f"{symbol}: unavailable ({exc})")
            continue
        strikes = chain.strikes()
        atm = strikes.index(chain.atm_strike())
        for strike in strikes[max(0, atm - STRIKES_EACH_SIDE) : atm + STRIKES_EACH_SIDE + 1]:
            for kind in ("CE", "PE"):
                quote = chain.get(strike, kind)
                if quote is None or not quote.ltp:
                    continue
                greeks = bs_greeks(chain.spot, strike, chain.years_to_expiry(), 0.065, (quote.iv or 15) / 100, kind)
                detail = check.detail(chain, quote.fill_price(OrderSide.BUY.value), greeks)
                lines.append(f"{symbol} {expiry} {strike:g} {kind}: {detail}")
    return lines


def add_calibrate_parser(subparsers) -> None:
    p = subparsers.add_parser("calibrate", help="re-measure the sideways-day and move-check calibration")
    p.add_argument("--range", default="5d", help="history for path efficiency (Yahoo: up to 60d)")
    p.set_defaults(func=run_calibrate_command)


def run_calibrate_command(args) -> int:
    cfg = load_config(args.config)
    live, holding = cfg.get("live", {}), cfg.get("holding", {})
    minimum = live.get("guards", {}).get("sideways_day", {}).get("min_efficiency", 0.3)
    check = MoveCheck(
        live.get("contract", {}).get("max_needed_to_likely_move", 1.5), holding.get("max_days", 2) * 7 / 5
    )
    for line in efficiency_report(args.range, minimum) + [""] + move_report(cfg, check):
        print(line)
    return 0
