"""Story A16 criteria 5, 6, 7 and 9 when things break (review findings of the self-review): a source or store that
raises, `rv` on a day that is not finished, a realised-variance conflict, a previous session left unfinished, the
heartbeat on runs that take nothing, and a run started after --until."""

import hashlib
from datetime import date, time

import pytest

from fno.intraday.recorder import ALREADY, NO_MARK, SettleRefused
from fno.intraday.rv_table import FIELDS, RvTable
from fno.storage.raw_store import StoredCopyDamaged
from tests.intraday.fakes import DAY, FakeClock, build, ist

YESTERDAY = date(2026, 10, 14)


def test_a_source_that_raises_gives_a_failed_row_the_streak_alert_and_a_heartbeat(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, source, alerts, publisher, _ = build(tmp_path, clock)
    source.take = lambda day, mark: (_ for _ in ()).throw(ValueError("odd payload with PLANTED-SECRET"))
    outcomes = recorder.run(time(9, 35))
    rows = recorder.ledger.rows(DAY)
    assert [(r["status"], r["failures"]) for r in rows] == [("failed", "take: ValueError")] * 2
    assert [o.status for o in outcomes] == ["failed", "failed"] and len(alerts.sent) == 1
    assert recorder.heartbeat.read()["status"] == "failed" and len(publisher.commits) == 2
    assert "PLANTED" not in (tmp_path / "slots" / "2026" / "10" / "nifty_20261015.csv").read_text()


def test_a_store_that_raises_gives_a_failed_row_and_the_loop_goes_on(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, source, *_ = build(tmp_path, clock)
    put = recorder.store.put
    recorder.store.put = lambda path, data: (_ for _ in ()).throw(StoredCopyDamaged(path)) if "0915" in path else put(
        path, data)  # fmt: skip
    recorder.run(time(9, 35))
    assert [(r["mark_ist"], r["status"], r["failures"]) for r in recorder.ledger.rows(DAY)] == [
        ("09:15", "failed", "store: StoredCopyDamaged"), ("09:30", "good", "")
    ]  # fmt: skip


def test_rv_refuses_a_holiday_and_an_unfinished_session_and_writes_nothing(tmp_path):
    clock = FakeClock(ist(DAY, 12, 0))
    recorder, *_ = build(tmp_path, clock)
    with pytest.raises(SettleRefused, match="not a recorded session"):
        recorder.settle_day(date(2026, 10, 20))
    with pytest.raises(SettleRefused, match="has not finished"):
        recorder.settle_day(DAY)
    clock.moment = ist(DAY, 15, 32)  # exactly the 15:30 window's end: still not finished
    with pytest.raises(SettleRefused):
        recorder.settle_day(DAY)
    assert not recorder.ledger.rows(DAY) and not recorder.session_rv.table.rows()


def test_rv_without_a_day_settles_the_latest_finished_session(tmp_path):
    clock = FakeClock(ist(DAY, 12, 0))
    recorder, *_ = build(tmp_path, clock)
    recorder.settle_day()
    assert len(recorder.ledger.rows(YESTERDAY)) == 26 and not recorder.ledger.rows(DAY)
    clock.moment = ist(DAY, 15, 32, 1)
    recorder.settle_day()
    assert len(recorder.ledger.rows(DAY)) == 26


def test_a_realised_variance_conflict_is_alerted_and_the_heartbeat_and_commit_still_happen(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, _, alerts, publisher, _ = build(tmp_path, clock)
    RvTable(tmp_path).write_once({**dict.fromkeys(FIELDS, ""), "session": "2026-10-15", "method": "other"})
    outcomes = recorder.run(time(15, 35))
    last = outcomes[-1]
    assert any(line.startswith("Action: check the 15-minute recorder's realised variance") for line in last.lines)
    assert alerts.sent[-1].startswith("Action: check the 15-minute recorder's realised variance")
    assert recorder.heartbeat.read()["mark"] == "15:30" and len(publisher.commits) == len(outcomes)


def test_the_next_session_settles_a_previous_session_left_unfinished(tmp_path):
    clock = FakeClock(ist(YESTERDAY, 9, 10))
    recorder, *_ = build(tmp_path, clock)
    recorder.run(time(12, 5))  # the host died after 12:00
    clock.moment = ist(DAY, 9, 10)
    outcome = recorder.snapshot()
    assert len(recorder.ledger.rows(YESTERDAY)) == 26 and recorder.session_rv.has_row(YESTERDAY)
    assert any("2026-10-14 realised variance written: void" in line for line in outcome.lines)


def test_the_first_session_ever_does_not_settle_the_day_before_it(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, _, alerts, *_ = build(tmp_path, clock)
    recorder.snapshot()
    assert not recorder.ledger.rows(YESTERDAY) and not alerts.sent


def test_a_run_that_takes_nothing_keeps_the_last_marks_fields_in_the_heartbeat(tmp_path):
    clock = FakeClock(ist(DAY, 15, 29))
    recorder, *_ = build(tmp_path, clock, skew=0.4)
    recorder.snapshot()
    clock.moment = ist(DAY, 15, 31)
    assert recorder.snapshot().status == ALREADY
    beat = recorder.heartbeat.read()
    assert (beat["mark"], beat["status"], beat["clock_status"]) == ("15:30", "good", "clock_ok")
    assert beat["run_started_at"] == "2026-10-15T10:01:00+00:00"


def test_a_run_started_after_until_says_so(tmp_path):
    clock = FakeClock(ist(DAY, 10, 6))
    recorder, source, *_ = build(tmp_path, clock)
    [outcome] = recorder.run(time(10, 5))
    assert outcome.status == NO_MARK and "started after --until 10:05" in outcome.detail and not source.taken


def test_marks_another_host_already_took_do_not_end_the_loop(tmp_path):
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, source, *_ = build(tmp_path, clock)
    other, other_source, *_ = build(tmp_path, FakeClock(ist(DAY, 9, 10)))
    other.run(time(9, 50))  # another host took 09:15, 09:30 and 09:45 into the same store
    clock.moment = ist(DAY, 9, 31)
    recorder.run(time(10, 5))
    assert source.taken == [ist(DAY, 10, 0)]


def test_the_stored_first_version_is_what_the_row_describes(tmp_path):
    clock = FakeClock(ist(DAY, 9, 14))
    recorder, source, *_ = build(tmp_path, clock)
    path = recorder.settlement.path(DAY, ist(DAY, 9, 15))
    first = {}
    real_put = recorder.store.put

    def other_host_first(p, data):
        if not first:
            other = source.take(DAY, ist(DAY, 9, 15))
            other.two_sided_contracts = 1
            first["data"] = other.to_bytes()
            real_put(p, first["data"])
        real_put(p, data)

    recorder.store.put = other_host_first
    recorder.snapshot()
    row = recorder.ledger.rows(DAY)[0]
    assert row["raw_sha256"] == hashlib.sha256(first["data"]).hexdigest() and row["two_sided_contracts"] == "1"
    assert recorder.store.rows()[0]["path"] == path  # ours went to the revisions area
