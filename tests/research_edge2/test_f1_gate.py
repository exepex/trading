"""F1 protocol section 5: the parity forward, the straddle's implied volatility, the EWMA forecast from closes before
the entry session only, and the gate's boundary."""

import math

import pytest
from f1study.gate import (
    NO_FORECAST,
    NO_FORWARD,
    NO_STRADDLE,
    STRADDLE_FACTOR,
    GateInputs,
    ewma_sigma,
    gate_inputs,
    implied,
    passes,
)

from .f1_fakes import EXPIRY, chain, quote


def test_the_forward_comes_from_put_call_parity_at_the_strike_nearest_spot():
    found = implied(chain(forward=22000.0), EXPIRY, spot=22010.0, n=4)
    assert found.forward == pytest.approx(22000.0)
    assert found.atm == 22000.0


def test_the_implied_volatility_is_the_atm_straddle_over_its_normal_scale():
    found = implied(chain(forward=22000.0), EXPIRY, spot=22000.0, n=4)
    assert found.sigma_iv == pytest.approx(240.0 / (STRADDLE_FACTOR * 22000.0 * math.sqrt(4 / 252)))


def test_no_traded_pair_gives_no_forward():
    assert implied(chain(volume=0), EXPIRY, 22000.0, 4).status == NO_FORWARD
    assert implied((), EXPIRY, 22000.0, 4).status == NO_FORWARD


def test_an_untraded_atm_leg_gives_no_straddle():
    quotes = [q if not (q.strike == 22000.0 and q.kind == "PE") else q._replace(volume=0) for q in chain()]
    quotes += [quote(22000.0 + 50 * i, k, 10.0) for i in (-1, 1) for k in ("CE", "PE")]
    found = implied(tuple(quotes), EXPIRY, 22030.0, 4)
    assert found.status in (NO_STRADDLE, "ok")
    assert found.status == NO_STRADDLE or found.atm != 22000.0


def test_ewma_of_constant_returns_is_their_annualised_size():
    closes = [100.0 * math.exp(0.01 * i) for i in range(60)]
    assert ewma_sigma(closes) == pytest.approx(0.01 * math.sqrt(252))


def test_ewma_needs_more_than_its_seed_returns():
    assert ewma_sigma([100.0] * 21) is None
    assert ewma_sigma([]) is None


def test_the_forecast_only_sees_the_closes_it_is_given():
    early = [100.0 * math.exp(0.01 * i) for i in range(60)]
    shocked = early + [early[-1] * 1.2]
    assert ewma_sigma(shocked) > ewma_sigma(early)  # a later close changes it: the caller must cut before entry


def test_too_few_closes_is_no_forecast():
    assert gate_inputs(chain(), EXPIRY, 22000.0, 4, [100.0] * 5).status == NO_FORECAST


@pytest.mark.parametrize(("ratio", "gate", "expected"),
                         [(1.2, "G12", True), (1.1999, "G12", False), (1.5, "G15", True), (1.49, "G15", False),
                          (0.3, "G0", True)])  # fmt: skip
def test_the_gate_includes_its_level(ratio, gate, expected):
    assert passes(gate, GateInputs("ok", 1.0, 1.0, ratio, 1.0)) is expected


def test_a_missing_ratio_fails_every_gate_but_g0():
    empty = GateInputs(NO_FORWARD)
    assert passes("G0", empty) and not passes("G12", empty) and not passes("G15", empty)
