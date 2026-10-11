"""Directional bias and volatility regime from price history and option-chain positioning.

Each component scores in [-1, +1] (bearish to bullish). The weighted sum is the bias.
These are well-known, simple heuristics. They are inputs to a decision, not a forecast.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import analytics as an
from .models import MarketContext, OptionChain

WEIGHTS = {"trend": 0.30, "momentum": 0.20, "rsi": 0.15, "pcr": 0.20, "oi_range": 0.15}


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class Component:
    name: str
    score: float
    weight: float
    detail: str


@dataclass
class Signals:
    bias: float
    label: str  # bullish / bearish / neutral
    agreement: float  # share of weighted components pointing the same way as the bias
    components: list[Component] = field(default_factory=list)
    atm_iv: float | None = None
    hv20: float | None = None
    vix_pct: float | None = None
    vol_regime: str = "normal"  # cheap / normal / rich
    pcr: float | None = None
    max_pain: float | None = None
    support: list[tuple[float, float]] = field(default_factory=list)
    resistance: list[tuple[float, float]] = field(default_factory=list)
    expected_move: float | None = None


def compute_signals(ctx: MarketContext, chain: OptionChain, config: dict) -> Signals:
    comps: list[Component] = []
    closes = ctx.closes
    spot = chain.spot

    # Trend: price relative to 20- and 50-day EMAs.
    if len(closes) >= 50:
        e20, e50 = an.ema(closes, 20)[-1], an.ema(closes, 50)[-1]
        if spot > e20 > e50:
            s = 1.0
        elif spot < e20 < e50:
            s = -1.0
        else:
            s = 0.4 if spot > e50 else -0.4
        comps.append(Component("trend", s, WEIGHTS["trend"], f"spot {spot:,.0f} vs EMA20 {e20:,.0f} / EMA50 {e50:,.0f}"))

    # Momentum: 20-day return, +/-4% maps to +/-1.
    if len(closes) >= 21:
        ret = closes[-1] / closes[-21] - 1
        comps.append(Component("momentum", _clamp(ret / 0.04), WEIGHTS["momentum"], f"20-day return {ret * 100:+.1f}%"))

    # RSI: trend-following in the middle band, contrarian at extremes.
    rsi = an.rsi(closes, 14)
    if rsi is not None:
        if rsi >= 70:
            s = -0.5
        elif rsi <= 30:
            s = 0.5
        else:
            s = _clamp((rsi - 50) / 20) * 0.6
        comps.append(Component("rsi", s, WEIGHTS["rsi"], f"RSI(14) {rsi:.0f}"))

    # PCR on open interest: heavier put writing is read as support. Extremes are discounted.
    pcr = an.put_call_ratio(chain)
    if pcr is not None:
        s = _clamp((pcr - 1.0) / 0.4)
        if pcr > 1.6 or pcr < 0.5:
            s *= 0.5
        comps.append(Component("pcr", s, WEIGHTS["pcr"], f"put/call OI ratio {pcr:.2f}"))

    # Position inside the OI range: near put-wall support leans up, near call-wall resistance leans down.
    walls = an.oi_walls(chain)
    if walls["support"] and walls["resistance"]:
        sup, res = walls["support"][0][0], walls["resistance"][0][0]
        if res > sup:
            pos = (spot - sup) / (res - sup)
            comps.append(
                Component(
                    "oi_range",
                    _clamp(1 - 2 * pos) * 0.7,
                    WEIGHTS["oi_range"],
                    f"spot sits {pos * 100:.0f}% of the way from put wall {sup:,.0f} to call wall {res:,.0f}",
                )
            )

    total_w = sum(c.weight for c in comps) or 1.0
    bias = sum(c.score * c.weight for c in comps) / total_w
    threshold = config.get("signals", {}).get("bias_threshold", 0.2)
    label = "bullish" if bias >= threshold else "bearish" if bias <= -threshold else "neutral"
    same_way = sum(c.weight for c in comps if c.score * bias > 0)
    agreement = same_way / total_w if bias else 0.0

    iv = an.atm_iv(chain, config.get("risk_free_rate", 0.065))
    hv = an.historical_vol(closes, 20)
    vix_pct = None
    if ctx.vix is not None and ctx.vix_year_low is not None and ctx.vix_year_high and ctx.vix_year_high > ctx.vix_year_low:
        vix_pct = (ctx.vix - ctx.vix_year_low) / (ctx.vix_year_high - ctx.vix_year_low)
    regime = "normal"
    ratio = iv / hv if iv and hv else None
    if (ratio and ratio > 1.25) or (vix_pct is not None and vix_pct > 0.6):
        regime = "rich"
    elif (ratio is None or ratio < 0.95) and (vix_pct is None or vix_pct < 0.3):
        regime = "cheap"

    return Signals(
        bias=bias,
        label=label,
        agreement=agreement,
        components=comps,
        atm_iv=iv,
        hv20=hv,
        vix_pct=vix_pct,
        vol_regime=regime,
        pcr=pcr,
        max_pain=an.max_pain(chain),
        support=walls["support"],
        resistance=walls["resistance"],
        expected_move=an.straddle_expected_move(chain),
    )
