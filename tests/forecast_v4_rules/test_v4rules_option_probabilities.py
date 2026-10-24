"""Story G7b completion, criteria 7, 10-12: V5's option-implied probability (against a value computed here with 50-digit
decimals and an independent erf series, not by fno code), the two rule forecasters, chi-square(5), V4's and V5's
outcomes and their base-rate inputs."""

import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal, getcontext
from pathlib import Path

import pytest

from fno.desk.settlement import FinalSettlement, SettlementError, SettlementPrices
from fno.forecast_v4.settlement import V5Outcome
from fno.forecast_v4_rules.baselines import MISSING, OK
from fno.forecast_v4_rules.option_outcomes import (
    Refused,
    V4Result,
    V5Resolver,
    resolve_v4,
    v4_base_outcome,
    v5_base_outcome,
)
from fno.forecast_v4_rules.option_probabilities import (
    chi2_5_cdf,
    inside_probability,
    option_implied_probability,
    v4_ewma_chi2,
    v5_ewma_lognormal,
)
from fno.forecast_v4_rules.option_terms import OptionTerms, Void
from fno.forecast_v4_rules.series import SessionRv, live_intraday_rv
from fno.models import IST
from fno.storage.creation_times import CreationTimes
from fno.storage.raw_source import NseDailyFoSource

getcontext().prec = 50
ROOT = Path(__file__).resolve().parents[2]
PI = Decimal("3.14159265358979323846264338327950288419716939937510")
D, MONTHLY, WEEKLY = date(2026, 10, 27), date(2026, 11, 23), date(2026, 11, 3)
V5_TERMS = OptionTerms(D, MONTHLY, 26000.0, 26080.0, 380.0, 300.0, 0.14, 0.14, 18, 27)
V4_TERMS = OptionTerms(D, WEEKLY, 26000.0, 26080.0, 200.0, 150.0, 0.138, 0.138, 5, 7)


def decimal_norm_cdf(x: Decimal) -> Decimal:
    """`(1 + erf(x / sqrt 2)) / 2`, erf by its Taylor series (|x| < 3 here, 120 terms are ample at 50 digits)."""
    z, term, total = x / Decimal(2).sqrt(), x / Decimal(2).sqrt(), Decimal(0)
    for n in range(120):
        total += term / (2 * n + 1)
        term *= -z * z / (n + 1)
    return (1 + 2 / PI.sqrt() * total) / 2


def decimal_inside(forward, strike, premium, variance) -> Decimal:
    f, k, p, v = (Decimal(str(a)) for a in (forward, strike, premium, variance))
    z = lambda x: ((x / f).ln() + v / 2) / v.sqrt()  # noqa: E731
    return decimal_norm_cdf(z(k + p)) - decimal_norm_cdf(z(k - p))


def test_option_implied_probability_matches_the_golden_fixture_and_an_independent_50_digit_value():
    golden = json.loads((ROOT / "tests" / "fixtures" / "forecast_v4" / "v5_golden.json").read_text())
    expected = decimal_inside(26080.0, 26000.0, 680.0, 0.14**2 * 27 / 365)
    assert float(expected) == pytest.approx(float(golden["probability"]), abs=1e-15)
    value = option_implied_probability(V5_TERMS)
    assert value.status == OK and value.value == pytest.approx(float(golden["probability"]), abs=1e-13)
    assert 0.3 < value.value < 0.6  # a straddle priced near its fair value: about half the time inside


def test_drift_term_and_calendar_clock_matter():
    """A planted break that drops `s^2 tau / 2` or uses the session clock must change the value."""
    variance = 0.14**2 * 27 / 365
    f, k, p, v = Decimal("26080"), Decimal("26000"), Decimal("680"), Decimal(str(variance))
    without_drift = decimal_norm_cdf(((k + p) / f).ln() / v.sqrt()) - decimal_norm_cdf(((k - p) / f).ln() / v.sqrt())
    value = option_implied_probability(V5_TERMS).value
    assert abs(value - float(without_drift)) > 1e-4
    assert abs(value - inside_probability(26080.0, 26000.0, 680.0, variance * 365 / 252)) > 1e-3


def test_inside_probability_edges():
    assert inside_probability(26000.0, 26000.0, 30_000.0, 0.01) == pytest.approx(1.0, abs=1e-9)  # K - P below 0
    assert inside_probability(26000.0, 26000.0, 1e-6, 0.01) == pytest.approx(0.0, abs=1e-6)  # a tiny premium


def test_v5_rule_uses_s_e_sessions_of_the_ewma_variance():
    s2 = 0.00008
    value = v5_ewma_lognormal(V5_TERMS, s2)
    assert value.value == pytest.approx(float(decimal_inside(26080.0, 26000.0, 680.0, 18 * s2)), abs=1e-13)
    assert v5_ewma_lognormal(V5_TERMS, None).status == MISSING
    assert v5_ewma_lognormal(V5_TERMS, 0.0).status == MISSING


@pytest.mark.parametrize(
    "x, p",
    [(11.070497693516351, 0.95), (1.1454762260617692, 0.05), (4.351460191095526, 0.50), (15.08627246938899, 0.99)],
)
def test_chi2_5_matches_exact_quantiles(x, p):
    assert chi2_5_cdf(x) == pytest.approx(p, abs=1e-6)


def test_void_terms_give_missing_for_the_baseline_and_both_rules():
    void = Void(D, "spread")
    assert option_implied_probability(void).status == MISSING
    assert v5_ewma_lognormal(void, 0.00008).status == MISSING
    assert v4_ewma_chi2(void, 0.00008).status == MISSING


def test_chi2_5_edges():
    assert chi2_5_cdf(0.0) == 0.0 and chi2_5_cdf(-1.0) == 0.0
    assert chi2_5_cdf(200.0) == pytest.approx(1.0)


def test_v4_rule_is_chi2_5_of_the_integrated_implied_variance_over_s2():
    threshold = V4_TERMS.sigma_iv_session_clock**2 * 5 / 252  # 0.0003652... (v4_golden.json's 7-day case)
    assert threshold == pytest.approx(0.00036522739726027397, rel=1e-9)
    assert v4_ewma_chi2(V4_TERMS, 0.00008).value == pytest.approx(chi2_5_cdf(threshold / 0.00008))
    assert v4_ewma_chi2(V4_TERMS, None).status == MISSING
    assert v4_ewma_chi2(V4_TERMS, 0.0).status == MISSING


SESSIONS = [date(2026, 10, 27), date(2026, 10, 28), date(2026, 10, 29), date(2026, 10, 30), date(2026, 11, 2),
            date(2026, 11, 3), date(2026, 11, 4)]  # fmt: skip


def rows(values, seen_hour=20):
    return [SessionRv(d, v, datetime.combine(d, time(seen_hour), IST)) for d, v in zip(SESSIONS[1:], values)]


def test_v4_outcome_from_the_next_five_live_sessions():
    golden = [6e-05, 8e-05, 7e-05, 9e-05, 7e-05]  # v4_golden.json: realised 13.656% vs implied 13.567%: no
    result = resolve_v4(V4_TERMS, rows(golden), SESSIONS)
    assert result == V4Result(D, False, date(2026, 11, 3))
    assert v4_base_outcome(result).value is False and v4_base_outcome(result).resolved_on == date(2026, 11, 3)
    assert resolve_v4(V4_TERMS, rows([5e-05] * 5), SESSIONS).below is True


def test_v4_outcome_void_and_unresolved():
    assert resolve_v4(V4_TERMS, rows([6e-05, None, 7e-05, 9e-05, 7e-05]), SESSIONS).below is None
    assert v4_base_outcome(resolve_v4(V4_TERMS, rows([6e-05, None, 7e-05, 9e-05, 7e-05]), SESSIONS)) is None
    assert resolve_v4(V4_TERMS, rows([6e-05, 8e-05, 7e-05, 9e-05]), SESSIONS) is None  # the 5th row not there yet
    assert resolve_v4(V4_TERMS, [], SESSIONS) is None


def test_v4_outcome_is_known_when_its_last_row_was_first_seen():
    late = rows([6e-05] * 5)
    late[-1] = SessionRv(late[-1].day, 6e-05, datetime.combine(date(2026, 11, 4), time(9), IST))
    assert resolve_v4(V4_TERMS, late, SESSIONS).resolved_on == date(2026, 11, 4)


class Settlements(SettlementPrices):
    def __init__(self, price):
        self.price = price

    def final_settlement(self, underlying, expiry):
        if self.price is None:
            return None
        return FinalSettlement(underlying, expiry, self.price, NseDailyFoSource.path_for(expiry), "f" * 64)


class Created(CreationTimes):
    def __init__(self, at):
        self.at, self.asked = at, []

    def created_at(self, path):
        self.asked.append(path)
        return self.at


EXPIRY_CLOSE = datetime.combine(MONTHLY, time(15, 30), IST)


def test_v5_outcome_is_strict_and_frozen_with_its_source_and_drive_creation_time():
    created = Created(EXPIRY_CLOSE + timedelta(hours=5))
    outcome = V5Resolver(Settlements(26500.0), created, dict).resolve(V5_TERMS)
    assert isinstance(outcome, V5Outcome) and outcome.inside is True  # |26500 - 26000| < 680
    assert outcome.first_seen_at == EXPIRY_CLOSE + timedelta(hours=5)
    assert created.asked == [NseDailyFoSource.path_for(MONTHLY)]
    assert v5_base_outcome(D, outcome).resolved_on == MONTHLY
    edge = V5Resolver(Settlements(26680.0), created, dict).resolve(V5_TERMS)  # |level - K| == P: outside
    assert edge.inside is False


def test_v5_first_seen_falls_back_to_a8_then_stays_unresolved():
    sighting = EXPIRY_CLOSE + timedelta(hours=3)
    outcome = V5Resolver(Settlements(26500.0), Created(None), lambda: {MONTHLY: sighting}).resolve(V5_TERMS)
    assert outcome.first_seen_at == sighting
    assert V5Resolver(Settlements(26500.0), Created(None), dict).resolve(V5_TERMS) is None
    assert V5Resolver(Settlements(None), Created(sighting), dict).resolve(V5_TERMS) is None


def test_an_unclear_settlement_file_is_refused_not_raised():
    class Unclear(SettlementPrices):
        def final_settlement(self, underlying, expiry):
            raise SettlementError("two prices")

    refused = V5Resolver(Unclear(), Created(EXPIRY_CLOSE), dict).resolve(V5_TERMS)
    assert refused == Refused(D, "two prices")


def test_a16b_backfilled_and_other_method_rows_never_reach_v4():
    raw = [{"session": d.isoformat(), "method": "rv-candle-15m-v1", "status": "ok", "rv_session": "0.00005",
            "first_seen_at": f"{d.isoformat()}T20:00:00+05:30"} for d in SESSIONS[1:6]]  # fmt: skip
    assert resolve_v4(V4_TERMS, live_intraday_rv(raw), SESSIONS) is None


def test_v5_settlement_seen_before_the_expirys_close_is_refused():
    early = V5Resolver(Settlements(26500.0), Created(EXPIRY_CLOSE - timedelta(seconds=1)), dict).resolve(V5_TERMS)
    assert isinstance(early, Refused) and "first seen" in early.reason
    on_time = V5Resolver(Settlements(26500.0), Created(EXPIRY_CLOSE), dict).resolve(V5_TERMS)
    assert isinstance(on_time, V5Outcome)


def test_judge_585_sf1a_v5_base_outcome_is_dated_by_the_ist_day_it_was_first_seen():
    # the expiry-day file first seen two days after the expiry: the base rate may use it only from then
    seen = EXPIRY_CLOSE + timedelta(days=2)
    outcome = V5Resolver(Settlements(26500.0), Created(seen), dict).resolve(V5_TERMS)
    assert v5_base_outcome(D, outcome).resolved_on == MONTHLY + timedelta(days=2)
    # 23:30 IST on the expiry day is 18:00 UTC the same day; 00:30 IST next day is still the previous UTC day
    after_midnight = datetime.combine(MONTHLY + timedelta(days=1), time(0, 30), IST)
    outcome = V5Resolver(Settlements(26500.0), Created(after_midnight), dict).resolve(V5_TERMS)
    assert v5_base_outcome(D, outcome).resolved_on == MONTHLY + timedelta(days=1)


def test_judge_585_sf1b_drives_created_time_wins_over_a8s_sighting():
    created, sighting = EXPIRY_CLOSE + timedelta(hours=6), EXPIRY_CLOSE + timedelta(hours=2)
    outcome = V5Resolver(Settlements(26500.0), Created(created), lambda: {MONTHLY: sighting}).resolve(V5_TERMS)
    assert outcome.first_seen_at == created
