"""Where the monitor's open positions come from (story LM1): every open paper or shadow position, valued at the mark.
Today no position is open anywhere (no paper trade, no shadow account, an empty playbook registry), so the source in
use is `NoOpenPositions`; the adapter over E1's accounts and E4's marking comes with the first position (round 2b)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

from ..intraday.document import SnapshotDocument
from .model import WatchedPosition


class OpenPositionSource(ABC):
    @abstractmethod
    def positions(self, day: date, mark: datetime, document: SnapshotDocument | None) -> list[WatchedPosition]:
        """Every open position, its loss at this mark's touch (None when a leg is not on the mark)."""


class NoOpenPositions(OpenPositionSource):
    def positions(self, day: date, mark: datetime, document: SnapshotDocument | None) -> list[WatchedPosition]:
        return []
