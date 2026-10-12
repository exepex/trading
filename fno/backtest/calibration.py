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


YAHOO_RANGES = ("5d", "1mo", "60d")
NO_DATA = "no data (every source failed)"
DEFAULT_IV_PCT = 15.0
RISK_FREE_RATE = 0.065


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
    if not hourly:
        return []
    share = sum(v >= minimum for v in hourly) / len(hourly)
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
                sigma = (quote.iv or DEFAULT_IV_PCT) / 100
                greeks = bs_greeks(chain.spot, strike, chain.years_to_expiry(), RISK_FREE_RATE, sigma, kind)
                detail = check.detail(chain, quote.fill_price(OrderSide.BUY.value), greeks)
                lines.append(f"{symbol} {expiry} {strike:g} {kind}: {detail}")
    return lines


def add_calibrate_parser(subparsers) -> None:
    p = subparsers.add_parser("calibrate", help="re-measure the sideways-day and move-check calibration")
    p.add_argument("--range", default="5d", choices=YAHOO_RANGES, help="history for path efficiency")
    p.set_defaults(func=run_calibrate_command)


def run_calibrate_command(args) -> int:
    from ..live.services import build_move_check

    cfg = load_config(args.config)
    minimum = cfg.get("live", {}).get("guards", {}).get("sideways_day", {}).get("min_efficiency", 0.3)
    efficiency = efficiency_report(args.range, minimum)
    moves = move_report(cfg, build_move_check(cfg))
    priced = [line for line in moves if "unavailable" not in line]
    for line in (efficiency or [f"path efficiency: {NO_DATA}"]) + [""] + (moves or [f"move check: {NO_DATA}"]):
        print(line)
    return 0 if efficiency or priced else 1
