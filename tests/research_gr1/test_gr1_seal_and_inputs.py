"""GR1 protocol sections 3 and 12 (a): the final period is sealed at load (a planted 2025 record never reaches run 1
and its outcome is never looked up); each global cue is read by A17's rule, so a planted same-day value is refused
(judge 428 SF2); an event counts only when announced before the issue day; run 1 holds no value after its last day."""

import math
from datetime import date

from gr1study.candidates import SINGLE
from gr1study.cues import DECISION_CUTOFF, OPEN_CUTOFF, cue_move, cutoff_for, usdinr_rows
from gr1study.inputs import up_to
from gr1study.rows import implied_rows

from fno.global_cues.other_sources import RbiUsdInrSource
from fno.global_cues.treasury_source import TreasuryTenYearSource
from fno.global_cues.us_index_sources import CboeSp500Source
from tests.research_gr1.gr1_fakes import context, record, rows

Q = (-0.02, -0.01, 0.0, 0.01, 0.02)
DAY = date(2024, 3, 6)  # a Wednesday


def test_a_planted_final_record_is_dropped_before_its_outcome_is_looked_up():
    asked = []

    def close(underlying, day):
        asked.append(day)
        return 101.0

    records = [record("NIFTY", date(2024, 12, 30), Q), record("NIFTY", date(2025, 1, 2), Q)]
    sealed = implied_rows(records, close, final_open=False)
    assert [r.day for r in sealed] == [date(2024, 12, 30)] and date(2025, 1, 3) not in asked
    assert [r.day for r in implied_rows(records, close, final_open=True)] == [date(2024, 12, 30), date(2025, 1, 2)]


def test_a_record_not_ok_or_without_an_outcome_is_dropped():
    records = [record("NIFTY", DAY, Q, status="missing"), record("NIFTY", date(2024, 3, 7), Q)]
    assert implied_rows(records, lambda u, d: None, final_open=False) == []
    kept = implied_rows(records, lambda u, d: 101.0, final_open=False)
    assert len(kept) == 1 and kept[0].outcome == math.log(101.0 / 100.0)


def table(values: dict[date, float]) -> list[dict[str, str]]:
    return [{"value_date": d.isoformat(), "value": str(v), "first_seen_at": "2026-10-15T06:00:00+05:30"}
            for d, v in values.items()]  # fmt: skip


def test_sp500_the_same_us_date_is_not_known_at_15_30_ist():
    rows_ = table({date(2024, 3, 4): 5000.0, date(2024, 3, 5): 5050.0, DAY: 9999.0})  # DAY's close: after 15:30 IST
    assert cue_move(rows_, CboeSp500Source(), DAY, DECISION_CUTOFF) == abs(math.log(5050.0 / 5000.0))


def test_us10y_the_same_date_is_not_known_at_15_30_ist():
    rows_ = table({date(2024, 3, 4): 4.10, date(2024, 3, 5): 4.15, DAY: 9.0})
    assert abs(cue_move(rows_, TreasuryTenYearSource(), DAY, DECISION_CUTOFF) - 0.05) < 1e-9


def test_usdinr_is_read_at_09_15_so_the_days_own_13_30_rate_never_counts():
    rows_ = table({date(2024, 3, 4): 82.9, date(2024, 3, 5): 83.0, DAY: 99.0})
    assert cue_move(rows_, RbiUsdInrSource(), DAY, OPEN_CUTOFF) == abs(math.log(83.0 / 82.9))
    assert cue_move(rows_, RbiUsdInrSource(), DAY, DECISION_CUTOFF) == abs(math.log(99.0 / 83.0))  # why 09:15
    assert cutoff_for("usdinr_rbi", DECISION_CUTOFF) == OPEN_CUTOFF
    assert cutoff_for("sp500", DECISION_CUTOFF) == cutoff_for("us10y", DECISION_CUTOFF) == DECISION_CUTOFF


def test_a_stale_cue_is_refused():
    rows_ = table({date(2024, 2, 1): 5000.0, date(2024, 2, 2): 5050.0})  # a month old on DAY
    assert cue_move(rows_, CboeSp500Source(), DAY, DECISION_CUTOFF) is None


def test_an_event_counts_only_when_announced_before_the_issue_day():
    (row,) = rows(DAY, DAY)  # target the next day
    known = context(events={row.target_day: date(2024, 1, 10)})
    late = context(events={row.target_day: DAY})  # announced on the issue day itself: not known at the issue
    assert SINGLE["C5"].features(row, known) == [1.0, 1.0] and SINGLE["C5"].features(row, late) == [1.0, 0.0]


def test_run_1_holds_no_value_after_its_last_day():
    values = {date(2024, 12, 31): 1.0, date(2025, 1, 1): 2.0}
    assert up_to(values, date(2024, 12, 31)) == {date(2024, 12, 31): 1.0}


def test_the_horizon_is_after_the_issue_day_up_to_and_with_the_target():
    (row,) = rows(DAY, DAY)
    on_issue_day = context(events={DAY: date(2024, 1, 10)}, expiries={"NIFTY": {DAY: frozenset({DAY})}})
    on_target = context(events={row.target_day: date(2024, 1, 10)},
                        expiries={"NIFTY": {DAY: frozenset({row.target_day})}})  # fmt: skip
    assert SINGLE["C5"].features(row, on_issue_day) == [1.0, 0.0] and SINGLE["C6"].features(row, on_issue_day) == [
        1.0,
        0.0,
    ]
    assert SINGLE["C5"].features(row, on_target) == [1.0, 1.0] and SINGLE["C6"].features(row, on_target) == [1.0, 1.0]


def test_usdinr_takes_rbis_rate_and_fbils_only_for_rbis_missing_dates():
    rbi = table({date(2018, 7, 9): 68.5, date(2022, 4, 12): 76.0})
    fbil = table({date(2018, 7, 10): 68.6, date(2022, 4, 12): 99.0, date(2020, 5, 4): 75.6})
    merged = usdinr_rows(rbi, fbil)
    expected = [("2018-07-09", "68.5"), ("2018-07-10", "68.6"), ("2020-05-04", "75.6"), ("2022-04-12", "76.0")]
    assert [(r["value_date"], r["value"]) for r in merged] == expected


def test_c6_reads_only_the_issue_days_own_file_never_a_later_revision():
    (row,) = rows(DAY, DAY)
    revised = {"NIFTY": {DAY: frozenset({date(2024, 3, 14)}), date(2024, 3, 7): frozenset({row.target_day})}}
    assert SINGLE["C6"].features(row, context(expiries=revised)) == [1.0, 0.0]  # the 7 Mar file's new date never counts
    assert SINGLE["C6"].features(row, context(expiries={"NIFTY": {}})) is None  # no file of the day: dropped
