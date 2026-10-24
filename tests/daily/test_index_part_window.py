"""DRY2 R1 (24 Oct): the indices part starts after NIFTY's commit, but never before its own early limit. A NIFTY part
that dies at 14:38 used to start A4c's index recorder at once; more than 20 minutes before 15:01 it is "too early",
records nothing, and the run never starts it again. Now the indices wait for their own time and record what they see."""

from datetime import date, datetime, time

from fno.daily.quote_parts import INDEX_EARLIEST_START, QUOTE_PARTS, QuoteParts
from fno.models import IST
from fno.quotes.indices import INDEX_WINDOW_START
from fno.quotes.recorder import MAX_EARLY_WAIT_SECONDS
from tests.timetable.fakes import Clock

from .fakes import FakeProcesses, RecordingCommitter, tracking

DAY = date(2026, 10, 23)
NIFTY, NSE, INDICES = (part.arguments for part in QUOTE_PARTS)


def _at(hour, minute):
    return datetime(2026, 10, 23, hour, minute, tzinfo=IST)


def test_the_indices_earliest_start_is_inside_a4c_s_early_limit():
    window, earliest = (datetime.combine(DAY, t, IST) for t in (INDEX_WINDOW_START, INDEX_EARLIEST_START))
    assert time(14, 44) == INDEX_EARLIEST_START and 0 < (window - earliest).total_seconds() < MAX_EARLY_WAIT_SECONDS


def test_a_nifty_part_that_dies_at_14_38_starts_the_indices_only_at_their_own_time(tmp_path):
    clock = Clock()
    clock.now = _at(14, 38)
    processes = FakeProcesses(clock, {NIFTY: (_at(14, 38), 1, []), NSE: (_at(15, 10), 0, []),
                                      INDICES: (_at(15, 13), 0, [])})  # fmt: skip
    parts = QuoteParts(QUOTE_PARTS, processes, RecordingCommitter(clock, []), lambda specs: [], _NoAlerts(), clock,
                       *tracking(tmp_path))  # fmt: skip
    parts.start(DAY)
    parts.service()  # NIFTY has died: its result is logged, so the indices may follow it, but not yet
    assert "nifty" in parts.results and [args for _, args in processes.started] == [NIFTY, NSE]
    assert parts.next_start() == datetime.combine(DAY, INDEX_EARLIEST_START, IST)  # a rehearsal's skip stops here
    clock.now = _at(14, 43)
    parts.service()
    assert len(processes.started) == 2
    clock.now = _at(14, 44)
    parts.start_due()  # any wait of the run starts it, without git
    assert [args for _, args in processes.started][-1] == INDICES and len(processes.started) == 3


def test_in_a_normal_day_the_indices_still_start_right_after_nifty_s_commit(tmp_path):
    clock = Clock()
    clock.now = _at(14, 38)
    processes = FakeProcesses(clock, {NIFTY: (_at(14, 57), 0, []), NSE: (_at(15, 10), 0, []),
                                      INDICES: (_at(15, 13), 0, [])})  # fmt: skip
    parts = QuoteParts(QUOTE_PARTS, processes, RecordingCommitter(clock, []), lambda specs: [], _NoAlerts(), clock,
                       *tracking(tmp_path))  # fmt: skip
    parts.start(DAY)
    clock.now = _at(14, 57)
    parts.service()
    assert [args for _, args in processes.started] == [NIFTY, NSE, INDICES]


class _NoAlerts:
    def send(self, text):
        return "alert sent"
