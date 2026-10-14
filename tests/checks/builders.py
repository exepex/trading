"""Common packs, execution schedules and NSE file stores for the data-check tests (story C3)."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, time

from fno.checks.data_checks import ScheduledCapture
from fno.checks.gate import DataGate
from fno.checks.schedule import ExecutionSchedule
from fno.checks.wiring import build_data_checks
from fno.desk.common_pack import SNAPSHOT_INPUT, CommonPack
from fno.models import IST
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.storage.raw_source import NseDailyFoSource
from fno.storage.wiring import build_session_calendar
from tests.desk.builders import EXPIRY, DictStore

CALENDAR = build_session_calendar()
SPOT, CLOSE = 25_000.0, 24_900.0  # +0.40%


class ExecutionWindow(ExecutionSchedule):
    """E3's role: the execution capture `snapshot_id`, taken 15:10-15:20 IST (E4's fixtures capture at 15:15)."""

    def __init__(self, snapshot_id: str = "exec", start: time = time(15, 10), end: time = time(15, 20)):
        self.snapshot_id, self.start, self.end = snapshot_id, start, end

    def capture(self, pack: CommonPack) -> ScheduledCapture:
        start, end = (datetime.combine(pack.day, t, IST) for t in (self.start, self.end))
        return ScheduledCapture(self.snapshot_id, start, end)


def quote_hash(store, day: date, snapshot_id: str) -> str:
    return hashlib.sha256(store.get(QuoteSnapshotRecorder.path(day, f"{snapshot_id}.csv"))).hexdigest()


def pack_of(store, day: date, snapshot_id: str = "exec", spots=(SPOT,), close: float | None = CLOSE, sha=None,
            named: str | None = None) -> CommonPack:  # fmt: skip
    """E2's pack shape: the A4 snapshot's provenance (its quote file hash), option items carrying the spot, and the
    previous session's official close."""
    previous = CALENDAR.previous_session(day)
    items = [{"name": f"option:{EXPIRY}:{25000 + 100 * n:g}:CE", "value": {"spot": s}} for n, s in enumerate(spots)]
    if close is not None:
        items.append({"name": f"close:{previous}", "value": {"nifty": close, "vix": 12.0}})
    provenance = {"snapshot_id": named or snapshot_id, "csv_sha256": sha or quote_hash(store, day, snapshot_id)}
    return CommonPack(day, {"day": day.isoformat(), "provenance": {SNAPSHOT_INPUT: provenance}, "items": items})


def nse_files(*days: date) -> DictStore:
    """A raw store holding NSE's F&O file of each of these days."""
    files = DictStore()
    for day in days:
        files.put(NseDailyFoSource.path_for(day), b"zip")
    return files


def gate(snapshots, alerts, day: date, schedule=None, shocks=None, nse=None) -> DataGate:
    nse = nse_files(CALENDAR.previous_session(day)) if nse is None else nse
    checks = build_data_checks([nse], CALENDAR, shocks)
    return DataGate(checks, snapshots, schedule or ExecutionWindow(), alerts)
