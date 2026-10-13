"""Story G2 criteria 1 and 3, on real data: B1's look-ahead harness proves no baseline (and no Book 1 value) moves
when any panel value after the forecast day's close changes, and a refit uses only data before its refit day."""

import sys
from datetime import date, datetime, time
from pathlib import Path
from random import Random

import numpy
import pytest

from fno.composition import load_research_data
from fno.config import load_app_config
from fno.forecast.baselines import BaseRateBaseline, RiskNeutralBaseline
from fno.forecast.book1_method import book1_probabilities
from fno.forecast.history import ForecastHistory
from fno.forecast.models import ModelBaseline
from fno.forecast.wiring import GOLDEN_OPTION_DAYS, build_atm_iv30
from fno.research_engine.features import DecisionContext, Feature, ResearchData
from fno.storage.wiring import build_session_calendar

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_engine"))
from lookahead_harness import assert_no_lookahead, perturb_panel  # noqa: E402

CALENDAR, ESTIMATOR = build_session_calendar(), build_atm_iv30(load_app_config())


def _history(data: ResearchData) -> ForecastHistory:
    return ForecastHistory(data.panel, CALENDAR, ESTIMATOR)


class AllForecasts(Feature):
    """Every baseline's and Book 1's five probabilities on a day, as one value for the harness."""

    name = "G2 baselines and G3 Book 1"

    def value(self, data: ResearchData, day: date, context: DecisionContext) -> tuple:
        h = _history(data)
        by = {b.name: b.probabilities(day) for b in (RiskNeutralBaseline(h), BaseRateBaseline(h), ModelBaseline(h))}
        by["book1_rules"] = book1_probabilities(by)
        return tuple((name, q, p) for name, values in sorted(by.items()) for q, p in sorted(values.items()))


@pytest.fixture(scope="module")
def real_data():
    return load_research_data((2023, 2024, 2025, 2026), keep=lambda d, e: (e - d).days <= GOLDEN_OPTION_DAYS)


def test_no_baseline_or_book1_value_moves_when_later_data_changes(real_data):
    days = [s.day for s in real_data.panel.sessions if date(2025, 9, 1) <= s.day <= date(2026, 9, 1)]
    for day in sorted(Random(20261013).sample(days, 2)):
        value = assert_no_lookahead(AllForecasts(), real_data, day, DecisionContext(day, day, day), trials=1)
        assert sum(p is not None for _, _, p in value) >= 14  # real values, not None against None


def test_a_refit_uses_only_data_known_before_its_refit_day(real_data):
    """Every panel value after the refit day's close is changed; the fit serving a later day of that month is equal."""
    day = date(2026, 3, 25)
    model = ModelBaseline(_history(real_data))
    refit = model.refit_day(day)
    changed, count = perturb_panel(real_data, datetime.combine(refit, time(15, 30)), Random(1))
    assert count > 0
    other = ModelBaseline(_history(changed))
    for question in ("q3_rv20_above_trailing", "q4_vix_up_10d"):
        a, b = model.fit(question, day), other.fit(question, day)
        assert a is not None and numpy.array_equal(a.coefficients, b.coefficients)
        assert numpy.array_equal(a.residuals, b.residuals)
