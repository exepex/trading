"""Inputs of India's market band and flows blocks (stories P10 and P8), read when a session is built: the session the
reader acts on next (from NSE's session calendar) and the archived flows copies (one per day fetched; the latest copy
of each session wins; only copies taken before the publication's own moment are read: no look-ahead, judge 66)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from hashlib import sha256

from ..research_data.calendar import SessionCalendar
from ..storage.raw_store import RawFileStore
from ..storage.snapshot_source import FiiDiiCashSource, NsdlFpiDailySource
from .flows_block import DAYS_KEPT, FlowsCopy, FlowsInputs
from .flows_files import CashFlows, read_fii_dii, read_nsdl_equity


@dataclass(frozen=True)
class FrameInputs:
    next_session: date  # the session being predicted: the next one after the published session
    next_session_kind: str  # regular, special or muhurat


def frame_inputs(calendar: SessionCalendar, day: date) -> FrameInputs:
    following = calendar.next_session(day)
    return FrameInputs(following, calendar.session_kind(following))


class FlowsReader:
    """A copy is filed under the IST day it was fetched, at any time of that day (flows-download at 21:10 IST, the
    07:10 IST market run, a hand run). Session D is published at 07:10 IST the next morning, so only copies filed on or
    before D are surely older than its publication; a copy filed the next day may be newer, and is never read for D.
    The archive keeps one copy per day (a different one is refused), so a re-run of D reads exactly the same copies."""

    def __init__(self, store: RawFileStore, calendar: SessionCalendar):
        self.store, self.calendar = store, calendar

    def on(self, day: date) -> FlowsInputs:
        sessions = self.calendar.sessions(day - timedelta(days=DAYS_KEPT * 2), day)[-DAYS_KEPT:]
        cash = self._latest(FiiDiiCashSource, day, _cash)
        nsdl = self._latest(NsdlFpiDailySource, day, _nsdl)
        copies = [copy for found in (cash, nsdl) for copy, _ in (found[d] for d in sorted(found))]
        return FlowsInputs(
            [cash[d][1] for d in sorted(cash)], [nsdl[d][1] for d in sorted(nsdl)], sessions, copies,
        )  # fmt: skip

    def _latest(self, source, day: date, read: Callable[[bytes, str], tuple[date, object]]) -> dict[date, tuple]:
        """Session -> (the copy, its figures) of its latest copy filed on or before `day` (copies read oldest first)."""
        found: dict[date, tuple] = {}
        filed = source.first_day
        while filed <= day:
            data = self.store.get(source.path_for(filed))
            if data is not None:
                covered, figures = read(data, source.FILENAME)
                if covered <= day:
                    found[covered] = (FlowsCopy(source.dataset, covered, filed, sha256(data).hexdigest()), figures)
            filed += timedelta(days=1)
        return found


def _cash(data: bytes, filename: str) -> tuple[date, CashFlows]:
    flows = read_fii_dii(data, filename)
    return flows.day, flows


def _nsdl(data: bytes, filename: str) -> tuple[date, tuple[date, float]]:
    day, net = read_nsdl_equity(data, filename)
    return day, (day, net)
