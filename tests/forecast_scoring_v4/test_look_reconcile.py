"""ChatGPT review 127 / response 213, agreed with G11: before a confirmatory look every scheduled AI slot-day has a v4
record row (ok or a definitive miss); a day without one (a sealed answer never collected) refuses the look."""

from datetime import date, datetime, timedelta, timezone

import pytest

from fno.constants import V4_SLOT_AI, V4_SLOT_RULES, V6_BIG_MOVE_1S
from fno.forecast_scoring.v4.audits import LookBlocked, OpenAuditFile
from fno.forecast_scoring.v4.cli import _look
from fno.forecast_scoring.v4.inputs import ForecastValue, V4ForecastSource
from fno.forecast_scoring.v4.reconcile import AiSlotDays, SlotDay, require_reconciled
from fno.forecast_scoring.v4.records import LookRecords, NoRegistrations, Registration
from fno.forecast_scoring.v4.scoring import V4Scoring
from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds
from fno.forecast_v4.terms import LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.test_records_and_report import OneForecaster, Outcomes

FREEZE = date(2027, 5, 21)
DAYS = [date(2027, 5, d) for d in (24, 25, 26, 27, 28)]  # Monday to Friday after the freeze
SEALED_NOT_COLLECTED = DAYS[2]
AT = datetime(2027, 5, 28, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))


class Records(V4ForecastSource):
    """book3_ai_v2: ok rows, a definitive not_fired on 27 May, nothing on 26 May; weather_vix_v1 (rules) has gaps."""

    def __init__(self, rows):
        self.rows = rows

    def forecasters(self, question):
        return list(self.rows)

    def values(self, question, forecaster):
        return self.rows.get(forecaster, {})


def records(ai_days, rules_days=()):
    ai = {d: ForecastValue(None if d == DAYS[3] else 0.1, True) for d in ai_days}  # 27 May: not_fired, no value
    return Records({"book3_ai_v2": ai, "weather_vix_v1": {d: ForecastValue(0.1, True) for d in rules_days}})


class Registered(NoRegistrations):
    def __init__(self, ai_start=DAYS[0]):
        self.ai_start = ai_start

    def registered(self):
        return {(V6_BIG_MOVE_1S, V4_SLOT_AI): Registration("book3_ai_v2", self.ai_start),
                (V6_BIG_MOVE_1S, V4_SLOT_RULES): Registration("weather_vix_v1", DAYS[0])}  # fmt: skip


def sessions(first, last):
    return [d for d in DAYS if first <= d <= last]


def slot_days(rows, registry=None):
    return AiSlotDays(rows, registry or Registered(), sessions)


def test_a_sealed_answer_never_collected_refuses_the_look_and_a_written_miss_settles_its_day():
    rows = records([d for d in DAYS if d != SEALED_NOT_COLLECTED], rules_days=DAYS[:1])  # the rules' gaps: ordinary
    unsettled = slot_days(rows).unsettled(FREEZE, AT.date())
    assert unsettled == [SlotDay(SEALED_NOT_COLLECTED, V6_BIG_MOVE_1S, V4_SLOT_AI)]  # 27 May's not_fired row settles it
    with pytest.raises(LookBlocked, match="1 without a record row, the earliest 2027-05-26"):
        require_reconciled(unsettled, AT.date())


def test_only_days_from_the_counted_start_to_the_look_are_checked():
    rows = records(DAYS[3:])
    assert slot_days(rows, Registered(ai_start=DAYS[3])).unsettled(FREEZE, AT.date()) == []  # starts 27 May
    assert slot_days(rows).unsettled(DAYS[2], AT.date()) == []  # frozen on 26 May: only 27-28 May count
    assert len(slot_days(rows).unsettled(FREEZE, DAYS[1])) == 2  # a look on 25 May needs 24-25 May only


def test_an_unsettled_slot_day_stops_a_recorded_look_and_records_nothing(tmp_path, capsys):
    look_records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    (tmp_path / "FREEZE_v4.md").write_text(f"# Freeze\nFrozen on: {FREEZE}\n")
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    rows = records([d for d in DAYS if d != SEALED_NOT_COLLECTED])
    gates = (OpenAuditFile(tmp_path / "none.csv", lambda: False), slot_days(rows))
    assert _look(scoring, look_records, FrozenToolThresholds(tmp_path), gates, LOOK_STOP_REVIEW, AT) == 1
    assert "2027-05-26 (v6_abs_move_2pct_next_session, ai_team)" in capsys.readouterr().out
    assert not look_records.path(LOOK_STOP_REVIEW).exists()


def test_the_live_wiring_has_no_registered_ai_slot_yet_and_skips_weekends():
    from fno.forecast_scoring.v4.wiring import _sessions_not_late, build_ai_slot_days

    assert build_ai_slot_days().unsettled(date(2026, 10, 1), date(2026, 10, 16)) == []
    assert _sessions_not_late(date(2026, 10, 9), date(2026, 10, 13)) == [date(2026, 10, 9), date(2026, 10, 12),
                                                                          date(2026, 10, 13)]  # fmt: skip
