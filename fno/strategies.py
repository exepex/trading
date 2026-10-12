"""Build, price and rank option strategy candidates for one chain."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import date

from .analytics import norm_pdf
from .costs import legs_charges
from .models import OptionChain, now_ist
from .naming import groww_contract_name
from .signals import Signals

CODES = {
    "bull_call_spread": "BCS",
    "bear_put_spread": "BPS",
    "long_call": "LC",
    "long_put": "LP",
    "iron_condor": "IC",
}
DIRECTION = {
    "bull_call_spread": "bullish",
    "long_call": "bullish",
    "bear_put_spread": "bearish",
    "long_put": "bearish",
    "iron_condor": "neutral",
}


@dataclass
class Leg:
    kind: str  # CE / PE
    strike: float
    side: str  # buy / sell
    price: float  # assumed fill per unit
    oi: float = 0.0
    spread_pct: float | None = None
    symbol: str | None = None

    @property
    def sign(self) -> int:
        return 1 if self.side == "buy" else -1

    def intrinsic(self, s: float) -> float:
        return max(s - self.strike, 0.0) if self.kind == "CE" else max(self.strike - s, 0.0)


@dataclass
class Candidate:
    id: str
    underlying: str
    expiry: str
    dte: int
    strategy: str
    direction: str
    spot: float
    lot_size: int
    legs: list[Leg]
    entry_value: float  # per unit; positive = net debit paid, negative = net credit received
    max_profit: float  # per unit (inf if unbounded)
    max_loss: float  # per unit, positive number
    breakevens: list[float]
    pop_market: float  # probability of profit at expiry under the market-implied distribution
    ev_market: float  # expected P&L per unit at expiry, market-implied (before charges)
    ev_view: float  # same, tilted by the directional view (assumption)
    charges_per_lot: float  # round-trip estimate
    stop_amount: float  # per unit loss that triggers exit
    target_amount: float  # per unit gain that triggers exit
    risk_per_lot: float  # planned rupee risk for one lot (stop + charges)
    worst_case_per_lot: float  # rupees if held to expiry and everything goes wrong
    lots: int
    score: float
    notes: list[str] = field(default_factory=list)
    capital_used: float = 0.0  # premium paid (or margin for credit trades) for the suggested lots
    exception: bool = False  # one lot above the normal per-trade budget, allowed on strong evidence

    def contract_names(self) -> list[str]:
        """How each leg reads in the Groww app search, e.g. 'NIFTY 19 Oct 22500 Put'."""
        expiry = date.fromisoformat(self.expiry)
        return [groww_contract_name(self.underlying, expiry, leg.strike, leg.kind) for leg in self.legs]

    def profit_text(self) -> str:
        if self.strategy == "long_put":
            return f"grows the further {self.underlying} falls"
        if math.isinf(self.max_profit):
            return f"grows the further {self.underlying} rises"
        return f"Rs {self.max_profit * self.lot_size:,.0f}"

    def payoff(self, s: float) -> float:
        return sum(l.sign * l.intrinsic(s) for l in self.legs) - self.entry_value

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("max_profit",):
            if math.isinf(d[k]):
                d[k] = None
        return d


def _round_to(x: float, step: float, how: str = "nearest") -> float:
    q = x / step
    q = math.floor(q) if how == "down" else math.ceil(q) if how == "up" else round(q)
    return q * step


def _terminal_grid(spot: float, sigma: float, t: float, r: float, z_shift: float, n: int = 401):
    """(price, weight) pairs approximating the lognormal terminal distribution."""
    zs = [-6 + 12 * i / (n - 1) for i in range(n)]
    dz = zs[1] - zs[0]
    sd = sigma * math.sqrt(t)
    pts = []
    for z in zs:
        s = spot * math.exp((r - 0.5 * sigma**2) * t + sd * (z + z_shift))
        pts.append((s, norm_pdf(z) * dz))
    total = sum(w for _, w in pts)
    return [(s, w / total) for s, w in pts]


def _analyse_payoff(c: Candidate) -> tuple[float, float, list[float]]:
    strikes = sorted({l.strike for l in c.legs})
    probe = [0.01] + strikes + [c.spot * 4]
    values = [c.payoff(s) for s in probe]
    slope_hi = c.payoff(c.spot * 5) - c.payoff(c.spot * 4)
    max_profit = math.inf if slope_hi > 1e-9 else max(values)
    max_loss = -min(values)
    grid = sorted(set(probe + [c.spot * (0.5 + i / 400) for i in range(401)]))
    bes = []
    prev_s, prev_v = grid[0], c.payoff(grid[0])
    for s in grid[1:]:
        v = c.payoff(s)
        if (prev_v < 0) != (v < 0) and v != prev_v:
            bes.append(round(prev_s + (s - prev_s) * (-prev_v) / (v - prev_v), 1))
        prev_s, prev_v = s, v
    return max_profit, max(max_loss, 0.0), sorted(set(bes))


def _make_leg(chain: OptionChain, strike: float, kind: str, side: str, slippage: float) -> Leg | None:
    q = chain.get(strike, kind)
    if not q or q.ltp <= 0:
        return None
    return Leg(
        kind=kind,
        strike=strike,
        side=side,
        price=round(q.fill_price(side, slippage), 2),
        oi=q.oi,
        spread_pct=q.spread_pct,
        symbol=q.symbol,
    )


def _structures(chain: OptionChain, sig: Signals, enabled: dict) -> list[tuple[str, list[tuple[float, str, str]]]]:
    step = chain.strike_step()
    atm = chain.atm_strike()
    em = sig.expected_move or chain.spot * 0.02
    out: list[tuple[str, list[tuple[float, str, str]]]] = []
    widths = sorted({max(step, _round_to(em, step)), max(step, _round_to(em * 0.5, step))})
    for w in widths:
        if enabled.get("bull_call_spread"):
            out.append(("bull_call_spread", [(atm, "CE", "buy"), (atm + w, "CE", "sell")]))
        if enabled.get("bear_put_spread"):
            out.append(("bear_put_spread", [(atm, "PE", "buy"), (atm - w, "PE", "sell")]))
    if enabled.get("long_call"):
        out.append(("long_call", [(atm, "CE", "buy")]))
    if enabled.get("long_put"):
        out.append(("long_put", [(atm, "PE", "buy")]))
    if enabled.get("iron_condor"):
        wing = max(step, _round_to(em * 0.5, step))
        sc = _round_to(chain.spot + em, step, "up")
        sp = _round_to(chain.spot - em, step, "down")
        out.append(
            (
                "iron_condor",
                [(sp - wing, "PE", "buy"), (sp, "PE", "sell"), (sc, "CE", "sell"), (sc + wing, "CE", "buy")],
            )
        )
    return out


def _exit_plan(strategy: str, entry_value: float, max_profit: float, cfg: dict) -> tuple[float, float]:
    ex = cfg.get("exits", {})
    if strategy in ("bull_call_spread", "bear_put_spread"):
        r = ex.get("debit_spread", {})
        return entry_value * r.get("stop_loss_pct_of_debit", 50) / 100, max_profit * r.get(
            "take_profit_pct_of_max_profit", 60
        ) / 100
    if strategy in ("long_call", "long_put"):
        r = ex.get("long_option", {})
        return entry_value * r.get("stop_loss_pct_of_premium", 40) / 100, entry_value * r.get(
            "take_profit_pct_of_premium", 80
        ) / 100
    credit = -entry_value
    r = ex.get("credit_spread", {})
    return credit * r.get("stop_loss_multiple_of_credit", 1.0), credit * r.get("take_profit_pct_of_credit", 50) / 100


def build_candidates(chain: OptionChain, sig: Signals, cfg: dict) -> list[Candidate]:
    liq = cfg.get("liquidity", {})
    slippage = liq.get("slippage_pct", 0.5)
    r = cfg.get("risk_free_rate", 0.065)
    sigma = sig.atm_iv or 0.15
    t = chain.years_to_expiry()
    view = cfg.get("signals", {}).get("view_strength", 0.35)
    market = _terminal_grid(chain.spot, sigma, t, r, 0.0)
    tilted = _terminal_grid(chain.spot, sigma, t, r, sig.bias * view)
    out: list[Candidate] = []
    for strategy, spec in _structures(chain, sig, cfg.get("strategies", {})):
        legs = [_make_leg(chain, k, kind, side, slippage) for k, kind, side in spec]
        if any(l is None for l in legs):
            continue
        entry = round(sum(l.sign * l.price for l in legs), 2)
        if strategy == "iron_condor" and entry >= 0:
            continue
        if strategy != "iron_condor" and entry <= 0:
            continue
        cid = f"{chain.underlying}-{chain.expiry:%d%b}-{CODES[strategy]}-" + "-".join(f"{int(l.strike)}" for l in legs)
        c = Candidate(
            id=cid,
            underlying=chain.underlying,
            expiry=chain.expiry.isoformat(),
            dte=(chain.expiry - now_ist().date()).days,
            strategy=strategy,
            direction=DIRECTION[strategy],
            spot=chain.spot,
            lot_size=chain.lot_size,
            legs=legs,
            entry_value=entry,
            max_profit=0,
            max_loss=0,
            breakevens=[],
            pop_market=0,
            ev_market=0,
            ev_view=0,
            charges_per_lot=0,
            stop_amount=0,
            target_amount=0,
            risk_per_lot=0,
            worst_case_per_lot=0,
            lots=0,
            score=0,
        )
        c.max_profit, c.max_loss, c.breakevens = _analyse_payoff(c)
        c.pop_market = sum(w for s, w in market if c.payoff(s) > 0)
        c.ev_market = sum(c.payoff(s) * w for s, w in market)
        c.ev_view = sum(c.payoff(s) * w for s, w in tilted)

        # Round trip: open every leg, then close every leg at a similar price.
        orders = [(l.side, l.price) for l in legs] + [("sell" if l.side == "buy" else "buy", l.price) for l in legs]
        c.charges_per_lot = round(legs_charges(orders, chain.lot_size, cfg.get("charges", {})), 2)
        stop, target = _exit_plan(strategy, entry, c.max_profit, cfg)
        c.stop_amount, c.target_amount = round(min(stop, c.max_loss), 2), round(target, 2)
        c.risk_per_lot = round(c.stop_amount * chain.lot_size + c.charges_per_lot, 2)
        c.worst_case_per_lot = round(c.max_loss * chain.lot_size + c.charges_per_lot, 2)

        # Liquidity checks.
        for l in legs:
            if l.oi < liq.get("min_open_interest", 500):
                c.notes.append(f"thin open interest at {int(l.strike)}{l.kind} ({l.oi:,.0f})")
            if l.spread_pct is not None and l.spread_pct > liq.get("max_spread_pct", 5.0):
                c.notes.append(f"wide bid-ask at {int(l.strike)}{l.kind} ({l.spread_pct:.1f}%)")
        cost_per_unit = c.charges_per_lot / chain.lot_size
        c.score = round((c.ev_view - cost_per_unit) / max(c.max_loss, 1e-6), 4)
        strong = confidence_label(sig) == "high" and c.score > 0 and c.target_amount >= 2 * c.stop_amount
        cost_per_lot = abs(entry) * chain.lot_size
        c.lots, c.exception, note = size_position(cost_per_lot, strong, cfg.get("position_rules", {}))
        c.capital_used = round(c.lots * cost_per_lot, 2)
        if note:
            c.notes.append(note)
        out.append(c)
    return out


def size_position(cost_per_lot: float, strong: bool, rules: dict) -> tuple[int, bool, str]:
    """Full lots within the per-trade budget (+ tolerance); one pricier lot only on strong evidence.

    Returns (lots, is_exception, note).
    """
    budget = rules.get("per_trade_budget", 10000)
    ceiling = budget * (1 + rules.get("budget_tolerance_pct", 10) / 100)
    exception_max = rules.get("exception_max_per_trade", 20000)
    if cost_per_lot <= 0:
        return 0, False, "no valid price"
    lots = int(ceiling // cost_per_lot)
    if lots >= 1:
        return lots, False, ""
    if cost_per_lot > exception_max:
        return 0, False, f"1 lot costs Rs {cost_per_lot:,.0f}, above the Rs {exception_max:,.0f} single-trade ceiling"
    if strong:
        return 1, True, f"1 lot costs Rs {cost_per_lot:,.0f}: above the normal budget, allowed on strong evidence"
    return (
        0,
        False,
        f"1 lot costs Rs {cost_per_lot:,.0f}, above Rs {ceiling:,.0f}, and the evidence is not strong enough",
    )


def confidence_label(sig: Signals) -> str:
    strength = abs(sig.bias)
    if strength >= 0.5 and sig.agreement >= 0.75:
        return "high"
    if strength >= 0.3 and sig.agreement >= 0.6:
        return "medium"
    return "low"


def select(cands: list[Candidate], sig: Signals) -> list[Candidate]:
    """Keep only candidates that match the bias and the volatility regime, best first."""
    keep = []
    for c in cands:
        if c.direction != sig.label:
            continue
        if c.strategy in ("long_call", "long_put") and sig.vol_regime == "rich":
            continue
        if c.strategy == "iron_condor" and sig.vol_regime == "cheap":
            continue
        if any("thin open interest" in n or "wide bid-ask" in n for n in c.notes):
            continue
        keep.append(c)
    # Setups that fit the position rules first, then by score.
    return sorted(keep, key=lambda c: (c.lots == 0, -c.score))
