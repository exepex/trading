"""Test doubles for the P0b probe: the dry run's made-up sources with faults planted on chosen calls, a recording
alert sender and publisher, and a builder for a slot runner and a day over them."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fno.capture_probes.archive import SlotArchive
from fno.capture_probes.constants import DRIVE_AREA, MIN_GAP_SECONDS, Source
from fno.capture_probes.counts import CountsFolder
from fno.capture_probes.day import ProbeDay
from fno.capture_probes.dry_run import JumpingClock, MadeUpGroww, MadeUpNse, MadeUpResponse, made_up_lot
from fno.capture_probes.groww_reader import GrowwAnswers, GrowwReader
from fno.capture_probes.nse_reader import NseGet, NseReader
from fno.capture_probes.pace import StudyPace
from fno.capture_probes.publish import Publisher
from fno.capture_probes.slot import SlotRunner, SlotTools
from fno.capture_probes.stops import StopRecorder
from fno.health.capture_errors import CaptureErrorLog
from fno.storage.raw_store import RawFileConflict

SESSION = date(2026, 10, 29)


class GrowwError(Exception):
    def __init__(self, code: str = "", message: str = "SECRET-IN-MESSAGE"):
        super().__init__(message)
        self.code = code


class GrowwRateLimitedStub(GrowwError):
    """Stands in for GW1's GrowwRateLimited."""


class FaultyGroww(MadeUpGroww):
    """Raises `faults[n]` on the n-th call (1-based), else answers as the dry run does; counts every call."""

    def __init__(self, clock, session, faults=None):
        super().__init__(clock, session)
        self.faults, self.calls = dict(faults or {}), 0

    def _maybe_fail(self):
        self.calls += 1
        if self.calls in self.faults:
            raise self.faults[self.calls]

    def get_expiries(self, **kw):
        self._maybe_fail()
        return super().get_expiries(**kw)

    def get_quote(self, **kw):
        self._maybe_fail()
        return super().get_quote(**kw)

    def get_option_chain(self, **kw):
        self._maybe_fail()
        return super().get_option_chain(**kw)


class FaultyNse(MadeUpNse):
    """Answers `faults[n]` (a response) on the n-th GET; records every method and header used."""

    def __init__(self, clock, session, faults=None):
        super().__init__(clock, session)
        self.faults, self.calls, self.sent_headers = dict(faults or {}), 0, []

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        self.sent_headers.append(dict(self.headers))
        if self.calls in self.faults:
            self.clock.sleep(0.2)
            fault = self.faults[self.calls]
            if isinstance(fault, BaseException):
                raise fault
            return fault
        return super().get(url, params, timeout)


def status(code: int) -> MadeUpResponse:
    return MadeUpResponse({}, status=code)


class RecordingAlerts:
    def __init__(self):
        self.sent = []

    def send(self, text: str) -> str:
        self.sent.append(text)
        return "alert sent"


class RecordingPublisher(Publisher):
    def __init__(self, fail_on: tuple[int, ...] = ()):
        self.calls, self.fail_on = [], fail_on

    def publish(self, what: str) -> str | None:
        self.calls.append(what)
        return "p0b records NOT committed: push failed: refused" if len(self.calls) in self.fail_on else None


class MemoryStore:
    def __init__(self, conflict: bool = False, fail: bool = False):
        self.files, self.conflict, self.fail = {}, conflict, fail

    def put(self, path: str, data: bytes):
        if self.conflict:
            raise RawFileConflict(path)
        if self.fail:
            raise OSError("drive down")
        self.files[path] = data


def is_rate_limited(error: Exception) -> bool:
    return isinstance(error, GrowwRateLimitedStub)


class Rig:
    """One probe day over planted faults; everything it writes is under `folder` or in memory."""

    def __init__(self, folder: Path, groww_faults=None, nse_faults=None, publisher=None, store=None,
                 start=None, trading=True, lot=made_up_lot):  # fmt: skip
        self.clock = JumpingClock(SESSION, start)
        self.groww = FaultyGroww(self.clock, SESSION, groww_faults)
        self.nse = FaultyNse(self.clock, SESSION, nse_faults)
        self.alerts, self.publisher = RecordingAlerts(), publisher or RecordingPublisher()
        self.store = store or MemoryStore()
        self.log = CaptureErrorLog(folder / "capture_errors.csv")
        paces = {s: StudyPace(MIN_GAP_SECONDS[s], self.clock.timer, self.clock.sleep) for s in Source}
        self.tools = SlotTools(GrowwReader(self.groww, GrowwAnswers(is_rate_limited), lot, self.clock.wall),
                               NseReader(NseGet(self.nse), lot, self.clock.wall), paces, self.clock.wall,
                               self.clock.timer, self.clock.sleep, SlotArchive(self.store, DRIVE_AREA),
                               CountsFolder(folder / "counts"), self.publisher,
                               StopRecorder(self.alerts, self.log))  # fmt: skip
        self.runner = SlotRunner(self.tools)
        self.day = ProbeDay(lambda day: trading, self.tools.folder, self.runner, self.clock.wall, self.clock.sleep)

    def run(self, session: date = SESSION) -> tuple[int, list[str]]:
        lines: list[str] = []
        code = self.day.run(session, lines.append)
        return code, lines

    def counts(self):
        return self.tools.folder.read(SESSION)
