"""Story G9 on the real path (judge 149 S1, S2, M2): a day neither file holds is an input failure; the 2% day is the
regime's own `>=`; the miss counts reach the report text, the report JSON and the recorded look."""

import json
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone

from fno.constants import V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.comparison import compare, paired_rows, seed_word
from fno.forecast_scoring.v4.inputs import Outcome, V4ForecastSource, V4OutcomeSource
from fno.forecast_scoring.v4.records import LookRecords, NoRegistrations
from fno.forecast_scoring.v4.render import report_json, report_lines
from fno.forecast_scoring.v4.scoring import QUESTIONS, V4Scoring
from fno.forecast_v4.misses import MissReport
from fno.forecast_v4.regime import is_big_move
from fno.forecast_v4.terms import LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.helpers import values

DAYS = [date(2025, 1, d) for d in range(1, 11)]
ABSENT, MISSED = DAYS[4], DAYS[6]  # day 5: neither file has a row; day 7: the forecaster has none
RETURNS = {DAYS[2]: 0.0199, MISSED: 0.02, DAYS[7]: -0.02}  # exactly 2% either way is a 2% day; 1.99% is not
OUTCOMES = {d: Outcome(i % 2 == 0, False, 15.0, RETURNS.get(d, 0.001)) for i, d in enumerate(DAYS)}
OWN = values({d: 0.3 for d in DAYS if d not in (ABSENT, MISSED)}, live=True)
BASE = values({d: 0.2 for d in DAYS if d != ABSENT}, live=True)
EXPECTED = MissReport(observable=9, missed=1, big_observable=2, big_missed=1, input_failures=1)


def test_a_day_neither_file_holds_is_an_input_failure_and_exactly_2_percent_is_a_2_percent_day():
    rows = paired_rows(OWN, BASE, OUTCOMES)
    assert ABSENT not in {r.day for r in rows}  # pairing never sees the day
    found = compare(V6_BIG_MOVE_5S, "weather_m1", "base_rate", rows, OUTCOMES, seed_word(V6_BIG_MOVE_5S, None, "x"))
    assert found.misses == EXPECTED and found.misses.operations_undecided
    assert found.pairing.missing_forecast == 1 and len(found.pairing.scored.days) == 8


def test_the_2_percent_predicate_is_inclusive_on_both_sides():
    assert is_big_move(0.02) and is_big_move(-0.02) and not is_big_move(0.0199) and not is_big_move(-0.0199)


class Files(V4ForecastSource):
    def forecasters(self, question):
        return ["base_rate", "weather_m1"] if question == V6_BIG_MOVE_5S else []

    def values(self, question, forecaster):
        return BASE if forecaster == "base_rate" else OWN


class Outcomes(V4OutcomeSource):
    def outcomes(self, question):
        return OUTCOMES


class Registered(NoRegistrations):
    def registered(self):
        return {(V6_BIG_MOVE_5S, "rules"): "weather_m1"}


def _scoring():
    return V4Scoring(Files(), Outcomes(), Registered())


def test_the_report_text_and_json_carry_the_miss_counts():
    reports = [_scoring().question_report(q) for q in QUESTIONS]
    assert f"    {EXPECTED.line()}" in report_lines(reports, frozen=False, as_of="2025-01-20")
    v6b = next(q for q in report_json(reports, frozen=False, as_of="2025-01-20")["questions"]
               if q["question"] == V6_BIG_MOVE_5S)  # fmt: skip
    assert v6b["comparisons"][0]["misses"] == asdict(EXPECTED)


def test_the_recorded_look_carries_each_members_miss_line(tmp_path, capsys):
    from fno.forecast_scoring.v4.cli import _look
    from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds

    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    (tmp_path / "FREEZE_v4.md").write_text("# Freeze\nFrozen on: 2024-12-31\n")
    at = datetime(2027, 5, 31, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    _look(_scoring(), records, FrozenToolThresholds(tmp_path), LOOK_STOP_REVIEW, at)
    recorded = json.loads(records.path(LOOK_STOP_REVIEW).read_text())
    assert [V6_BIG_MOVE_5S, "rules", EXPECTED.line()] in recorded["misses"]
    assert recorded["test_a"] == "undecided"
