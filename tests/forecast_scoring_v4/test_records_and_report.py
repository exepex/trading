"""Story G8 criteria 8-9: EXPLORATORY before the freeze, a look recorded once, look 2's closed set from look 1, and
"not enough data yet" instead of a failure (V4 and V5 too since story G7b completion, part e)."""

import json
from datetime import date

import pytest

from fno.constants import (
    V1_RV_1S,
    V2_RV_5S,
    V4_CLAIM,
    V4_COHORT_CLOSE_PROXY,
    V4_COHORT_LIVE,
    V4_OPEN,
    V5_INSIDE_STRADDLE,
    V6_BIG_MOVE_5S,
)
from fno.forecast_scoring.v4.days import DayCounts
from fno.forecast_scoring.v4.inputs import ForecastValue, Outcome, V4ForecastSource, V4OutcomeSource
from fno.forecast_scoring.v4.records import EXPLORATORY, LookRecordExists, LookRecords, NoRegistrations, Registration
from fno.forecast_scoring.v4.render import report_json, report_lines
from fno.forecast_scoring.v4.scoring import QUESTIONS, STATUS_NO_DATA, V4Scoring
from fno.forecast_v4.terms import LOOK_SETTLE_DATE, LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.helpers import settled_slot_days, values

NO_DAYS = DayCounts(0, 0, 0, 0)


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
    assert status[V5_INSIDE_STRADDLE] == STATUS_NO_DATA and status[V1_RV_1S] == STATUS_NO_DATA
    assert status[f"{V2_RV_5S}/intraday"] == STATUS_NO_DATA  # part f's series, no rows here
    lines = report_lines(reports, frozen=False, as_of="2025-01-06", days=NO_DAYS)
    assert lines[0] == EXPLORATORY and f"{V1_RV_1S}: {STATUS_NO_DATA}" in lines
    v6b = next(r for r in reports if r.question == V6_BIG_MOVE_5S)
    live, proxy = v6b.cohorts[V4_COHORT_LIVE], v6b.cohorts[V4_COHORT_CLOSE_PROXY]
    assert v6b.live_forecasts == 2 and [c.forecaster for c in live.comparisons] == ["weather_m1"]
    assert live.scores["weather_m1"].n == 1 and live.comparisons[0].pairing.unresolved == 1
    assert live.comparisons[0].pairing.missing_baseline == 1  # resolved 2 Jan: the back-fill base rate is never pooled
    assert list(proxy.scores) == ["base_rate"] and proxy.comparisons == []
    assert report_json(reports, frozen=False, as_of="2025-01-06", days=NO_DAYS)["exploratory"] is True
    assert report_lines(reports, frozen=True, as_of="2025-01-06", days=NO_DAYS)[0] != EXPLORATORY


def test_a_look_before_the_freeze_prints_exploratory_and_writes_nothing_and_after_it_records_once(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone

    from fno.forecast_scoring.v4.cli import _look
    from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds

    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    at = datetime(2027, 5, 31, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    assert _look(scoring, records, FrozenToolThresholds(tmp_path), settled_slot_days(), LOOK_STOP_REVIEW, at) == 0
    assert capsys.readouterr().out.startswith(EXPLORATORY) and not records.path(LOOK_STOP_REVIEW).exists()
    (tmp_path / "FREEZE_v4.md").write_text("# Freeze\nFrozen on: 2024-12-31\n")
    _look(scoring, records, FrozenToolThresholds(tmp_path), settled_slot_days(), LOOK_STOP_REVIEW, at)
    recorded = json.loads(records.path(LOOK_STOP_REVIEW).read_text())
    assert recorded["test_a"] == "undecided" and len(recorded["members"]) == 15
    with pytest.raises(LookRecordExists):
        _look(scoring, records, FrozenToolThresholds(tmp_path), settled_slot_days(), LOOK_STOP_REVIEW, at)


def test_the_freeze_day_is_read_from_its_record_and_a_record_without_it_is_refused(tmp_path):
    from fno.forecast_scoring.v4.records import FreezeDateMissing

    records = LookRecords(tmp_path, tmp_path / "FREEZE_v4.md")
    (tmp_path / "FREEZE_v4.md").write_text("# Freeze v4\nFrozen on: 2027-01-04\n")
    assert records.frozen_on() == date(2027, 1, 4)
    (tmp_path / "FREEZE_v4.md").write_text("# Freeze v4\n")
    with pytest.raises(FreezeDateMissing):
        records.frozen_on()


class Mixed(V4ForecastSource):
    """Back-fill to 3 Jan, live from 2 Jan (a pre-freeze manual check on 2 Jan), freeze on 2 Jan."""

    def forecasters(self, question):
        return ["base_rate", "weather_m1"]

    def values(self, question, forecaster):
        rows = {date(2025, 1, d): (0.2, d >= 2) for d in range(1, 7)}
        rows[date(2025, 1, 3)] = (0.2, False)  # a back-fill row after the freeze day still never counts
        return {d: ForecastValue(v, live) for d, (v, live) in rows.items()}


class Registered(NoRegistrations):
    def registered(self):
        return {(V6_BIG_MOVE_5S, "rules"): Registration("weather_m1", date(2025, 1, 1))}


class AllResolved(V4OutcomeSource):
    def outcomes(self, question):
        return {date(2025, 1, d): Outcome(d % 2 == 0, False, 14.0, 0.0) for d in range(1, 7)}


def test_after_the_freeze_a_look_counts_only_live_rows_of_later_days():
    scoring = V4Scoring(Mixed(), AllResolved(), Registered())
    member = scoring.member_comparisons(counted_after=date(2025, 1, 2))[(V6_BIG_MOVE_5S, "rules")]
    assert member.pairing.scored.days == (date(2025, 1, 4), date(2025, 1, 5), date(2025, 1, 6))
    everything = scoring.member_comparisons(counted_after=None)[(V6_BIG_MOVE_5S, "rules")]
    assert len(everything.pairing.scored.days) == 6
