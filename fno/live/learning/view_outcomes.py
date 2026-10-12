"""Measures how every view and every signal vote turned out: the price move 30 and 90 minutes later.

This grades the signals on every scan, not only on the few trades taken, so we learn within days which
rules actually predict price and which are noise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..models import ScanReport
from ..results_store import ResultsStore

VIEW_OUTCOME_KIND = "view_outcome"


@dataclass
class PendingView:
    symbol: str
    seen_at: datetime
    price: float
    score: float
    direction: str
    votes: dict[str, float]  # rule -> score
    horizons_left: list[int] = field(default_factory=list)


class ViewOutcomeTracker:
    def __init__(self, store: ResultsStore, horizons_minutes: tuple[int, ...] = (30, 90)):
        self.store = store
        self.horizons = tuple(sorted(horizons_minutes))
        self.pending: list[PendingView] = []

    def observe(self, report: ScanReport) -> int:
        """Resolve views whose horizon has passed, then start tracking this scan's views. Returns outcomes stored."""
        stored = self._resolve(report.prices, report.started_at)
        for view in report.views:
            price = report.prices.get(view.symbol)
            if price:
                self.pending.append(
                    PendingView(
                        symbol=view.symbol,
                        seen_at=report.started_at,
                        price=price,
                        score=view.score,
                        direction=view.direction.value,
                        votes={v.rule: v.score for v in view.votes},
                        horizons_left=list(self.horizons),
                    )
                )
        return stored

    def end_of_day(self) -> None:
        """Views whose horizon runs past the close cannot be graded fairly overnight: drop them."""
        self.pending.clear()

    def _resolve(self, prices: dict[str, float], now: datetime) -> int:
        stored = 0
        for view in self.pending:
            price_now = prices.get(view.symbol)
            if not price_now:
                continue
            for horizon in [h for h in view.horizons_left if now - view.seen_at >= timedelta(minutes=h)]:
                self.store.record(VIEW_OUTCOME_KIND, self._outcome(view, horizon, price_now), now, view.symbol)
                view.horizons_left.remove(horizon)
                stored += 1
        self.pending = [v for v in self.pending if v.horizons_left]
        return stored

    @staticmethod
    def _outcome(view: PendingView, horizon: int, price_now: float) -> dict:
        return {
            "seen_at": view.seen_at.isoformat(timespec="seconds"),
            "horizon_minutes": horizon,
            "forward_return_pct": round((price_now / view.price - 1) * 100, 4),
            "score": view.score,
            "direction": view.direction,
            "votes": view.votes,
        }
