"""Common packs, execution schedules and NSE file stores for the data-check tests (story C3)."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta

from fno.checks.data_checks import CaptureRecord, ScheduledCapture
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


def file_hash(store, day: date, name: str) -> str:
    return hashlib.sha256(store.get(QuoteSnapshotRecorder.path(day, name))).hexdigest()


def committed_record(store, day: date, snapshot_id: str) -> CaptureRecord:
    """E3's role: the committed record of its execution capture, as the files stood when it was committed."""
    record = {
        "snapshot_id": snapshot_id,
        "csv_sha256": file_hash(store, day, f"{snapshot_id}.csv"),
        "meta_sha256": file_hash(store, day, f"{snapshot_id}.meta.json"),
        "source": "E3 record (test)",
    }
    return CaptureRecord(**record)


class ExecutionWindow(ExecutionSchedule):
    """E3's role: the execution capture `snapshot_id`, taken 15:10-15:20 IST (E4's fixtures capture at 15:15), with its
    committed capture record read from `store` (or the given record, or none)."""

    def __init__(self, snapshot_id="exec", store=None, record=None, start=time(15, 10), end=time(15, 20)):
        self.snapshot_id, self.store, self.record, self.start, self.end = snapshot_id, store, record, start, end

    def capture(self, pack: CommonPack) -> ScheduledCapture:
        start, end = (datetime.combine(pack.day, t, IST) for t in (self.start, self.end))
        record = self.record or (committed_record(self.store, pack.day, self.snapshot_id) if self.store else None)
        return ScheduledCapture(self.snapshot_id, start, end, record)


def pack_of(store, day: date, snapshot_id: str = "exec", spots=(SPOT,), close: float | None = CLOSE) -> CommonPack:
    """E2's pack shape (schema 2, story E2b): the A4 snapshot's provenance (its file and sidecar hashes), one
    `spot:<expiry>` item per chain, and the previous session's official close."""
    previous = CALENDAR.previous_session(day)
    items = [{"name": f"spot:{EXPIRY + timedelta(days=28 * n)}", "value": s} for n, s in enumerate(spots)]
    if close is not None:
        items.append({"name": f"close:{previous}", "value": {"nifty": close, "vix": 12.0}})
    provenance = {"snapshot_id": snapshot_id, "csv_sha256": file_hash(store, day, f"{snapshot_id}.csv"),
                  "meta_sha256": file_hash(store, day, f"{snapshot_id}.meta.json")}  # fmt: skip
    return CommonPack(day, {"day": day.isoformat(), "provenance": {SNAPSHOT_INPUT: provenance}, "items": items})


def nse_files(*days: date) -> DictStore:
    """A raw store holding NSE's F&O file of each of these days."""
    files = DictStore()
    for day in days:
        files.put(NseDailyFoSource.path_for(day), b"zip")
    return files


def gate(snapshots, alerts, day: date, schedule=None, shocks=None, nse=None) -> DataGate:
    """The real checks; the schedule defaults to E3's role for capture "exec" with its record read from the store."""
    nse = nse_files(CALENDAR.previous_session(day)) if nse is None else nse
    checks = build_data_checks([nse], CALENDAR, shocks)
    return DataGate(checks, snapshots, schedule or ExecutionWindow(store=snapshots.store), alerts)
