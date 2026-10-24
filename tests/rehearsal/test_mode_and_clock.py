"""REH1: the rehearsal's identity travels to children in one variable; the replay clock is one offset file shared by
every process, started at the routine's time on the day, and only ever moves forward."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.clock import ReplayClock
from fno.rehearsal.mode import Rehearsal, rehearsal

DAY = date(2026, 10, 23)


def test_the_mode_round_trips_through_the_environment_and_names_its_places(tmp_path):
    mode = Rehearsal.new(DAY, tmp_path / "home", tmp_path / "record")
    again = rehearsal({ENV_FNO_REHEARSAL: mode.to_env()})
    assert again == mode and rehearsal({}) is None
    assert mode.branch == f"rehearsal/2026-10-23-{mode.run_id}" and mode.drive_root == f"dryrun/{mode.run_id}"
    assert mode.label.startswith("*DRY RUN, 2026-10-23 replay, not a real trading day*\nNot yet in rehearsal: ")
    assert Rehearsal.new(DAY, tmp_path, tmp_path).run_id != mode.run_id


class Wall:
    def __init__(self):
        self.now = datetime(2026, 10, 24, 6, 0, tzinfo=UTC)

    def __call__(self):
        return self.now


def test_two_processes_reading_one_clock_file_agree_and_a_jump_moves_both(tmp_path):
    wall = Wall()
    start = datetime(2026, 10, 23, 8, 35, tzinfo=UTC)  # 14:05 IST
    parent, child = ReplayClock(tmp_path, wall), ReplayClock(tmp_path, wall)
    parent.start(start)
    assert parent() == child() == start
    wall.now += timedelta(seconds=30)  # real time runs between jumps
    assert child() == start + timedelta(seconds=30)
    parent.jump_to(datetime(2026, 10, 23, 9, 28, tzinfo=UTC))  # the desk's 14:58
    assert child() == datetime(2026, 10, 23, 9, 28, tzinfo=UTC)
    parent.jump_to(start)  # a moment already past: never back
    assert child() == datetime(2026, 10, 23, 9, 28, tzinfo=UTC)
    assert not list(Path(tmp_path).glob("*.tmp"))  # each write lands whole
