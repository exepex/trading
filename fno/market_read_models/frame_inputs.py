"""Inputs of India's market band and flows blocks (stories P10 and P8), read when a session is built: the session the
reader acts on next (from NSE's session calendar) and the archived flows copies (one per day fetched; the latest copy
of each session wins, and nothing after the published session is read: no look-ahead)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from ..research_data.calendar import SessionCalendar
from ..storage.raw_store import RawFileStore
from ..storage.snapshot_source import FiiDiiCashSource, NsdlFpiDailySource
from .flows_block import DAYS_KEPT, FlowsInputs
from .flows_files import CashFlows, read_fii_dii, read_nsdl_equity


@dataclass(frozen=True)
class FrameInputs:
    next_session: date  # the session being predicted: the next one after the published session
    next_session_kind: str  # regular, special or muhurat


def frame_inputs(calendar: SessionCalendar, day: date) -> FrameInputs:
    following = calendar.next_session(day)
    return FrameInputs(following, calendar.session_kind(following))


class FlowsReader:
    def __init__(self, store: RawFileStore, calendar: SessionCalendar):
        self.store, self.calendar = store, calendar

    def on(self, day: date) -> FlowsInputs:
        sessions = self.calendar.sessions(day - timedelta(days=DAYS_KEPT * 2), day)[-DAYS_KEPT:]
        cash = self._latest(FiiDiiCashSource, day, _cash)
        nsdl = self._latest(NsdlFpiDailySource, day, _nsdl)
        return FlowsInputs(
            [cash[d] for d in sorted(cash)], [nsdl[d] for d in sorted(nsdl)], sessions,
        )  # fmt: skip

    def _latest(self, source, day: date, read: Callable[[bytes, str], tuple[date, object]]) -> dict[date, object]:
        """Session -> its latest archived copy's figures (copies read oldest first), for sessions up to `day`."""
        found: dict[date, object] = {}
        fetched, last_fetch = source.first_day, self.calendar.next_session(day)
        while fetched <= last_fetch:  # NSE serves a session's values until the next one's release: every copy of it
            data = self.store.get(source.path_for(fetched))
            if data is not None:
                covered, figures = read(data, source.FILENAME)
                if covered <= day:
                    found[covered] = figures
            fetched += timedelta(days=1)
        return found


def _cash(data: bytes, filename: str) -> tuple[date, CashFlows]:
    flows = read_fii_dii(data, filename)
    return flows.day, flows


def _nsdl(data: bytes, filename: str) -> tuple[date, tuple[date, float]]:
    day, net = read_nsdl_equity(data, filename)
    return day, (day, net)
