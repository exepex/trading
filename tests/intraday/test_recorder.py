"""Story A16 criteria 1, 2, 5, 7, 9 (heartbeat written) and 13 (outcomes): the recorder with fakes."""

from datetime import date, time, timedelta

import pytest

from fno.intraday.ledger import FIELDS
from fno.intraday.recorder import ALREADY, MISSED_NOW, NO_MARK, NOT_TRADING_DAY
from fno.intraday.slots import marks
from fno.quotes.recorder import MUHURAT_ONLY
from fno.research_data.calendar import CalendarError
from tests.intraday.fakes import DAY, FakeClock, build, ist


def test_the_session_loop_takes_exactly_the_26_marks_and_writes_the_session_rv(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, source, alerts, publisher, store = build(tmp_path, clock)
    outcomes = recorder.run(time(15, 35))
    assert [f"{m:%H:%M}" for m in source.taken] == [f"{m:%H:%M}" for m in marks(DAY)]
    assert len(source.taken) == 26 and source.taken[0].time() == time(9, 15) and source.taken[-1].time() == time(15, 30)
    assert [o.status for o in outcomes[:26]] == ["good"] * 26 and not alerts.sent
    rows = recorder.ledger.rows(DAY)
    assert [r["mark_ist"] for r in rows] == [f"{m:%H:%M}" for m in marks(DAY)] and list(rows[0]) == list(FIELDS)
    assert all(r["status"] == "good" and r["lateness_seconds"] == "1.0" for r in rows)
    assert any("realised variance written" in line for line in outcomes[25].lines)
    assert len(publisher.commits) == len(outcomes)  # every run commits its files
    assert recorder.heartbeat.read()["mark"] == "15:30"


def test_a_run_started_late_misses_the_mark_for_good_and_takes_the_next(tmp_path):
    clock = FakeClock(ist(DAY, 9, 17, 1))  # 121 s after 09:15
    recorder, source, *_ = build(tmp_path, clock)
    outcome = recorder.snapshot()
    assert outcome.mark == "09:30" and outcome.status == "good" and source.taken == [ist(DAY, 9, 30)]
    rows = recorder.ledger.rows(DAY)
    assert [(r["mark_ist"], r["status"], r["failures"]) for r in rows] == [
        ("09:15", "missed", "not_taken"), ("09:30", "good", "")
    ]  # fmt: skip


def test_at_the_120_second_boundary_the_mark_is_still_taken(tmp_path):
    clock = FakeClock(ist(DAY, 9, 17, 0))  # exactly mark + 120 s: the window is still open
    recorder, source, *_ = build(tmp_path, clock)
    recorder.snapshot()
    assert source.taken == [ist(DAY, 9, 15)]


def test_an_early_run_waits_for_its_mark_and_the_index_request_goes_out_on_it(tmp_path):
    clock = FakeClock(ist(DAY, 9, 0, 1))  # 14:59 before 09:15
    recorder, source, *_ = build(tmp_path, clock)
    outcome = recorder.snapshot()
    assert outcome.mark == "09:15" and source.prepared == [DAY]
    row = recorder.ledger.rows(DAY)[0]
    assert row["request_sent_at"] == "2026-10-15T03:45:00+00:00"  # UTC with offset (clock contract)


def test_more_than_15_minutes_early_takes_nothing(tmp_path):
    clock = FakeClock(ist(DAY, 8, 59, 59))
    recorder, source, *_ = build(tmp_path, clock)
    assert recorder.snapshot().status == NO_MARK and not source.taken


def test_a_mark_already_stored_is_not_taken_again(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, source, *_ = build(tmp_path, clock)
    recorder.snapshot()
    clock.moment = ist(DAY, 9, 14)  # a second host starting for the same mark
    outcome = recorder.snapshot()
    assert outcome.status == ALREADY and outcome.mark == "09:15" and len(source.taken) == 1
    assert len(recorder.ledger.rows(DAY)) == 1


def test_a_wait_that_overruns_the_window_records_a_miss(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, source, *_ = build(tmp_path, clock)
    source.prepare = lambda day: clock.advance(200)  # sign-in hangs past the mark's window
    outcome = recorder.snapshot()
    assert outcome.status == MISSED_NOW and not source.taken
    assert recorder.ledger.rows(DAY)[0]["status"] == "missed"


@pytest.mark.parametrize(
    "day, detail",
    [(date(2026, 10, 20), ""), (date(2026, 10, 18), ""), (date(2026, 11, 8), MUHURAT_ONLY)],
    ids=["weekday holiday", "sunday", "muhurat only"],
)
def test_days_that_are_not_recorded_sessions_record_nothing(tmp_path, day, detail):
    clock = FakeClock(ist(day, 9, 14))
    recorder, source, _, publisher, _ = build(tmp_path, clock)
    outcome = recorder.snapshot()
    assert (outcome.status, outcome.detail) == (NOT_TRADING_DAY, detail)
    assert not source.taken and not recorder.ledger.rows(day) and recorder.heartbeat.read() is None
    assert not publisher.commits


def test_a_special_saturday_session_is_recorded(tmp_path):
    saturday = date(2026, 10, 17)
    clock = FakeClock(ist(saturday, 9, 14))
    recorder, source, *_ = build(tmp_path, clock)
    assert recorder.snapshot().status == "good" and source.taken == [ist(saturday, 9, 15)]


def test_a_day_outside_the_calendar_raises(tmp_path):
    clock = FakeClock(ist(date(2027, 1, 4), 9, 14))
    recorder, *_ = build(tmp_path, clock)
    with pytest.raises(CalendarError):
        recorder.snapshot()


def test_two_bad_marks_in_a_row_alert_once_per_streak_and_a_repeat_is_not_bad(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    plans = {"09:30": "old", "09:45": "fail", "10:15": "repeat", "10:30": "slow", "10:45": "partial"}
    recorder, _, alerts, *_ = build(tmp_path, clock, plans)
    recorder.run(time(11, 5))
    rows = {r["mark_ist"]: r for r in recorder.ledger.rows(DAY)}
    assert [rows[m]["status"] for m in ("09:15", "09:30", "09:45", "10:00", "10:15", "10:30", "10:45", "11:00")] == [
        "good", "stale", "failed", "good", "good", "late", "incomplete", "good"
    ]  # fmt: skip
    assert rows["09:45"]["alert"].endswith("alert sent to #fno-desk") and rows["09:45"]["alert_at"]  # reached two
    assert alerts.sent[0].startswith("Action: check the 15-minute recorder")
    assert "09:30 stale (index_time_old)" in alerts.sent[0] and "09:45 failed (index_failed" in alerts.sent[0]
    assert rows["10:15"]["failures"] == "index_repeated" and rows["10:30"]["failures"] == "index_late"
    assert rows["10:30"]["alert"] == ""  # one bad mark alone
    assert rows["10:45"]["alert"] and len(alerts.sent) == 2  # reached two exactly 60 minutes after the first: sent


def test_a_new_streak_more_than_an_hour_later_alerts_again(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    plans = {"09:30": "old", "09:45": "old", "11:00": "old", "11:15": "old"}
    recorder, _, alerts, *_ = build(tmp_path, clock, plans)
    recorder.run(time(11, 20))
    assert len(alerts.sent) == 2 and "11:00" in alerts.sent[1]


def test_one_bad_mark_alone_sends_nothing(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, _, alerts, *_ = build(tmp_path, clock, {"09:30": "old"})
    recorder.run(time(10, 5))
    assert not alerts.sent


def test_a_silent_host_gap_is_recorded_as_missed_rows_and_alerted_by_the_next_run(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, _, alerts, *_ = build(tmp_path, clock)
    recorder.snapshot()
    clock.moment = ist(DAY, 10, 14)  # the host was away for 09:30, 09:45 and 10:00
    recorder.snapshot()
    statuses = [(r["mark_ist"], r["status"]) for r in recorder.ledger.rows(DAY)]
    assert statuses == [("09:15", "good"), ("09:30", "missed"), ("09:45", "missed"), ("10:00", "missed"),
                        ("10:15", "good")]  # fmt: skip
    assert len(alerts.sent) == 1 and "2 bad snapshots in a row on 2026-10-15: 09:30 missed" in alerts.sent[0]


def test_settling_a_finished_session_writes_every_missed_row_and_a_void_rv(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, *_ = build(tmp_path, clock)
    recorder.snapshot()
    clock.moment = ist(DAY, 16, 0)
    lines = recorder.settle_day(DAY)
    rows = recorder.ledger.rows(DAY)
    assert len(rows) == 26 and sum(r["status"] == "missed" for r in rows) == 25
    assert any("realised variance written: void" in line for line in lines)
    assert any("realised variance already written: void" in line for line in recorder.settle_day(DAY))  # once


def test_an_empty_session_settles_to_26_missed_rows(tmp_path):
    clock = FakeClock(ist(DAY, 16, 0))
    recorder, source, *_ = build(tmp_path, clock)
    recorder.settle_day(DAY)
    assert [r["status"] for r in recorder.ledger.rows(DAY)] == ["missed"] * 26 and not source.taken


def test_the_heartbeat_holds_utc_times_and_the_clock_reading(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, *_ = build(tmp_path, clock, skew=6.0)
    outcome = recorder.snapshot()
    beat = recorder.heartbeat.read()
    assert beat["run_started_at"] == "2026-10-15T03:44:00+00:00" and beat["clock_status"] == "clock_skew"
    assert any("clock WARNING: host vs github off by 6.0 s" in line for line in outcome.lines)
    assert recorder.ledger.rows(DAY)[0]["clock_status"] == "clock_skew"


def test_a_snapshot_stored_but_never_written_to_the_ledger_gets_its_row_later(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, *_ = build(tmp_path, clock)
    recorder.snapshot()
    recorder.ledger.path(DAY, ist(DAY, 9, 15)).unlink()  # the run stopped after saving to Drive
    clock.moment = ist(DAY, 9, 29)
    recorder.snapshot()
    assert [(r["mark_ist"], r["status"]) for r in recorder.ledger.rows(DAY)] == [("09:15", "good"), ("09:30", "good")]
    assert timedelta(0) <= clock.moment - ist(DAY, 9, 30)


def test_a_failed_send_does_not_count_and_is_retried_at_the_next_mark(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, _, alerts, *_ = build(tmp_path, clock, {"09:30": "old", "09:45": "old"})
    recorder.alerts.failing = alerts.failing = True
    recorder.run(time(9, 50))
    alerts.failing = False
    recorder.run(time(10, 5))
    rows = {r["mark_ist"]: r for r in recorder.ledger.rows(DAY)}
    assert len(alerts.sent) == 2 and "alert NOT sent: test" in rows["09:45"]["alert"]
    assert rows["10:00"]["alert"].endswith("alert sent to #fno-desk")  # the 09:30-09:45 streak, retried


def test_a_held_alert_is_sent_after_the_hour_even_when_its_streak_has_ended(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    plans = {"09:15": "old", "09:30": "old", "10:00": "old", "10:15": "old"}
    recorder, _, alerts, *_ = build(tmp_path, clock, plans)
    recorder.run(time(10, 20))
    assert len(alerts.sent) == 1  # 10:00-10:15 held: 45 minutes after the 09:30 alert
    recorder.run(time(10, 50))
    rows = {r["mark_ist"]: r for r in recorder.ledger.rows(DAY)}
    assert len(alerts.sent) == 2 and "10:00 stale" in alerts.sent[1] and rows["10:30"]["status"] == "good"
    assert rows["10:30"]["alert"] and rows["10:45"]["alert"] == ""
