"""The reader tests' shared fakes (story MS-INS, part a): a dashcam that refuses writes and can damage a file, the
reader over fakes, a fixed "today", and a correction sealed on a later session."""

from datetime import date, datetime

from fno.school.constants import SLOT_1500, RecordKind, RoadCode
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.seal import StaleSeal
from fno.school.fakes import FakeDashcam, FakeSettlementSource
from fno.school.instructor.fakes import FakeSnapshotArchive
from fno.school.instructor.reader import PathReader, record_sha256
from tests.school.contracts.builders import IST
from tests.school.drivers.builders import WeekdayCalendar
from tests.school.instructor.builders import (
    ROAD,
    SESSIONS,
    refilled,
    snap,
)

LATER = date(2026, 11, 5)
CLOCK = FixedClock(datetime(2026, 11, 30, 21, 0, tzinfo=IST))  # "today": after every fixture's file
OTHER_ROAD = RoadCode.NIFTY_MONTHLY


class WriteRefusingDashcam(FakeDashcam):
    """The read-only proof: any seal after the fixtures are laid fails the test. A file named in `damaged` reads as
    the real store reads bytes that differ from their seal: `StaleSeal`."""

    locked = False
    damaged: frozenset = frozenset()

    def seal(self, *args, **kwargs):
        assert not self.locked, "the instructor wrote into the dashcam"
        return super().seal(*args, **kwargs)

    def read(self, seal):
        if any(seal.path.endswith(f"{d:%Y/%m/%d}/1500.{kind}.jsonl.gz") for d, kind in self.damaged):
            raise StaleSeal(seal.path)
        return super().read(seal)


def reader(dashcam, archive=None, settlements=None) -> PathReader:
    archive = archive or FakeSnapshotArchive({(ROAD, d): snap(d) for d in SESSIONS})
    dashcam.locked = True
    return PathReader(dashcam, archive, settlements or FakeSettlementSource(), WeekdayCalendar(), CLOCK)


def correct_later(dashcam, record, day=LATER, exit_price=12.05):
    fixed = refilled(record, exit_price, corrects=record_sha256(record))
    dashcam.locked = False
    dashcam.seal(day, SLOT_1500, RecordKind.OUTCOMES, (fixed,))  # its own session: the first file is never rewritten
    return fixed
