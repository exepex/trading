"""Criteria 4b and 5 (story MS-P0b): the days and times the probe refuses, and its stop for good."""

from datetime import date, time, timedelta

import pytest

from fno.school.probes.constants import BLACKOUT_DAYS, MAX_SESSIONS, SLOTS, Source
from fno.school.probes.counts import DayCounts, SourceSlot

from .fakes import SESSION, Rig, status


def earlier_session(rig, day: date, stops=None):
    rig.tools.folder.write(DayCounts(str(day), {"10:07": {Source.NSE: SourceSlot(reserved=11, used=11)}},
                                     dict(stops or {})))  # fmt: skip


def test_a_full_day_runs_its_four_slots_and_ends_clean(tmp_path):
    rig = Rig(tmp_path)
    code, lines = rig.run()
    assert code == 0 and lines[-1] == "p0b 2026-10-29: done, 206 Groww and 44 NSE requests"
    assert list(rig.counts().slots) == [s.strftime("%H:%M") for s in SLOTS]


def test_a_non_trading_day_reads_nothing(tmp_path):
    rig = Rig(tmp_path, trading=False)
    assert rig.run() == (0, ["p0b: not a trading day; nothing read"]) and rig.groww.calls == 0


@pytest.mark.parametrize("day", sorted(BLACKOUT_DAYS))
def test_each_kept_clear_day_reads_nothing(tmp_path, day):
    rig = Rig(tmp_path)
    code, lines = rig.run(day)
    assert lines == [f"p0b: {day} is kept clear for v4 and A16h; nothing read"] and rig.nse.calls == 0


def test_a_sixth_session_is_refused_but_a_rerun_of_a_fifth_is_not(tmp_path):
    rig = Rig(tmp_path)
    for k in range(MAX_SESSIONS):
        earlier_session(rig, SESSION - timedelta(days=k + 1))
    assert rig.run() == (1, ["p0b: 5 sessions already captured; a sixth needs the owner"])
    rig.tools.folder.write(DayCounts(str(SESSION), {"10:07": {}}))  # today already started: a rerun goes on
    code, lines = rig.run()
    assert "a sixth" not in " ".join(lines)


def test_four_earlier_sessions_still_allow_a_fifth(tmp_path):
    rig = Rig(tmp_path)
    for k in range(MAX_SESSIONS - 1):
        earlier_session(rig, SESSION - timedelta(days=k + 1))
    assert rig.run()[0] == 0


def test_a_source_stopped_on_two_sessions_is_stopped_for_good(tmp_path):
    rig = Rig(tmp_path)
    for k in (1, 2):
        earlier_session(rig, SESSION - timedelta(days=k), {Source.NSE: "p0b nse stopped"})
    code, lines = rig.run()
    assert "p0b nse stopped for good: blocked on 2 sessions; the owner decides" in lines
    assert rig.nse.calls == 0 and rig.groww.calls > 0 and code == 1


def test_one_stopped_session_is_not_yet_for_good(tmp_path):
    rig = Rig(tmp_path)
    earlier_session(rig, SESSION - timedelta(days=1), {Source.NSE: "p0b nse stopped"})
    rig.run()
    assert rig.nse.calls > 0


def test_a_slot_more_than_2_min_late_is_skipped_and_one_at_2_min_runs(tmp_path):
    rig = Rig(tmp_path, start=time(10, 9, 1))
    code, lines = rig.run()
    assert lines[0] == "p0b slot 10:07: skipped, more than 2 min late" and "10:07" not in rig.counts().slots
    rig = Rig(tmp_path / "b", start=time(10, 9))
    rig.run()
    assert "10:07" in rig.counts().slots


def test_a_slot_already_counted_is_never_run_again(tmp_path):
    rig = Rig(tmp_path)
    rig.run()
    calls = rig.groww.calls
    rig.run()
    assert rig.groww.calls == calls


def test_a_slot_stops_hard_at_six_minutes_with_its_unread_rows_missing(tmp_path):
    slow = {n: status(503) for n in range(2, 12)}  # NSE answers 5xx: retries eat the clock
    rig = Rig(tmp_path, nse_faults=slow)
    rig.tools.paces[Source.NSE].gap = 40.0  # each request 40 s apart: 6 minutes hold about 9
    rig.run()
    entry = rig.counts().slots["10:07"][Source.NSE]
    assert entry.used < 11 and entry.quality["missing"] > 0
    assert rig.clock.wall().time() >= time(14, 7)  # the day went on to its later slots
