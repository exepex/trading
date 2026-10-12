"""Good and bad hours: closed trades grouped by time of entry, days to expiry at entry and exit reason."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from ...constants import TradeStatus
from ...models import IST

ENTRY_BUCKETS = (  # (label, starts at)
    ("09:15-10:30 opening", time(9, 15)),
    ("10:30-12:00 morning", time(10, 30)),
    ("12:00-13:30 midday", time(12, 0)),
    ("13:30-15:30 afternoon", time(13, 30)),
)
EXPIRY_BUCKETS = (("0-4 days to expiry", 0), ("5-9 days to expiry", 5), ("10+ days to expiry", 10))
UNKNOWN = "unknown"
HEADER = f"{'group':<26} {'trades':>6} {'won':>5} {'net P&L':>11} {'per trade':>10}"
ROW = "{label:<26} {trades:>6} {win:>4.0f}% {net:>11,.0f} {avg:>10,.0f}"
NO_TRADES = "No closed trades yet."


@dataclass(frozen=True)
class GroupResult:
    label: str
    trades: int
    win_rate_pct: float
    net_pnl: float

    @property
    def per_trade(self) -> float:
        return self.net_pnl / self.trades if self.trades else 0.0


def _ist(stamp: str) -> datetime:
    moment = datetime.fromisoformat(stamp)
    return moment.astimezone(IST) if moment.tzinfo else moment  # the journal writes IST; convert anything else


def entry_bucket(opened_at: str) -> str:
    moment = _ist(opened_at).time()
    label = ENTRY_BUCKETS[0][0]
    for name, starts in ENTRY_BUCKETS:
        if moment >= starts:
            label = name
    return label


def expiry_bucket(opened_at: str, expiry: str | None) -> str:
    if not expiry:
        return UNKNOWN
    days = (date.fromisoformat(expiry) - _ist(opened_at).date()).days
    label = EXPIRY_BUCKETS[0][0]
    for name, minimum in EXPIRY_BUCKETS:
        if days >= minimum:
            label = name
    return label


def _group(trades: list[dict], key) -> list[GroupResult]:
    groups: dict[str, list[float]] = {}
    for trade in trades:
        groups.setdefault(key(trade), []).append(float(trade.get("pnl_net") or 0.0))
    return [
        GroupResult(label, len(pnls), 100.0 * sum(p > 0 for p in pnls) / len(pnls), sum(pnls))
        for label, pnls in sorted(groups.items())
    ]


def trade_stats(trades: list[dict]) -> dict[str, list[GroupResult]]:
    closed = [t for t in trades if t.get("status") == TradeStatus.CLOSED.value and t.get("opened_at")]
    return {
        "By time of entry": _group(closed, lambda t: entry_bucket(t["opened_at"])),
        "By days to expiry at entry": _group(closed, lambda t: expiry_bucket(t["opened_at"], t.get("expiry"))),
        "By exit reason": _group(closed, lambda t: t.get("exit_reason") or "unknown"),
    }


def format_trade_stats(stats: dict[str, list[GroupResult]]) -> str:
    if not any(stats.values()):
        return NO_TRADES
    lines = []
    for title, groups in stats.items():
        lines += ["", title, HEADER]
        lines += [
            ROW.format(label=g.label[:26], trades=g.trades, win=g.win_rate_pct, net=g.net_pnl, avg=g.per_trade)
            for g in groups
        ]
    return "\n".join(lines).lstrip()
