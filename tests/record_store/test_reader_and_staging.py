"""Story DR1: readers read only through the record (verified bytes plus the as-seen pointer), and staging gives every
writer its own name, so two writers of one session never meet on a name."""

from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from fno.close_read.constants import READ
from fno.record_store.cli import cmd_certify, cmd_read
from fno.record_store.constants import CERTIFIED, PROVISIONAL
from fno.record_store.reader import NotRecorded, RecordReader
from fno.record_store.staging import StagingArea
from fno.storage.data_store import DataStore
from fno.storage.wiring import build_session_calendar
from tests.record_store.helpers import SESSION, World, answer


@pytest.fixture
def world(tmp_path):
    world = World(tmp_path)
    world.a4h_saves(READ, answer())
    return world


def test_a_provisional_need_is_served_and_points_at_the_exact_bytes(world):
    world.certifier().certify(SESSION, PROVISIONAL)
    seen = RecordReader(world.records, world.drive).read("closes", SESSION, PROVISIONAL)
    assert seen.data == answer() and seen.as_seen.level == PROVISIONAL
    assert seen.as_seen.path == "data/closes/2026/10/2026-10-23.first.raw.json"


def test_a_certified_record_serves_a_provisional_need_but_never_the_reverse(world):
    reader = RecordReader(world.records, world.drive)
    world.certifier().certify(SESSION, PROVISIONAL)
    with pytest.raises(NotRecorded, match="no certified record"):
        reader.read("closes", SESSION, CERTIFIED)
    world.certifier().certify(SESSION, CERTIFIED)
    assert reader.read("closes", SESSION, PROVISIONAL).as_seen.level == CERTIFIED


def test_a_record_whose_bytes_changed_is_refused_by_name(world, tmp_path):
    world.certifier().certify(SESSION, PROVISIONAL)
    (tmp_path / "drive/data/closes/2026/10/2026-10-23.first.raw.json").write_bytes(b"{}")
    with pytest.raises(NotRecorded, match="other bytes than recorded"):
        RecordReader(world.records, world.drive).read("closes", SESSION, PROVISIONAL)


def test_two_writers_staging_one_session_in_the_same_second_get_two_names(world):
    clock = lambda: datetime(2026, 10, 23, 10, 10, 6, tzinfo=UTC)  # noqa: E731
    areas = [StagingArea("closes", DataStore(world.drive, "data", world.receipts, "closeread", run, clock),
                         world.receipts, clock) for run in ("run-a", "run-b")]  # fmt: skip
    first, second = (area.stage(SESSION, data, ".json") for area, data in zip(areas, (b"a", b"b"), strict=True))
    assert first.path != second.path and first.path.startswith("data/staging/closes/2026-10-23/20261023T101006")
    assert [v.path for v in areas[0].versions(SESSION)] == sorted([first.path, second.path])


def test_the_commands_print_one_line_and_exit_1_when_not_recorded(world):
    lines = []
    args = SimpleNamespace(dataset="closes", day=SESSION, level=PROVISIONAL, commit=False)
    assert cmd_read(args, lines.append, RecordReader(world.records, world.drive)) == 1
    assert cmd_certify(args, lines.append, world.certifier()) == 0
    assert cmd_read(args, lines.append, RecordReader(world.records, world.drive)) == 0
    assert lines[0] == "closes 2026-10-23: no provisional record"
    assert lines[-1].startswith("closes 2026-10-23 provisional: data/closes/2026/10/2026-10-23.first.raw.json sha256 ")


def test_since_certifies_every_session_of_the_window_and_fails_while_one_is_missing(world):
    class Calendar:
        def sessions(self, start, end):
            assert (start.isoformat(), end.isoformat()) == ("2026-10-22", SESSION)  # not before the live date
            return [start, end]

    lines = []
    args = SimpleNamespace(dataset="closes", day=SESSION, level=PROVISIONAL, since=7, commit=False)
    assert cmd_certify(args, lines.append, world.certifier(), calendar=Calendar()) == 1
    assert lines[0] == "closes 2026-10-22 provisional: NOT recorded: no staged version"
    assert lines[1].startswith("closes 2026-10-23 provisional: recorded ")


class Recorded:
    """A certifier that has every session it is asked for (only the window is under test)."""

    def __init__(self):
        self.rules, self.asked = SimpleNamespace(live_from=date(2026, 10, 1)), []

    def certify(self, session, level):
        self.asked.append(session)
        return SimpleNamespace(line=f"closes {session} {level}: already recorded", recorded=True, alert=False)


@pytest.mark.parametrize(
    "morning, last",
    [
        ("2026-10-23", "2026-10-22"),  # a trading morning: today's certified record is due tomorrow
        ("2026-10-26", "2026-10-23"),  # a Monday: the previous session is Friday
        ("2026-10-21", "2026-10-19"),  # the day after NSE's 20 Oct holiday
    ],
)
def test_the_morning_certified_catch_up_ends_at_the_previous_session(morning, last):
    """Judge 546 SF1, on NSE's real calendar: every earlier session recorded means exit 0 and no line for today."""
    certifier, lines = Recorded(), []
    args = SimpleNamespace(dataset="closes", day=morning, level=CERTIFIED, since=7, commit=False)
    assert cmd_certify(args, lines.append, certifier, calendar=build_session_calendar()) == 0
    assert certifier.asked[-1] == last and morning not in certifier.asked
    assert not any(morning in line for line in lines)


def test_the_evening_provisional_catch_up_includes_today():
    certifier = Recorded()
    args = SimpleNamespace(dataset="closes", day="2026-10-23", level=PROVISIONAL, since=7, commit=False)
    assert cmd_certify(args, [].append, certifier, calendar=build_session_calendar()) == 0
    assert certifier.asked[-1] == "2026-10-23"


def test_a_catch_up_with_a_source_down_sends_one_alert_naming_every_session():
    """Judge 561's note: `--since 7` with a store down alerted once per session."""

    class Down:
        rules = SimpleNamespace(live_from=date(2026, 10, 1))

        def certify(self, session, level):
            line = f"closes {session} {level}: NOT recorded: a source could not be read: down; nothing is certified"
            return SimpleNamespace(line=line, recorded=False, alert=True)

    class Alerts:
        def __init__(self):
            self.sent = []

        def send(self, text):
            self.sent.append(text)
            return "sent"

    alerts = Alerts()
    args = SimpleNamespace(dataset="closes", day="2026-10-26", level=CERTIFIED, since=7, commit=False)
    assert cmd_certify(args, [].append, Down(), alerts, build_session_calendar()) == 1
    (text,) = alerts.sent
    assert text.startswith("Omenix F&O records: closes 2026-10-19 certified") and text.count("NOT recorded") == 4
