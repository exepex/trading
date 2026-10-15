"""Story G8 criteria 8-9: EXPLORATORY before the freeze, a look recorded once, look 2's closed set from look 1, and
"not started" / "not enough data yet" instead of a failure."""

import json
from datetime import date

import pytest

from fno.constants import V1_RV_1S, V4_CLAIM, V4_OPEN, V5_INSIDE_STRADDLE, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.inputs import Outcome, V4ForecastSource, V4OutcomeSource
from fno.forecast_scoring.v4.records import EXPLORATORY, LookRecordExists, LookRecords, NoRegistrations
from fno.forecast_scoring.v4.render import report_json, report_lines
from fno.forecast_scoring.v4.scoring import QUESTIONS, STATUS_NO_DATA, STATUS_NOT_STARTED, V4Scoring
from fno.forecast_v4.terms import LOOK_SETTLE_DATE, LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.helpers import values


def test_a_look_is_recorded_once_and_look_2_reads_the_members_closed_at_look_1(tmp_path):
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    assert not records.frozen() and records.closed(LOOK_SETTLE_DATE) == set()
    members = [{"question": V6_BIG_MOVE_5S, "slot": "rules", "verdict": V4_CLAIM, "futile": False},
               {"question": V1_RV_1S, "slot": "rules", "verdict": V4_OPEN, "futile": True},
               {"question": V1_RV_1S, "slot": "hybrid", "verdict": V4_OPEN, "futile": False}]  # fmt: skip
    records.write(LOOK_STOP_REVIEW, {"members": members})
    with pytest.raises(LookRecordExists):
        records.write(LOOK_STOP_REVIEW, {"members": []})
    assert json.loads(records.path(LOOK_STOP_REVIEW).read_text())["members"] == members
    assert records.closed(LOOK_SETTLE_DATE) == {(V6_BIG_MOVE_5S, "rules"), (V1_RV_1S, "rules")}
    assert records.closed(LOOK_STOP_REVIEW) == set()
    (tmp_path / "FREEZE_v4.md").write_text("frozen\n")
    assert records.frozen()


class OneForecaster(V4ForecastSource):
    def forecasters(self, question):
        return ["base_rate", "weather_m1"] if question == V6_BIG_MOVE_5S else []

    def values(self, question, forecaster):
        value = 0.14 if forecaster == "base_rate" else 0.2
        return values({date(2025, 1, 2): value, date(2025, 1, 3): value}, live=forecaster == "weather_m1")


class Outcomes(V4OutcomeSource):
    def outcomes(self, question):
        return {date(2025, 1, 2): Outcome(True, False, 14.0, 0.021)}  # 3 Jan unresolved


def test_the_report_is_exploratory_before_the_freeze_and_never_fails_on_empty_questions():
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    reports = [scoring.question_report(q) for q in QUESTIONS]
    status = {r.question: r.status for r in reports}
    assert status[V5_INSIDE_STRADDLE] == STATUS_NOT_STARTED and status[V1_RV_1S] == STATUS_NO_DATA
    lines = report_lines(reports, frozen=False, as_of="2025-01-06")
    assert lines[0] == EXPLORATORY and f"{V1_RV_1S}: {STATUS_NO_DATA}" in lines
    v6b = next(r for r in reports if r.question == V6_BIG_MOVE_5S)
    assert v6b.live_forecasts == 2 and [c.forecaster for c in v6b.comparisons] == ["weather_m1"]
    assert v6b.scores["weather_m1"].n == 1 and v6b.comparisons[0].pairing.unresolved == 1
    assert report_json(reports, frozen=False, as_of="2025-01-06")["exploratory"] is True
    assert report_lines(reports, frozen=True, as_of="2025-01-06")[0] != EXPLORATORY


def test_a_look_before_the_freeze_prints_exploratory_and_writes_nothing_and_after_it_records_once(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone

    from fno.forecast_scoring.v4.cli import _look
    from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds

    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    at = datetime(2027, 5, 31, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    assert _look(scoring, records, FrozenToolThresholds(tmp_path), LOOK_STOP_REVIEW, at) == 0
    assert capsys.readouterr().out.startswith(EXPLORATORY) and not records.path(LOOK_STOP_REVIEW).exists()
    (tmp_path / "FREEZE_v4.md").write_text("frozen\n")
    _look(scoring, records, FrozenToolThresholds(tmp_path), LOOK_STOP_REVIEW, at)
    recorded = json.loads(records.path(LOOK_STOP_REVIEW).read_text())
    assert recorded["test_a"] == "undecided" and len(recorded["members"]) == 15
    with pytest.raises(LookRecordExists):
        _look(scoring, records, FrozenToolThresholds(tmp_path), LOOK_STOP_REVIEW, at)
