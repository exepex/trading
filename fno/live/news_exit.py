"""Closes an open trade early when strong, credible news goes against it. Exit only: news never adds to a trade.

Used for the paper book and the shadow book alike. One trade that cannot be priced never stops the others."""

from __future__ import annotations

import logging
from datetime import datetime

from ..constants import Direction, ExitReason
from .news.impact import STRONG_CREDIBILITY, NewsRoom
from .paper_desk import PaperDesk

log = logging.getLogger(__name__)
ERROR_TEMPLATE = "{trade} adverse-news exit failed: {error}"


class AdverseNewsExit:
    def __init__(self, room: NewsRoom, min_score: float = 0.5):
        self.room = room
        self.min_score = min_score

    def close_hit(self, desk: PaperDesk, now: datetime) -> tuple[list[dict], list[str]]:
        """Trades closed because of news against them, and the errors met (one per trade that failed)."""
        closed, errors = [], []
        for trade in desk.open_trades():
            try:
                note = self._against(trade, now)
                exited = desk.close(trade["id"], ExitReason.ADVERSE_NEWS, note) if note else None
            except Exception as exc:  # noqa: BLE001 - report it, keep checking the other trades
                errors.append(ERROR_TEMPLATE.format(trade=trade["id"], error=exc))
                continue
            if exited:
                closed.append(exited)
        return closed, errors

    def _against(self, trade: dict, now: datetime) -> str | None:
        """The news reason when credible news pushes at least `min_score` against the trade's side."""
        pulse = self.room.pulse(trade["underlying"], now)
        strongest = pulse.strongest
        if strongest is None or strongest.story.credibility not in STRONG_CREDIBILITY:
            return None
        side = 1 if trade.get("direction") == Direction.BULLISH.value else -1
        return strongest.reason if pulse.score * side <= -self.min_score else None
