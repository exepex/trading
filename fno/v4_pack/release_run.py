"""The day's v4 release run (story G10 part 2; judge 282.2's condition): first the catch-up, then today. The catch-up
writes a `system_late` record for every scored session from the go-live date to yesterday that has no release record
**in Drive** (the write-once store decides, never the checkout), so a day the routine never ran is settled and no look
stays blocked. Today: the pack from the day's capture, or `system_late` once the 14:40 window has closed with none.
A write-once refusal is named and the run goes on; nothing is ever overwritten."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta

from ..storage.data_store import DataStore
from ..storage.raw_store import RawFileConflict
from .builder import PackBuilder
from .capture import CaptureSource
from .codec import capture_window
from .model import Pack
from .paths import release_path
from .release import publish

NOT_LIVE = "v4 release: not live (config.yaml daily.live_from.forecasts_v4 is not set or is later)"
RELEASED = "v4 release {day}: {label}{detail}"
CAUGHT_UP = "v4 release {day}: system_late (catch-up: no release record in Drive)"
ALREADY = "v4 release {day}: already released"
WAITING = "v4 release {day}: no complete pack yet ({reasons}); not released before {end:%H:%M}"
REFUSED = "v4 release {day}: REFUSED by the write-once store ({error}); nothing overwritten"


class ReleaseRun:
    def __init__(self, store: DataStore, in_drive: Callable[[str], bool], capture: CaptureSource,
                 builder: PackBuilder, sessions: Callable[[date, date], list[date]], live_from: date | None,
                 clock: Callable[[], datetime]):  # fmt: skip
        """`in_drive(path)`: whether the data store's Drive area holds `path`; `sessions(a, b)`: scored sessions in
        [a, b]."""
        self.store, self.in_drive, self.capture, self.builder = store, in_drive, capture, builder
        self.sessions, self.live_from, self.clock = sessions, live_from, clock
        self.refused = False

    def run(self, today: date) -> list[str]:
        if self.live_from is None or today < self.live_from:
            return [NOT_LIVE]
        lines = [self._catch_up(day) for day in self.sessions(self.live_from, today - timedelta(days=1))]
        lines = [line for line in lines if line]
        if today in self.sessions(today, today):
            lines.append(self._today(today))
        return lines

    def _catch_up(self, day: date) -> str:
        if self._released(day):
            return ""
        return self._publish(day, None) or CAUGHT_UP.format(day=day)

    def _today(self, day: date) -> str:
        if self._released(day):
            return ALREADY.format(day=day)
        built = self.builder.build(day, self.capture.capture(day))
        end = capture_window(day)[1]
        if built.pack is None and self.clock() <= end:
            return WAITING.format(day=day, reasons="; ".join(built.reasons), end=end)
        detail = "" if built.pack else f" ({'; '.join(built.reasons)})"
        return self._publish(day, built.pack) or RELEASED.format(day=day, label=self._label(built.pack), detail=detail)

    def _publish(self, day: date, pack: Pack | None) -> str:
        """'' when written; the refusal line when the write-once store refused."""
        try:
            publish(self.store, day, pack)
        except RawFileConflict as error:
            self.refused = True
            return REFUSED.format(day=day, error=type(error).__name__)
        return ""

    def _released(self, day: date) -> bool:
        return self.in_drive(f"{self.store.area}/{release_path(day)}")

    @staticmethod
    def _label(pack: Pack | None) -> str:
        return pack.label if pack else "system_late"
