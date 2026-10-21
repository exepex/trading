"""Story A16 criterion 6: the realised variance's definition (design 5.2), its units and the void rule; and the
session row computed from stored snapshots, written once."""

import math
from datetime import date, time
from types import SimpleNamespace

import pytest

from fno.intraday.realised_vol import QuoteSnapshotRv15m
from fno.intraday.rv_table import RvConflict
from fno.intraday.session_rv import previous_recorded_session
from fno.intraday.slots import marks
from tests.intraday.fakes import DAY, FakeClock, build, calendar, ist, level_at

LEVELS = [25000.0 * (1 + 0.001 * k * (-1) ** k) for k in range(26)]  # a zig-zag path, 26 levels


def test_the_intraday_part_sums_25_squared_log_returns_and_the_overnight_part_is_separate():
    result = QuoteSnapshotRv15m().compute(LEVELS, 24900.0)
    by_hand = sum(math.log(LEVELS[k] / LEVELS[k - 1]) ** 2 for k in range(1, 26))
    assert result.intraday == pytest.approx(by_hand, rel=1e-12)
    assert result.overnight == pytest.approx(math.log(25000 / 24900) ** 2, rel=1e-12)
    assert result.session == pytest.approx(by_hand + math.log(25000 / 24900) ** 2, rel=1e-12)
    assert result.vol_pct == pytest.approx(100 * math.sqrt(result.session))


def test_units_one_percent_session_is_rv_0_0001():
    flat = [100.0] * 26
    result = QuoteSnapshotRv15m().compute(flat, 100.0 / math.exp(0.01))  # a 1% log move overnight only
    assert result.session == pytest.approx(0.0001) and result.vol_pct == pytest.approx(1.0)


@pytest.mark.parametrize("missing", [0, 12, 25])
def test_any_missing_level_voids_the_intraday_part_never_interpolated(missing):
    levels = list(LEVELS)
    levels[missing] = None
    result = QuoteSnapshotRv15m().compute(levels, 24900.0)
    assert result.intraday is None and result.session is None and result.unusable_marks == (missing,)
    assert (result.overnight is None) == (missing == 0)  # 09:15 is the overnight part's end


def test_no_previous_close_voids_only_the_overnight_part():
    result = QuoteSnapshotRv15m().compute(LEVELS, None)
    assert result.intraday is not None and result.overnight is None and result.session is None
    assert result.previous_close_missing


@pytest.mark.parametrize("count", [0, 25, 27])
def test_anything_but_26_levels_is_refused(count):
    with pytest.raises(ValueError):
        QuoteSnapshotRv15m().compute([100.0] * count, 100.0)


def _two_sessions(tmp_path, plans=None):
    """Records 14 Oct and 15 Oct fully through the recorder, then returns the 15 Oct row and the recorder."""
    clock = FakeClock(ist(date(2026, 10, 14), 9, 10))
    recorder, *_ = build(tmp_path, clock, plans)
    recorder.run(time(15, 35))
    clock.moment = ist(DAY, 9, 10)
    recorder.run(time(15, 35))
    return {r["session"]: r for r in recorder.session_rv.table.rows()}, recorder


def test_the_session_row_matches_a_hand_computation_from_the_stored_levels(tmp_path):
    rows, _ = _two_sessions(tmp_path)
    row = rows["2026-10-15"]
    levels = [level_at(mark) for mark in marks(DAY)]
    previous = level_at(ist(date(2026, 10, 14), 15, 30))
    intraday = sum(math.log(levels[k] / levels[k - 1]) ** 2 for k in range(1, 26))
    overnight = math.log(levels[0] / previous) ** 2
    assert row["status"] == "ok" and row["void_reason"] == "" and row["good_slots"] == "26"
    assert float(row["rv_intraday"]) == pytest.approx(intraday, abs=1e-10)
    assert float(row["rv_overnight"]) == pytest.approx(overnight, abs=1e-10)
    assert float(row["rv_session"]) == pytest.approx(intraday + overnight, abs=1e-10)
    assert row["as_of"] == "2026-10-15T10:00:00+00:00" and row["method"] == "rv-quote-15m-v1"
    assert row["measure"] == "quote_snapshot" and len(row["inputs_sha256"]) == 64
    assert rows["2026-10-14"]["status"] == "void"  # its previous session (13 Oct) was never recorded
    assert "previous session" in rows["2026-10-14"]["void_reason"]


@pytest.mark.parametrize("plan", ["old", "fail", "slow"])
def test_a_stale_failed_or_late_index_level_voids_the_session(tmp_path, plan):
    rows, _ = _two_sessions(tmp_path, {"12:00": plan})
    assert rows["2026-10-15"]["status"] == "void" and "12:00" in rows["2026-10-15"]["void_reason"]


def test_a_repeated_level_is_kept_and_flagged_and_does_not_void_the_session(tmp_path):
    rows, recorder = _two_sessions(tmp_path, {"12:00": "repeat"})
    assert rows["2026-10-15"]["status"] == "ok" and rows["2026-10-15"]["basis_counts"] == "quote_last_trade_time:26"
    flagged = [r for r in recorder.ledger.rows(DAY) if r["mark_ist"] == "12:00"][0]
    assert (flagged["status"], flagged["failures"]) == ("good", "index_repeated")


def test_missing_option_quotes_do_not_void_the_realised_variance(tmp_path):
    rows, _ = _two_sessions(tmp_path, {"12:00": "partial"})
    assert rows["2026-10-15"]["status"] == "ok"


def test_the_row_is_written_once_and_other_inputs_are_refused(tmp_path):
    rows, recorder = _two_sessions(tmp_path)
    assert "already written" in recorder.session_rv.compute(DAY)
    first = recorder.session_rv.table.rows()
    path = recorder.files.used(DAY, ist(DAY, 12, 0))
    recorder.files.store.store.folder.joinpath("raw", *path.split("/")).unlink()  # an input disappears (planted)
    with pytest.raises(RvConflict):
        recorder.session_rv.compute(DAY)
    assert recorder.session_rv.table.rows() == first


NOT_COUNTED_1 = "; not counted: 1 before the first session with a recorded previous session (void by construction)"


def test_the_first_recorded_session_is_void_by_construction_and_not_counted(tmp_path):
    """Owner, 16 Oct 2026: 14 Oct (the first) has no recorded previous session, so its overnight part cannot exist;
    the 5% count starts at 15 Oct."""
    _, recorder = _two_sessions(tmp_path)
    assert recorder.session_rv.void_share_line() == "void sessions: 0 of 1 (0.0%)" + NOT_COUNTED_1


def rv_rows(folder, statuses):
    from fno.intraday.rv_table import CUTOFF_FIELDS, FIELDS, RvTable

    table = RvTable(folder)
    for day, status in statuses.items():
        table.write_once({**dict.fromkeys((*FIELDS, *CUTOFF_FIELDS), ""), "session": day, "status": status,
                          "method": "rv-quote-15m-v1", "inputs_sha256": day})  # fmt: skip
    return table


def test_a_later_void_session_counts_and_is_flagged_above_5_percent(tmp_path):
    from fno.intraday.session_rv import SessionRv

    table = rv_rows(tmp_path, {"2026-10-13": "void", "2026-10-14": "ok", "2026-10-15": "void", "2026-10-16": "ok"})
    files = SimpleNamespace(source="groww")  # the void share never reads a snapshot
    line = SessionRv(files, calendar(), table, QuoteSnapshotRv15m()).void_share_line()
    assert line == "void sessions: 1 of 3 (33.3%) - above 5%: propose a new version (design 5.2)" + NOT_COUNTED_1


def test_the_overnight_part_starts_from_the_last_recorded_session_skipping_a_muhurat_day():
    assert previous_recorded_session(calendar(), date(2026, 11, 9)) == date(2026, 11, 6)
    assert previous_recorded_session(calendar(), date(2026, 10, 19)) == date(2026, 10, 17)  # special Saturday
    assert previous_recorded_session(calendar(), date(2026, 10, 21)) == date(2026, 10, 19)  # holiday skipped


def test_the_1530_run_records_v4s_moved_after_cutoff_flag_and_sign_never_a_level(tmp_path):
    """Story G10: the same usable levels as the RV; 14:30 to 15:15 on the fake path is +0.3%, under X (0.61%)."""
    from fno.forecast_v4.cutoff_move import cutoff_flag
    from fno.intraday.wiring import v4_cutoff_flag

    clock = FakeClock(ist(DAY, 9, 10))
    recorder, *_ = build(tmp_path, clock)
    recorder.session_rv.cutoff = v4_cutoff_flag
    recorder.run(time(15, 35))
    row = recorder.session_rv.table.row(DAY)
    assert (row["moved_after_cutoff"], row["cutoff_move_sign"]) == ("no", "+")
    assert cutoff_flag({time(14, 30): level_at(ist(DAY, 14, 30)), time(15, 15): level_at(ist(DAY, 15, 15))},
                       0.002) == ("yes", "+")  # fmt: skip


def test_an_unusable_1515_level_leaves_the_flag_not_computable(tmp_path):
    from fno.intraday.wiring import v4_cutoff_flag

    clock = FakeClock(ist(DAY, 9, 10))
    recorder, *_ = build(tmp_path, clock, {"15:15": "fail"})
    recorder.session_rv.cutoff = v4_cutoff_flag
    recorder.run(time(15, 35))
    row = recorder.session_rv.table.row(DAY)
    assert (row["moved_after_cutoff"], row["cutoff_move_sign"]) == ("", "")


def test_the_count_starts_across_a_muhurat_day_from_the_previous_recorded_session(tmp_path):
    """9 Nov's previous recorded session is 6 Nov: the 8 Nov muhurat evening has no 15:30 mark (judge 270's plant:
    the calendar's plain previous session would never let the count start)."""
    from fno.intraday.session_rv import SessionRv

    table = rv_rows(tmp_path, {"2026-11-06": "void", "2026-11-09": "ok"})
    files = SimpleNamespace(source="groww")
    line = SessionRv(files, calendar(), table, QuoteSnapshotRv15m()).void_share_line()
    assert line == "void sessions: 0 of 1 (0.0%)" + NOT_COUNTED_1
