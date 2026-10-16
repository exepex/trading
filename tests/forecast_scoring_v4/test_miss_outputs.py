"""Story G9 on the real path (judge 149 S1, S2, M2): a day neither file holds is an input failure; the 2% day is the
regime's own `>=`; the miss counts reach the report text, the report JSON and the recorded look."""

import json
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone

from fno.constants import V4_SLOT_AI, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.comparison import compare, paired_rows, seed_word
from fno.forecast_scoring.v4.days import DayCounts
from fno.forecast_scoring.v4.inputs import Outcome, V4ForecastSource, V4OutcomeSource
from fno.forecast_scoring.v4.records import LookRecords, NoRegistrations, Registration
from fno.forecast_scoring.v4.render import report_json, report_lines
from fno.forecast_scoring.v4.scoring import QUESTIONS, V4Scoring
from fno.forecast_v4.misses import MissReport
from fno.forecast_v4.regime import is_big_move
from fno.forecast_v4.terms import LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.helpers import settled_slot_days, values

DAYS = [date(2025, 1, d) for d in range(1, 11)]
ABSENT, MISSED = DAYS[4], DAYS[6]  # day 5: neither file has a row; day 7: the forecaster has none
RETURNS = {DAYS[2]: 0.0199, MISSED: 0.02, DAYS[7]: -0.02}  # exactly 2% either way is a 2% day; 1.99% is not
OUTCOMES = {d: Outcome(i % 2 == 0, False, 15.0, RETURNS.get(d, 0.001)) for i, d in enumerate(DAYS)}
OWN = values({d: 0.3 for d in DAYS if d not in (ABSENT, MISSED)}, live=True)
BASE = values({d: 0.2 for d in DAYS if d != ABSENT}, live=True)
EXPECTED = MissReport(observable=9, missed=1, big_observable=2, big_missed=1, input_failures=1)

NO_DAYS = DayCounts(0, 0, 0, 0)


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
    def __init__(self, effective_start=DAYS[0], slot="rules"):
        self.registration, self.slot = Registration("weather_m1", effective_start), slot

    def registered(self):
        return {(V6_BIG_MOVE_5S, self.slot): self.registration}


def _scoring():
    return V4Scoring(Files(), Outcomes(), Registered())


def test_the_report_text_and_json_carry_the_miss_counts():
    reports = [_scoring().question_report(q) for q in QUESTIONS]
    assert f"    {EXPECTED.line()}" in report_lines(reports, frozen=False, as_of="2025-01-20", days=NO_DAYS)
    v6b = next(q for q in report_json(reports, frozen=False, as_of="2025-01-20", days=NO_DAYS)["questions"]
               if q["question"] == V6_BIG_MOVE_5S)  # fmt: skip
    assert v6b["cohorts"]["live"]["comparisons"][0]["misses"] == asdict(EXPECTED)
    assert v6b["cohorts"]["close_proxy"] == {"scores": {}, "comparisons": []}


def test_the_recorded_look_carries_each_members_miss_line(tmp_path, capsys):
    from fno.forecast_scoring.v4.cli import _look
    from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds

    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    (tmp_path / "FREEZE_v4.md").write_text("# Freeze\nFrozen on: 2024-12-31\n")
    at = datetime(2027, 5, 31, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    _look(_scoring(), records, FrozenToolThresholds(tmp_path), settled_slot_days(), LOOK_STOP_REVIEW, at)
    recorded = json.loads(records.path(LOOK_STOP_REVIEW).read_text())
    assert [V6_BIG_MOVE_5S, "rules", EXPECTED.line()] in recorded["misses"]
    assert recorded["test_a"] == "undecided"


class BrokenAfterFreeze(V4ForecastSource):
    """Live every day except 3-5 Jan, the three days straight after a 2 Jan freeze; the baseline never misses."""

    def forecasters(self, question):
        return ["base_rate", "weather_m1"]

    def values(self, question, forecaster):
        if forecaster == "base_rate":
            return BASE | values({ABSENT: 0.2}, live=True)
        return values({d: 0.3 for d in DAYS if d not in DAYS[2:5]}, live=True)


def test_after_the_freeze_misses_count_from_the_day_after_it_and_earlier_days_never_count():
    scoring = V4Scoring(BrokenAfterFreeze(), Outcomes(), Registered())
    member = scoring.member_comparisons(counted_after=DAYS[1])[(V6_BIG_MOVE_5S, "rules")]
    assert member.misses == MissReport(observable=8, missed=3, big_observable=2, big_missed=0, input_failures=0)
    assert member.misses.operations_undecided


class StartsAfterFreeze(BrokenAfterFreeze):
    """No row at all before 6 Jan, the fourth session after a 2 Jan freeze; live every day from then on."""

    def values(self, question, forecaster):
        if forecaster == "base_rate":
            return super().values(question, forecaster)
        return values({d: 0.3 for d in DAYS[5:]}, live=True)


def test_a_registered_slot_misses_from_its_effective_start_even_before_its_first_forecast():
    """Owner, 16 Oct 2026: an AI slot registered from day 1 after the freeze that first submits on day 4 has 3
    misses (days 1-3); its first forecast never moves the start."""
    scoring = V4Scoring(StartsAfterFreeze(), Outcomes(), Registered(DAYS[2], V4_SLOT_AI))
    member = scoring.member_comparisons(counted_after=DAYS[1])[(V6_BIG_MOVE_5S, V4_SLOT_AI)]
    assert member.misses == MissReport(observable=8, missed=3, big_observable=2, big_missed=0, input_failures=0)


def test_misses_never_count_before_a_later_effective_start():
    later = V4Scoring(StartsAfterFreeze(), Outcomes(), Registered(DAYS[5]))
    assert later.member_comparisons(counted_after=DAYS[1])[(V6_BIG_MOVE_5S, "rules")].misses.missed == 0


def test_a_void_day_neither_file_holds_is_not_an_input_failure():
    outcomes = OUTCOMES | {ABSENT: Outcome(True, True, 15.0, 0.001)}  # resolved, but void
    found = compare(V6_BIG_MOVE_5S, "weather_m1", "base_rate", paired_rows(OWN, BASE, outcomes), outcomes, 4)
    assert found.misses == MissReport(observable=9, missed=1, big_observable=2, big_missed=1, input_failures=0)
