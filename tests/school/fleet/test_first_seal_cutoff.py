"""Story MS-P1j3: the runner makes no first seal of a session after the slot's last start (15:25 IST) in RECORD mode,
since law 6 would then refuse every fill; a sealed session, a replay and a closed day run as before."""

from datetime import UTC, datetime, time, timedelta

import pytest

from fno.daily.wiring import SCHOOL_STARTS_BY
from fno.models import IST
from fno.school.constants import FLEET_STOPPED, SLOT_LAST_START
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.fleet import RunMode
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.ledgers import open_positions
from fno.school.fleet.runner import FIRST_SEAL_TOO_LATE
from tests.school.contracts import builders as b
from tests.school.fleet.rig import DAY2, Rig, all_roads
from tests.school.fleet.test_runner import expiring_rig

LAWS = (FakeMaxLossLaw(10_000),)
STOP_START = FIRST_SEAL_TOO_LATE.split("{")[0]


def rig_at(tmp_path, at: datetime) -> Rig:
    rig = Rig(tmp_path, (FakeDriver(all_roads("CS1"), b.put_spread()),), LAWS)
    rig.fleet.clock = FixedClock(at)
    return rig


def on(session, hour, minute, second=0, micro=0) -> datetime:
    return datetime.combine(session, time(hour, minute, second, micro), IST)


def nothing_written(rig: Rig) -> bool:
    accounts = rig.accounts.ledgers == {} and rig.ticket_accounts.ledgers == {}
    return rig.dashcam.files == {} and accounts and not any(rig.root.rglob("*"))


@pytest.mark.parametrize("at", [on(b.SESSION, 15, 4), on(b.SESSION, 15, 25)])
def test_a_first_run_by_the_last_start_seals_and_fills(tmp_path, at):
    rig = rig_at(tmp_path, at)
    run = rig.fleet.run(b.SESSION, RunMode.RECORD)
    assert run.status == "" and run.decisions and rig.dashcam.files and len(rig.accounts.ledgers["CS1@1"]) == 1


@pytest.mark.parametrize(
    "at",
    [on(b.SESSION, 15, 25, 0, 1), on(b.SESSION, 15, 45), on(b.SESSION + timedelta(days=1), 10, 0)],
    ids=["one microsecond late", "after the close", "the next day"],
)
def test_a_later_first_run_seals_settles_fills_and_writes_nothing_and_stops_loudly(tmp_path, at):
    rig = rig_at(tmp_path, at)
    run = rig.fleet.run(b.SESSION, RunMode.RECORD)
    assert run.status == FIRST_SEAL_TOO_LATE.format(now=at, by=SLOT_LAST_START, session=b.SESSION)
    assert run.status.startswith(FLEET_STOPPED) and run.decisions == () and run.fills == ()
    assert nothing_written(rig)


def test_the_message_reads_as_the_person_sees_it(tmp_path):
    run = rig_at(tmp_path, on(b.SESSION, 15, 45)).fleet.run(b.SESSION, RunMode.RECORD)
    assert run.status == (f"stopped: too late for a first seal: 15:45:00 IST is after the slot's last start, 15:25 IST "
                          f"on {b.SESSION}; nothing sealed")  # fmt: skip


def test_a_utc_clock_is_compared_in_ist(tmp_path):
    last = on(b.SESSION, 15, 25).astimezone(UTC)
    assert rig_at(tmp_path / "a", last).fleet.run(b.SESSION, RunMode.RECORD).status == ""
    late = rig_at(tmp_path / "b", last + timedelta(seconds=1)).fleet.run(b.SESSION, RunMode.RECORD)
    assert late.status.startswith(STOP_START)


def test_a_replay_is_never_refused(tmp_path):
    rig = rig_at(tmp_path, on(b.SESSION, 15, 45))
    run = rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert run.status == "" and run.decisions and rig.dashcam.files


def test_a_session_already_sealed_reruns_after_the_last_start_as_before(tmp_path):
    rig = rig_at(tmp_path, on(b.SESSION, 15, 4))
    first = rig.fleet.run(b.SESSION, RunMode.RECORD)
    sealed = dict(rig.dashcam.files)
    rig.fleet.clock = FixedClock(on(b.SESSION, 15, 45))
    again = rig.fleet.run(b.SESSION, RunMode.RECORD)
    assert not again.status.startswith(STOP_START) and again.decisions == first.decisions
    assert rig.dashcam.files == sealed and len(rig.accounts.ledgers["CS1@1"]) == 1


def test_a_session_with_nothing_scheduled_prints_its_own_line_whatever_the_hour(tmp_path):
    rig = rig_at(tmp_path, on(DAY2, 15, 45))
    rig.fleet.catalogue.days = {}  # no road listed for the session: a closed day
    run = rig.fleet.run(DAY2, RunMode.RECORD)
    assert run.status == "" and run.decisions == () and nothing_written(rig)


class MovingClock:
    """A clock that reads `first` until the captures are read, then `later` (the snapshot source moves it)."""

    def __init__(self, first: datetime, later: datetime):
        self.at, self.later = first, later

    def now(self) -> datetime:
        return self.at


def test_a_run_started_by_the_last_start_seals_even_if_reading_the_captures_crosses_it(tmp_path):
    rig = rig_at(tmp_path, on(b.SESSION, 15, 4))
    clock = rig.fleet.clock = MovingClock(on(b.SESSION, 15, 25), on(b.SESSION, 15, 26))
    read = rig.fleet.snapshots.for_road

    def slow_read(*args, **kwargs):
        clock.at = clock.later  # reading the captures took past the last start
        return read(*args, **kwargs)

    rig.fleet.snapshots.for_road = slow_read
    assert rig.fleet.run(b.SESSION, RunMode.RECORD).status == "" and rig.dashcam.files
    assert clock.at == clock.later  # the captures really were read after the start


def test_a_late_first_run_settles_no_expired_position(tmp_path):
    """The check sits before `settle_expired`: an expired position stays open, its exit unsealed, for an in-time run."""
    rig, later = expiring_rig(tmp_path)
    held = {driver: list(rows) for driver, rows in rig.accounts.ledgers.items()}
    rig.fleet.clock = FixedClock(on(later, 15, 45))
    run = rig.fleet.run(later, RunMode.RECORD)
    assert run.status.startswith(STOP_START) and rig.accounts.ledgers == held
    assert open_positions(tuple(rig.accounts.ledgers["CS1@1"]))  # still open: nothing settled
    assert all(key[0] != later for key in rig.dashcam.files)


def test_a_late_first_run_on_a_day_whose_roads_all_closed_is_refused_too(tmp_path):
    """Criterion 1 as written: a scheduled session, even of closed roads only, makes no first seal after 15:25."""
    rig = Rig(tmp_path, (FakeDriver(all_roads("CS1"), b.put_spread()),), LAWS, open_roads=())
    rig.fleet.clock = FixedClock(on(b.SESSION, 15, 45))
    run = rig.fleet.run(b.SESSION, RunMode.RECORD)
    assert run.status.startswith(STOP_START) and nothing_written(rig)


def test_the_daily_step_and_the_runner_share_one_last_start():
    assert SCHOOL_STARTS_BY is SLOT_LAST_START == time(15, 25)


@pytest.fixture
def replay_clock(monkeypatch, tmp_path):
    """REH1's own replay clock, installed as a rehearsing process installs it (`rehearsal/process.py`); the package's
    clock is restored after the test."""
    from fno import models
    from fno.rehearsal.clock import ReplayClock

    monkeypatch.setattr(models, "_clock", models._clock)  # restored at the end
    clock = ReplayClock(tmp_path / "state")
    models.install_clock(clock)
    return clock


def test_a_rehearsed_past_session_seals_by_its_replayed_last_start_and_not_after(tmp_path, replay_clock):
    """Criterion 3's rehearsal clause, on the clock the record root wires (`wiring.IstClock`, judge 627 SF1)."""
    from fno.school.wiring import IstClock

    replay_clock.start(on(b.SESSION, 15, 20))
    wired = IstClock()
    assert abs((wired.now() - on(b.SESSION, 15, 20)).total_seconds()) < 60  # the replayed day, not today
    rig = rig_at(tmp_path / "in time", on(b.SESSION, 15, 4))
    rig.fleet.clock = wired
    assert rig.fleet.run(b.SESSION, RunMode.RECORD).status == "" and rig.dashcam.files
    replay_clock.jump_to(on(b.SESSION, 15, 26))
    late = rig_at(tmp_path / "late", on(b.SESSION, 15, 4))
    late.fleet.clock = wired
    assert late.fleet.run(b.SESSION, RunMode.RECORD).status.startswith(STOP_START) and nothing_written(late)
