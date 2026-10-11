"""Data passed between the live scanner's stages. Plain data, no behaviour beyond simple derived values."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime

from ..constants import STRATEGY_LONG_CALL, STRATEGY_LONG_PUT, Direction, OiBuildup, OptionKind, OrderSide


@dataclass(frozen=True)
class Candle:
    start: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class UnderlyingSnapshot:
    """One F&O underlying at scan time: price move and futures open-interest move."""

    symbol: str
    last_price: float
    previous_close: float | None = None
    oi_change_pct: float | None = None
    traded_value: float = 0.0  # rupees, futures + options, used to rank activity

    @property
    def day_change_pct(self) -> float | None:
        if not self.previous_close:
            return None
        return (self.last_price / self.previous_close - 1) * 100


@dataclass
class SignalVote:
    """One rule's opinion: score in [-1, +1] (bearish to bullish) with a plain-English reason."""

    rule: str
    score: float
    weight: float
    reason: str


@dataclass
class GuardVerdict:
    """A hard filter that can block an underlying regardless of the votes."""

    guard: str
    blocked: bool
    reason: str


@dataclass
class MarketView:
    """Combined view of one underlying."""

    symbol: str
    direction: Direction
    score: float  # weighted mean of the votes, [-1, +1]
    agreement: float  # share of weighted votes on the side of the score
    votes: list[SignalVote] = field(default_factory=list)
    guards: list[GuardVerdict] = field(default_factory=list)
    strong_evidence: bool = False

    @property
    def blocked(self) -> bool:
        return any(g.blocked for g in self.guards)

    @property
    def block_reasons(self) -> list[str]:
        return [g.reason for g in self.guards if g.blocked]


@dataclass
class TradeIdea:
    """A concrete paper trade: one option contract to buy, sized to the position rules."""

    id: str
    underlying: str
    contract_name: str  # as shown in Groww search
    expiry: date
    strike: float
    option_kind: str
    entry_price: float  # per unit, assumed fill (ask)
    lot_size: int
    lots: int
    stop_price: float
    target_price: float
    spot: float
    view: MarketView
    exception: bool = False  # one lot above the normal budget, allowed on strong evidence
    notes: list[str] = field(default_factory=list)

    @property
    def capital_used(self) -> float:
        return self.entry_price * self.lot_size * self.lots

    @property
    def strategy(self) -> str:
        return STRATEGY_LONG_CALL if self.option_kind == OptionKind.CALL.value else STRATEGY_LONG_PUT

    def to_journal_candidate(self) -> dict:
        """The shape fno.journal.open_trade expects."""
        return {
            "id": self.id,
            "underlying": self.underlying,
            "expiry": self.expiry.isoformat(),
            "strategy": self.strategy,
            "direction": self.view.direction.value,
            "spot": self.spot,
            "legs": [
                {
                    "kind": self.option_kind,
                    "strike": self.strike,
                    "side": OrderSide.BUY.value,
                    "price": self.entry_price,
                }
            ],
            "lot_size": self.lot_size,
            "lots": self.lots,
            "entry_value": self.entry_price,
            "stop_amount": round(self.entry_price - self.stop_price, 2),
            "target_amount": round(self.target_price - self.entry_price, 2),
            "exception": self.exception,
            "contract_name": self.contract_name,
            "score": round(self.view.score, 3),
            "reasons": [v.reason for v in self.view.votes if v.score * self.view.score > 0],
        }


@dataclass
class ScanReport:
    """What one scan cycle saw and did."""

    started_at: datetime
    universe_size: int
    shortlisted: list[str] = field(default_factory=list)
    views: list[MarketView] = field(default_factory=list)
    ideas: list[TradeIdea] = field(default_factory=list)
    opened: list[str] = field(default_factory=list)  # journal trade ids
    rejected: dict[str, str] = field(default_factory=dict)  # idea id -> reason
    errors: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "started_at": self.started_at.isoformat(),
            "universe_size": self.universe_size,
            "shortlisted": self.shortlisted,
            "ideas": [i.id for i in self.ideas],
            "opened": self.opened,
            "rejected": self.rejected,
            "errors": self.errors,
        }


def oi_buildup(price_change_pct: float | None, oi_change_pct: float | None, threshold_pct: float = 0.5) -> OiBuildup:
    """Classic reading of futures price vs open interest."""
    if price_change_pct is None or oi_change_pct is None:
        return OiBuildup.UNCLEAR
    if abs(price_change_pct) < threshold_pct * 0.2 or abs(oi_change_pct) < threshold_pct:
        return OiBuildup.UNCLEAR
    if price_change_pct > 0:
        return OiBuildup.LONG_BUILDUP if oi_change_pct > 0 else OiBuildup.SHORT_COVERING
    return OiBuildup.SHORT_BUILDUP if oi_change_pct > 0 else OiBuildup.LONG_UNWINDING


def as_record(obj) -> dict:
    """Dataclass to a JSON-friendly dict (dates and enums as strings)."""

    def clean(value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, Direction):
            return value.value
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value

    return clean(asdict(obj))
