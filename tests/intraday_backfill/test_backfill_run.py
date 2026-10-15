"""Story A16b, criteria 1, 3, 5 and 6 (runs): raw first, calendar order, transient failures defer, permanent absences
write void rows, a failed window resumes cleanly, three Groww failures stop the run. Fake Groww, Drive and NSE."""

from datetime import date

import pytest

from fno.intraday import backfill as backfill_module
from fno.intraday.backfill_report import report_lines
from fno.intraday.candle_source import ONE_MINUTE
from tests.intraday_backfill.fakes import (
    START,
    FakeGroww,
    FakeNse,
    build,
    fifteen_minute_rows,
    levels,
    minute_rows,
    session_data,
)

WEEK = [date(2026, 9, 28), date(2026, 9, 29), date(2026, 9, 30), date(2026, 10, 1)]  # 2 Oct is a holiday
AFTER = date(2026, 10, 5)


def run(tmp_path, days, end, failing=None, store=None, overrides=None):
    fifteen, minutes, nse = session_data(days, overrides)
    groww = FakeGroww(fifteen, minutes, failing)
    backfill = build(tmp_path, groww, FakeNse(nse), store)
    return backfill, backfill.run(START, end), groww


def statuses(backfill, days):
    rows = [backfill.table.row(d) for d in days]
    return [(r["status"], r["void_reason"]) if r else None for r in rows]


def test_a_normal_run_writes_every_session_back_filled_after_archiving_its_copies(tmp_path):
    backfill, report, _ = run(tmp_path, [*WEEK, AFTER], AFTER)
    assert report.complete and len(report.written) == 5 and report.held == 0
    assert statuses(backfill, WEEK)[0] == ("void", "no_previous_close")  # the series' first session
    assert statuses(backfill, [*WEEK[1:], AFTER]) == [("ok", "")] * 4
    rows = backfill.table.rows()
    assert {r["provenance"] for r in rows} == {"backfilled"} and {r["measure"] for r in rows} == {"candle_close"}
    manifest = backfill.archive.rows()
    assert {r["path"] for r in manifest} >= {r["copy_15m"] for r in rows} | {r["copy_1m"] for r in rows}
    assert report.windows == ["window 2026-09-28..2026-10-05: 125 of 125 session candles (5 sessions)"]


def test_the_calendar_decides_holiday_special_and_muhurat(tmp_path):
    special, muhurat, holiday = date(2026, 10, 10), date(2026, 10, 21), date(2026, 10, 2)
    days = [*WEEK, holiday, AFTER, date(2026, 10, 9), special, date(2026, 10, 20), muhurat]
    backfill, report, _ = run(tmp_path, days, date(2026, 10, 21))
    assert backfill.table.row(special)["status"] == "ok"
    assert backfill.table.row(muhurat) is None and backfill.table.row(holiday) is None
    assert muhurat not in report.sessions and date(2026, 10, 11) not in report.sessions


def test_a_session_without_candles_is_a_void_row_and_the_next_has_a_void_overnight_part(tmp_path):
    backfill, report, groww = run(tmp_path, [*WEEK, AFTER], AFTER, overrides={("15m", WEEK[2]): []})
    assert statuses(backfill, [WEEK[2]]) == [("void", "missing_candles:25")]
    assert (ONE_MINUTE, WEEK[2], WEEK[2]) not in groww.calls  # no 1-minute check for an incomplete session
    after = backfill.table.row(WEEK[3])
    assert after["void_reason"] == "no_previous_close" and after["rv_intraday"] and not after["rv_overnight"]
    assert report.complete


def test_a_missing_middle_candle_keeps_the_15_30_level_for_the_next_session(tmp_path):
    rows = fifteen_minute_rows(WEEK[1], levels(WEEK[1]), drop=(7,))
    backfill, _, _ = run(tmp_path, WEEK, WEEK[3], overrides={("15m", WEEK[1]): rows})
    assert backfill.table.row(WEEK[1])["void_reason"] == "missing_candles:1"
    assert backfill.table.row(WEEK[2])["status"] == "ok"  # its overnight part starts from the trusted 15:30 level


# Transient or permanent (judge 122 addendum 2): four cases.


def test_a_groww_error_on_the_1_minute_call_defers_and_the_next_run_writes_it(tmp_path):
    backfill, report, _ = run(tmp_path, WEEK, WEEK[3], failing={("minutes", WEEK[1])})
    assert backfill.table.row(WEEK[1]) is None and "GrowwAPIException" in report.deferred[WEEK[1]]
    assert report.deferred[WEEK[2]] == f"previous session {WEEK[1]} has no row" and not report.complete
    again = build(tmp_path, FakeGroww(*session_data(WEEK)[:2]), FakeNse(session_data(WEEK)[2])).run(START, WEEK[3])
    assert again.complete and set(again.written) == {WEEK[1], WEEK[2], WEEK[3]} and again.held == 1


def test_a_received_1_minute_answer_missing_a_minute_is_a_void_row(tmp_path):
    values = levels(WEEK[1])
    short = minute_rows(WEEK[1], values, values[0] - 3.0, skip=("11:44",))
    backfill, report, _ = run(tmp_path, WEEK, WEEK[3], overrides={("1m", WEEK[1]): short})
    assert statuses(backfill, [WEEK[1]]) == [("void", "no_1m_check:1")] and report.complete
    assert backfill.table.row(WEEK[2])["void_reason"] == "no_previous_close"  # its levels are untrusted


def test_a_failed_nse_read_defers(tmp_path):
    backfill, report, _ = run(tmp_path, WEEK, WEEK[3], overrides={("nse", WEEK[1]): OSError("drive")})
    assert backfill.table.row(WEEK[1]) is None and report.deferred[WEEK[1]] == f"NSE index-close {WEEK[1]}: OSError"


def test_nse_s_definitive_absence_is_a_void_row(tmp_path):
    backfill, report, _ = run(tmp_path, WEEK, WEEK[3], overrides={("nse", WEEK[1]): None})
    row = backfill.table.row(WEEK[1])
    assert (row["status"], row["void_reason"], row["nse_check"]) == ("void", "nse_unchecked", "unchecked")
    assert backfill.table.row(WEEK[2])["void_reason"] == "no_previous_close" and report.complete


def test_a_failed_middle_window_defers_then_resumes_without_a_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(backfill_module, "WINDOW_DAYS", 2)
    days = [*WEEK, AFTER]
    backfill, report, _ = run(tmp_path, days, AFTER, failing={("window", WEEK[2])})
    assert backfill.table.row(WEEK[1]) is not None and backfill.table.row(WEEK[2]) is None
    assert report.deferred[AFTER] == f"previous session {WEEK[3]} has no row"
    resumed = build(tmp_path, FakeGroww(*session_data(days)[:2]), FakeNse(session_data(days)[2])).run(START, AFTER)
    assert resumed.complete and backfill.table.row(AFTER)["rv_overnight"]  # computed, never a fixed wrong void


def test_three_groww_failures_in_a_row_stop_the_run(tmp_path, monkeypatch):
    monkeypatch.setattr(backfill_module, "WINDOW_DAYS", 1)
    failing = {("window", d) for d in WEEK}
    _, report, groww = run(tmp_path, [*WEEK, AFTER], AFTER, failing=failing)
    assert report.stopped.startswith("3 Groww failures in a row") and len(groww.calls) == 3
    assert report.deferred[AFTER] == "not reached: the run stopped"


def test_a_drive_save_failure_defers_without_counting_as_a_groww_failure(tmp_path):
    class Refusing:
        def put(self, path, data):
            raise OSError("drive down")

        def get(self, path):
            return None

    backfill, report, _ = run(tmp_path, WEEK, WEEK[3], store=Refusing())
    assert report.deferred[WEEK[0]] == "window 2026-09-28..2026-10-01: OSError" and not backfill.archive.rows()
    assert not report.stopped and backfill.table.rows() == []


def test_each_window_line_shows_a_shortfall_and_deferrals_count_runs_in_a_row(tmp_path):
    rows = fifteen_minute_rows(WEEK[1], levels(WEEK[1]), drop=(3, 4))
    backfill, report, _ = run(
        tmp_path, WEEK, WEEK[3], failing={("minutes", WEEK[2])}, overrides={("15m", WEEK[1]): rows}
    )
    assert report.windows == ["window 2026-09-28..2026-10-01: 98 of 100 session candles (4 sessions)"]
    second = build(tmp_path, FakeGroww(*session_data(WEEK)[:2], failing={("minutes", WEEK[2])}),
                   FakeNse(session_data(WEEK)[2])).run(START, WEEK[3])  # fmt: skip
    lines = report_lines(second, backfill.table.rows(), backfill.deferrals.counts())
    assert f"DEFERRED {WEEK[2]}: Groww 1m {WEEK[2]}..{WEEK[2]}: GrowwAPIException (2 run(s) in a row)" in lines


def test_a_rerun_writes_nothing_new_and_fetches_nothing(tmp_path):
    backfill, _, _ = run(tmp_path, WEEK, WEEK[3])
    groww = FakeGroww(*session_data(WEEK)[:2])
    again = build(tmp_path, groww, FakeNse(session_data(WEEK)[2])).run(START, WEEK[3])
    assert again.complete and again.held == 4 and not again.written and groww.calls == []


@pytest.mark.parametrize("start", [date(2026, 9, 29), date(2026, 10, 1)])
def test_a_range_starting_after_the_series_start_waits_for_its_earlier_sessions(tmp_path, start):
    fifteen, minutes, nse = session_data(WEEK)
    report = build(tmp_path, FakeGroww(fifteen, minutes), FakeNse(nse)).run(start, WEEK[3])
    assert not report.written and report.deferred[start].startswith("previous session")
