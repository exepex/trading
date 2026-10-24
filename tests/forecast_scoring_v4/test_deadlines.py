"""Story G10 completion, criterion 8: G8 applies the 15:10 verdicts. A late live row is no forecast that day (a miss);
an on-time one is kept; a live row without a verdict is counted "deadline not checked" and a recorded look refuses
while one exists up to its date; back-fill rows and the AI books are never checked here."""

from datetime import date

import pytest

from fno.constants import BOOK3_AI
from fno.forecast_scoring.v4.days import DayCounts
from fno.forecast_scoring.v4.deadlines import (
    DeadlineVerdicts,
    LateCommitmentsOut,
    require_checked,
    unchecked_days,
)
from fno.forecast_scoring.v4.inputs import ForecastValue, V4ForecastSource
from fno.forecast_scoring.v4.reconcile import LookBlocked
from fno.v4_pack.deadline import Verdict, verdict_bytes

THU, FRI, MON = date(2026, 10, 22), date(2026, 10, 23), date(2026, 10, 26)
BACKFILL = date(2026, 10, 21)


class Rows(V4ForecastSource):
    def forecasters(self, question):
        return ["base_rate", BOOK3_AI]

    def values(self, question, forecaster):
        return {BACKFILL: ForecastValue(0.1, False), THU: ForecastValue(0.2, True), FRI: ForecastValue(0.3, True),
                MON: ForecastValue(0.4, True)}  # fmt: skip


class Files:
    def __init__(self, by_day):
        self.by_day = by_day

    def files(self):
        from datetime import datetime

        from fno.models import IST

        at = datetime(2026, 10, 22, 14, 12, tzinfo=IST)
        return {f"data/v4/deadlines/{d}.json": verdict_bytes(d, [Verdict("base_rate", "q", at, v)])
                for d, v in self.by_day.items()}  # fmt: skip


def checked(by_day):
    return LateCommitmentsOut(Rows(), DeadlineVerdicts(Files(by_day)))


def test_a_late_row_is_a_miss_an_on_time_row_stays_and_a_day_without_a_verdict_is_unchecked():
    source = checked({THU: "late", FRI: "on_time"})
    values = source.values("q", "base_rate")
    assert values[THU] == ForecastValue(None, True)  # a live row with no value: a miss under G9's caps
    assert values[FRI] == ForecastValue(0.3, True) and values[BACKFILL] == ForecastValue(0.1, False)
    assert source.unchecked == {MON}


def test_the_ai_books_and_back_fill_rows_are_never_checked():
    source = checked({})
    assert source.values("q", BOOK3_AI) == Rows().values("q", BOOK3_AI) and source.unchecked == set()
    source.values("q", "base_rate")
    assert source.unchecked == {THU, FRI, MON}  # never the back-fill day


def test_a_day_without_a_verdict_file_is_unchecked():
    source = LateCommitmentsOut(Rows(), DeadlineVerdicts(Files({THU: "on_time", FRI: "on_time", MON: "on_time"})))
    assert source.values("q", "base_rate")[THU].value == 0.2 and source.unchecked == set()
    assert unchecked_days(LateCommitmentsOut(Rows(), DeadlineVerdicts(Files({THU: "on_time"}))), ("q",)) == [FRI, MON]


def test_a_look_refuses_while_a_counted_day_up_to_it_is_unchecked():
    with pytest.raises(LookBlocked, match="1 day\\(s\\) not checked, the earliest 2026-10-23"):
        require_checked([FRI, MON], THU, FRI)
    require_checked([MON], THU, FRI)  # a later day does not block an earlier look
    require_checked([THU], THU, MON)  # a day up to the freeze is never counted (review finding 2)
    require_checked([], THU, MON)


def test_a_row_its_day_s_verdict_file_does_not_name_was_committed_after_the_check_and_is_late():
    """Review finding 1: a row pushed at 16:00, after 15:12's check wrote the day's file, is a miss, never scored, and
    never leaves the day unchecked for good."""
    source = LateCommitmentsOut(Rows(), DeadlineVerdicts(Files({THU: "on_time", FRI: "on_time", MON: "on_time"})))
    assert source.values("q", "other_rule")[THU] == ForecastValue(None, True) and source.unchecked == set()


def test_the_counts_line_names_the_unchecked_days():
    assert "deadline not checked 2" in DayCounts(1, 0, 0, 0, 0, 2).line()


def test_a_recorded_look_with_an_unchecked_day_records_nothing(tmp_path, capsys):
    from fno.forecast_scoring.v4.cli import _look
    from fno.forecast_scoring.v4.records import LookRecords, NoRegistrations
    from fno.forecast_scoring.v4.scoring import V4Scoring
    from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds
    from fno.forecast_v4.terms import LOOK_STOP_REVIEW
    from tests.forecast_scoring_v4.helpers import intact
    from tests.forecast_scoring_v4.test_look_reconcile import AT, DAYS, FREEZE, records, slot_days
    from tests.forecast_scoring_v4.test_records_and_report import OneForecaster, Outcomes

    look_records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    (tmp_path / "FREEZE_v4.md").write_text(f"# Freeze\nFrozen on: {FREEZE}\n")
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    code = _look(scoring, look_records, FrozenToolThresholds(tmp_path), slot_days(records(DAYS)), LOOK_STOP_REVIEW,
                 AT, lambda: [FREEZE, DAYS[1]], freeze=intact)  # the freeze day itself is not counted  # fmt: skip
    assert code == 1 and not look_records.path(LOOK_STOP_REVIEW).exists()
    assert "deadline checked: 1 day(s) not checked, the earliest 2027-05-25" in capsys.readouterr().out
