"""G2 and G3 (story R1b, criteria 6 and 7): spent or exposed rows make a test exploratory, named; the sample plan's n,
its time, and `exploratory_shadow` above 3 years."""

import pytest

from fno.config import ROOT
from fno.factory.constants import Outcome
from fno.factory.data_spend import data_spend, parse_register
from fno.factory.fields import CardError
from fno.factory.sample_plan import SamplePlan, sample_plan

REGISTER = parse_register((ROOT / "research" / "DATA_SPEND.md").read_text(encoding="utf-8"))
SPENT = "NIFTY monthly options | NSE daily closes | 2019-2023"
EXPOSED = "India VIX | daily closes | 2017-2026"
FRESH = "NIFTY monthly option and future candles | Groww 15-minute candles (last trades) | 2019 - 2023"
FORWARD = "NIFTY options 15:00 bid/ask (A4) | Groww quotes | from 13 Oct 2026"


@pytest.mark.parametrize(("rows", "outcome", "named"), [
    ([FRESH, FORWARD], Outcome.FRESH, []), ([FRESH, SPENT], Outcome.EXPLORATORY, [SPENT]),
    ([EXPOSED, FORWARD], Outcome.EXPLORATORY, [EXPOSED])])  # fmt: skip
def test_the_rows_read_decide_fresh_or_exploratory(rows, outcome, named):
    verdict = data_spend(REGISTER, rows, "56", "card")
    assert verdict.outcome == outcome and [row.key for row in verdict.not_fresh] == named
    assert [row.key for row in verdict.rows] == rows


def test_a_registered_row_is_fresh_only_for_the_trial_it_names():
    text = "## Register\n\n| Data set | Price type | Period | Status | Used by | Notes |\n|---|---|---|---|---|---|\n"
    register = parse_register(text + "| X | quotes | 2027 | `registered` | 56 (its protocol) | |\n")
    assert data_spend(register, ["X | quotes | 2027"], "56", "card").outcome == Outcome.FRESH
    assert data_spend(register, ["X | quotes | 2027"], "5", "card").outcome == Outcome.EXPLORATORY


def test_a_row_not_in_the_register_is_refused_by_name():
    with pytest.raises(CardError, match="names 'NIFTY futures | ticks | 2030', which is not a row"):
        data_spend(REGISTER, ["NIFTY futures | ticks | 2030"], "56", "card")


@pytest.mark.parametrize(("frequency", "outcome"), [(1000, Outcome.PLANNED), (12, Outcome.EXPLORATORY_SHADOW)])
def test_the_sample_plan(frequency, outcome):
    plan = sample_plan(sd_per_trade=3000, expected_net=150, frequency_per_year=frequency, pass_level=0.01)
    assert plan.z == pytest.approx(2.3263, abs=1e-4)
    assert plan.n == 2165  # (2.3263 x 3000 / 150)^2 = 2164.7, rounded up
    assert plan.years == pytest.approx(2165 / frequency) and plan.outcome == outcome
    with pytest.raises(ValueError, match="above zero"):
        sample_plan(3000, 0, 12, 0.01)


@pytest.mark.parametrize(("years", "outcome"), [(3.0, Outcome.PLANNED), (3.0001, Outcome.EXPLORATORY_SHADOW)])
def test_the_three_year_limit_is_exact(years, outcome):
    assert SamplePlan(z=2.33, n=36, years=years).outcome == outcome
    assert sample_plan(3000, 150, 2165 / years, 0.01).outcome == outcome
