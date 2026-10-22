"""Part b's attribution (story MS-INS, criteria 1-9): stepwise Black-76 on the parity forward, costs from the fills and
the recorded spread, the residual balancing so the components less the costs are the net."""

import random
from dataclasses import replace
from datetime import date

import pytest

from fno.school.constants import OptionKind
from fno.school.contracts.snapshot import ContractKey
from fno.school.instructor.attribution.attribute import Components, add_step, attribute, is_poor_fit
from fno.school.instructor.attribution.points import snapshot_point
from fno.school.instructor.contracts import DataFault
from tests.school.instructor.attribution.fixtures import LONG, SHORT, UNITS, model_snapshot, path
from tests.school.instructor.builders import RULES

ENTRY_DAY, MIDDLE_DAY, EXIT_DAY = date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 4)
UNITS_BY_KEY = {SHORT: -UNITS, LONG: UNITS}


def test_the_hand_computed_put_spread():
    """Short 1000 put, long 900 put, 30 units each, expiry 23 Nov 2026 15:30 IST, rate 0. Entry 2 Nov 15:02, F = 1000,
    sigma = 0.20 (T0 = 30,268 minutes = 0.0575875 years); exit 4 Nov 15:02, F = 980, sigma = 0.22 (T1 = 0.0521081).

    Black-76 at entry, found independently by finite differences on B1's price:
    - 1000 put: mid 19.1453, delta -0.490427, gamma 0.00830983, vega 95.7082, theta -166.196 a year;
    - 900 put: mid 0.2255, delta -0.0132350, gamma 0.000708313, vega 8.15854, theta -14.1672 a year.

    With dF = -20, d(sigma) = +0.02 and dt = 0.0054795 years, signed units -30 and +30:
    - delta: -30 x -0.490427 x -20 + 30 x -0.013235 x -20 = -294.256 + 7.941 = -286.32;
    - gamma: (-30 x 0.00830983 + 30 x 0.000708313) x 1/2 x 400 = -45.61;
    - vega: (-30 x 95.7082 + 30 x 8.15854) x 0.02 = -52.53;
    - theta: (-30 x -166.196 + 30 x -14.1672) x 0.0054795 = +24.99.

    Market P&L at the mids: -30 x (31.4155 - 19.1453) + 30 x (0.8714 - 0.2255) = -348.73, so the residual (the higher
    orders of one 2-session step) is -348.73 + 286.32 + 45.61 + 52.53 - 24.99 = +10.74. Charges 4 x Rs 20 = 80; the
    spread paid 4 fills x 0.05 x 30 = 6.00; the net -348.73 - 80 - 6 = -434.73."""
    result = attribute(
        path((model_snapshot(ENTRY_DAY, 1000.0, 0.20), model_snapshot(EXIT_DAY, 980.0, 0.22))), 0.0, RULES
    )
    expected = dict(delta=-286.32, gamma=-45.61, vega=-52.53, theta=24.99, residual=10.74, charges=80.0, spread=6.0,
                    net=-434.73, steps=1, steps_merged=0, iv_unsolved=0, poor_fit=False)  # fmt: skip
    assert {k: round(getattr(result, k), 2) if isinstance(v, float) else getattr(result, k)
            for k, v in expected.items()} == expected  # fmt: skip
    assert result.closed_on == EXIT_DAY and result.rules_sha256 == RULES


def _step(start, end) -> Components:
    parts = Components()
    add_step(parts, snapshot_point(start, tuple(UNITS_BY_KEY), 0.0), snapshot_point(end, tuple(UNITS_BY_KEY), 0.0),
              UNITS_BY_KEY, 0.0)  # fmt: skip
    return parts


def test_a_pure_forward_move_has_no_vega_and_no_theta():
    start = model_snapshot(ENTRY_DAY, 1000.0, 0.20)
    end = replace(model_snapshot(ENTRY_DAY, 990.0, 0.20), finished_at=start.finished_at)
    parts = _step(start, end)
    assert abs(parts.vega) < 1e-4 and parts.theta == 0 and parts.delta != 0 and parts.gamma != 0


def test_a_pure_time_step_has_only_theta():
    parts = _step(model_snapshot(ENTRY_DAY, 1000.0, 0.20), model_snapshot(EXIT_DAY, 1000.0, 0.20))
    assert abs(parts.delta) < 1e-6 and abs(parts.gamma) < 1e-9 and abs(parts.vega) < 1e-4 and parts.theta > 0


def test_on_random_paths_the_residual_is_the_mid_to_mid_pnl_less_the_greeks():
    """The identity holds by construction; this checks that the costs measured from the fills leave exactly the
    mid-to-mid market P&L in the residual, on 200 random paths whose middle snapshot moves the market too."""
    draw = random.Random(20261023)
    for _ in range(200):
        moves = [(1000.0 * draw.uniform(0.95, 1.05), draw.uniform(0.12, 0.35)) for _ in range(3)]
        shots = tuple(model_snapshot(day, f, s) for day, (f, s) in zip((ENTRY_DAY, MIDDLE_DAY, EXIT_DAY), moves))
        result = attribute(path(shots), 0.0, RULES)
        market = sum(units * (shots[-1].quote(k).mid - shots[0].quote(k).mid) for k, units in UNITS_BY_KEY.items())
        greeks = result.delta + result.gamma + result.vega + result.theta
        assert result.residual == pytest.approx(market - greeks, abs=0.01) and result.steps == 2


def test_a_middle_snapshot_missing_a_leg_merges_its_step():
    shots = (model_snapshot(ENTRY_DAY, 1000.0, 0.20), model_snapshot(MIDDLE_DAY, 990.0, 0.21, drop=(LONG,)),
             model_snapshot(EXIT_DAY, 980.0, 0.22))  # fmt: skip
    result = attribute(path(shots), 0.0, RULES)
    assert (result.steps, result.steps_merged) == (1, 1)


def test_an_unsolvable_volatility_puts_that_legs_step_in_the_residual():
    start = snapshot_point(model_snapshot(ENTRY_DAY, 1000.0, 0.20), tuple(UNITS_BY_KEY), 0.0)
    end = snapshot_point(model_snapshot(EXIT_DAY, 980.0, 0.22), tuple(UNITS_BY_KEY), 0.0)
    whole, unsolved = Components(), Components()
    add_step(whole, start, end, UNITS_BY_KEY, 0.0)
    add_step(unsolved, replace(start, sigmas={**start.sigmas, SHORT: None}), end, UNITS_BY_KEY, 0.0)
    assert unsolved.iv_unsolved == 1 and abs(unsolved.delta) < abs(whole.delta)
    long_only = {LONG: UNITS}
    alone = Components()
    add_step(alone, start, end, long_only, 0.0)
    assert (unsolved.delta, unsolved.vega) == pytest.approx((alone.delta, alone.vega))  # only the long leg counted


def test_an_unsolvable_volatility_at_the_steps_end_also_goes_to_the_residual():
    start = snapshot_point(model_snapshot(ENTRY_DAY, 1000.0, 0.20), tuple(UNITS_BY_KEY), 0.0)
    end = snapshot_point(model_snapshot(EXIT_DAY, 980.0, 0.22), tuple(UNITS_BY_KEY), 0.0)
    parts = Components()
    add_step(parts, start, replace(end, sigmas={**end.sigmas, LONG: None}), UNITS_BY_KEY, 0.0)
    assert parts.iv_unsolved == 1


def test_a_settled_positions_last_step_ends_at_intrinsic_with_no_vega():
    shots = (model_snapshot(ENTRY_DAY, 1000.0, 0.20),)
    result = attribute(path(shots, settlement=985.0), 0.0, RULES)
    assert result.steps == 1 and result.vega == 0 and result.closed_on == date(2026, 11, 23)
    market = -UNITS * (15.0 - shots[0].quote(SHORT).mid) + UNITS * (0.0 - shots[0].quote(LONG).mid)
    assert result.residual == pytest.approx(market - (result.delta + result.gamma + result.theta), abs=0.01)


@pytest.mark.parametrize("residual, size, poor", [
    (200.0, 100.0, False), (200.01, 100.0, True), (-200.01, 100.0, True),  # Rs 200, at and beyond
    (250.0, 1000.0, False), (250.01, 1000.0, True),  # 25% of the components, at and beyond
])  # fmt: skip
def test_poor_fit_needs_both_rs_200_and_a_quarter_of_the_components(residual, size, poor):
    assert is_poor_fit(residual, size) is poor


def test_entry_and_exit_on_one_snapshot_is_costs_only():
    only = model_snapshot(ENTRY_DAY, 1000.0, 0.20)
    result = attribute(path((only,)), 0.0, RULES)
    assert (result.steps, result.delta, result.gamma, result.vega, result.theta) == (0, 0, 0, 0, 0)
    assert result.residual == pytest.approx(0.0, abs=0.01) and result.net == pytest.approx(-80.0 - 6.0, abs=0.01)


def test_a_faulted_path_or_a_missing_entry_or_exit_mid_is_not_attributed():
    shots = (model_snapshot(ENTRY_DAY, 1000.0, 0.20), model_snapshot(EXIT_DAY, 980.0, 0.22))
    assert attribute(replace(path(shots), faults=(DataFault.SNAPSHOT_MISSING,)), 0.0, RULES) is None
    no_exit_quote = (shots[0], model_snapshot(EXIT_DAY, 980.0, 0.22, drop=(SHORT,)))
    assert attribute(replace(path(shots), snapshots=no_exit_quote), 0.0, RULES) is None


def test_at_a_652_rate_theta_carries_its_rate_term():
    """r = 0.065: theta +24.70 by finite differences on B1's price at the path's own forward and volatilities (the
    parity forward reads 1000.00 and 980.00007); the residual pinned beside it."""
    shots = (model_snapshot(ENTRY_DAY, 1000.0, 0.20, rate=0.065), model_snapshot(EXIT_DAY, 980.0, 0.22, rate=0.065))
    result = attribute(path(shots), 0.065, RULES)
    assert (round(result.theta, 2), round(result.residual, 2), result.steps) == (24.70, 10.57, 1)


def test_the_spread_is_measured_from_the_fills_on_the_paths_own_mids_not_taken_from_the_record():
    shots = (model_snapshot(ENTRY_DAY, 1000.0, 0.20), model_snapshot(EXIT_DAY, 980.0, 0.22))
    clean = path(shots)
    other_basis = replace(clean, outcome=replace(clean.outcome, slippage_vs_mid=999.0))
    assert attribute(other_basis, 0.0, RULES) == attribute(clean, 0.0, RULES)
    assert round(attribute(clean, 0.0, RULES).spread, 2) == 6.0


def test_a_nan_price_on_an_unrelated_strike_does_not_spoil_the_forward():
    shots = (model_snapshot(ENTRY_DAY, 1000.0, 0.20), model_snapshot(EXIT_DAY, 980.0, 0.22))
    far_call = ContractKey(SHORT.expiry, 1100.0, OptionKind.CALL)
    bad = replace(shots[0].quote(far_call), bid=float("nan"))
    spoiled = (replace(shots[0], quotes={**shots[0].quotes, far_call: bad}), shots[1])
    result, clean = attribute(path(spoiled), 0.0, RULES), attribute(path(shots), 0.0, RULES)
    assert result.iv_unsolved == 0 and round(result.delta, 2) == round(clean.delta, 2)


def test_legs_on_two_expiries_are_not_attributed():
    """Every quote of both expiries is there, so only the one-expiry rule can refuse it."""
    later = date(2026, 12, 28)

    def both(day, forward, sigma):
        near, far_shot = model_snapshot(day, forward, sigma), model_snapshot(day, forward, sigma, expiry=later)
        return replace(near, expiries=(near.expiries[0], later), quotes={**near.quotes, **far_shot.quotes})

    clean = path((both(ENTRY_DAY, 1000.0, 0.20), both(EXIT_DAY, 980.0, 0.22)))
    far = replace(clean.outcome.entry.legs[1], key=replace(LONG, expiry=later))
    two = replace(clean.outcome.entry, legs=(clean.outcome.entry.legs[0], far))
    assert attribute(replace(clean, outcome=replace(clean.outcome, entry=two)), 0.0, RULES) is None


def test_a_session_the_road_was_closed_counts_as_a_merged_step():
    shots = (model_snapshot(ENTRY_DAY, 1000.0, 0.20), model_snapshot(EXIT_DAY, 980.0, 0.22))
    assert attribute(replace(path(shots), sessions_skipped=1), 0.0, RULES).steps_merged == 1
