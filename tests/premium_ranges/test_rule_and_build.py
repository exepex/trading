"""Criteria 1-2: the rule's hand values, the put's reversed quantiles, the drift term, the zero-step case, and every
"not ranged" reason counted."""

import math
from datetime import date

import pytest

from fno.premium_ranges.build import premium_record
from fno.premium_ranges.constants import (
    DECAY_ONLY,
    EXPIRES_BY_NEXT,
    NO_ATM_IV,
    NO_CHANGE,
    NO_DISTRIBUTION,
    NO_IV,
    RULE,
)
from fno.premium_ranges.rule import ContractInputs, Z, decay_only, forward_quantiles, no_change, rule_range
from fno.price_distribution.pricing import black76_price

from .builders import contract, expiry, g13_record

D, NEXT, E1, E2 = date(2026, 10, 16), date(2026, 10, 19), date(2026, 10, 27), date(2026, 11, 23)


def inputs(side: str) -> ContractInputs:
    return ContractInputs(23000.0, side, 150.0, 0.13, 23000.0, 0.14, 11, 0.065)


def test_forward_quantiles_carry_the_drift_term():
    found = forward_quantiles(23000.0, 0.14, 3)
    h = 3 / 365
    assert found[2] == pytest.approx(23000.0 * math.exp(-(0.14**2) * h / 2))
    assert found[0] == pytest.approx(23000.0 * math.exp(-(0.14**2) * h / 2 + Z[0] * 0.14 * math.sqrt(h)))


def test_a_call_is_priced_at_each_forward_and_a_put_reversed():
    forwards = forward_quantiles(23000.0, 0.14, 3)
    call = [black76_price(f, 23000.0, "CE", 8, 0.065, 0.13) for f in forwards]
    put = [black76_price(f, 23000.0, "PE", 8, 0.065, 0.13) for f in forwards]
    assert rule_range(inputs("CE"), 3) == pytest.approx(tuple(call))
    assert rule_range(inputs("PE"), 3) == pytest.approx(tuple(reversed(put)))
    assert list(rule_range(inputs("PE"), 3)) == sorted(rule_range(inputs("PE"), 3))


def test_a_zero_step_gives_the_decay_free_value_and_the_baselines_are_points():
    today = black76_price(23000.0, 23000.0, "CE", 11, 0.065, 0.13)
    assert rule_range(inputs("CE"), 0) == pytest.approx((today,) * 5)
    assert decay_only(inputs("CE"), 3) == (black76_price(23000.0, 23000.0, "CE", 8, 0.065, 0.13),) * 5
    assert no_change(inputs("CE")) == (150.0,) * 5


def test_a_record_ranges_every_contract_with_an_iv_and_counts_the_rest_by_reason():
    record = g13_record(D, [
        expiry(date(2026, 10, 19), 3, [contract(23000.0, "CE", 90.0)]),  # expires on d+
        expiry(E1, 11, [contract(23000.0, "CE", 150.0), contract(22500.0, "PE", 40.0, iv_points=None)]),
        expiry(E2, 38, [contract(23000.0, "PE", 300.0)], ok=False),
        expiry(date(2026, 12, 28), 73, [contract(23000.0, "PE", 500.0)], atm=None),
    ])  # fmt: skip
    found = premium_record(record, NEXT, "m" * 64, "2026-10-16T15:20:00+05:30")
    assert found["step_days"] == 3 and found["next_session"] == "2026-10-19" and found["source"] == "nse"
    assert found["not_ranged"] == {EXPIRES_BY_NEXT: 1, NO_ATM_IV: 1, NO_DISTRIBUTION: 1, NO_IV: 1}
    (row,) = found["rows"]
    assert (row["expiry"], row["strike"], row["side"], row["mid"], row["days"]) == (E1.isoformat(), 23000.0, "CE",
                                                                                     150.0, 11)  # fmt: skip
    own = ContractInputs(23000.0, "CE", 150.0, 0.14, 23000.0, 0.14, 11, 0.065)
    assert row[RULE] == pytest.approx(rule_range(own, 3), abs=1e-4)
    assert row[NO_CHANGE] == [150.0] * 5 and len(set(row[DECAY_ONLY])) == 1


def test_each_contract_keeps_its_own_iv_not_the_atm_iv():
    """Sticky strike (judge 465 note 1): the contract's IV of d prices its range; the ATM IV only moves the forward."""
    record = g13_record(D, [expiry(E1, 11, [contract(23500.0, "CE", 40.0, iv_points=17.5)], atm=12.0)])
    (row,) = premium_record(record, NEXT, "m" * 64, None)["rows"]
    own = ContractInputs(23500.0, "CE", 40.0, 0.175, 23000.0, 0.12, 11, 0.065)
    at_atm = ContractInputs(23500.0, "CE", 40.0, 0.12, 23000.0, 0.12, 11, 0.065)
    assert row[RULE] == pytest.approx(rule_range(own, 3), abs=1e-4)
    assert row[RULE][2] > rule_range(at_atm, 3)[2] + 1  # the ATM IV would price it far lower
    assert row[DECAY_ONLY] == pytest.approx(decay_only(own, 3), abs=1e-4)
