"""Which capture a decision executes at, and its window (story C3). E3 will give its execution capture through
`ExecutionSchedule`; until then the desk's capture is the pack's own A4 snapshot, in the recorder's window."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ..desk.common_pack import SNAPSHOT_INPUT, CommonPack
from ..models import IST
from ..quotes.recorder import WINDOW_END, WINDOW_START
from .data_checks import ScheduledCapture


class ExecutionSchedule(ABC):
    @abstractmethod
    def capture(self, pack: CommonPack) -> ScheduledCapture | None:
        """The capture the day's decisions execute at, with its window; None when there is none."""


class PackSnapshotSchedule(ExecutionSchedule):
    """The A4 snapshot the common pack holds, inside the recorder's window (14:55-15:10 IST)."""

    def capture(self, pack: CommonPack) -> ScheduledCapture | None:
        snapshot_id = pack.body["provenance"].get(SNAPSHOT_INPUT, {}).get("snapshot_id")
        if snapshot_id is None:
            return None
        start, end = (datetime.combine(pack.day, moment, IST) for moment in (WINDOW_START, WINDOW_END))
        return ScheduledCapture(snapshot_id, start, end)
