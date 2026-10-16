"""G13 criterion 5: smile values. A flat-IV chain's smile value is its mid; one planted off-curve contract alone sits
outside its bid-ask; fewer than 5 out-of-the-money IVs give no smile; every record says it is no trade signal."""

import pytest

from fno.price_distribution.chain import ExpiryChain, Quote, SpreadFilter, used_quotes
from fno.price_distribution.constants import SMILE_VALUE_NOTE
from fno.price_distribution.records import valuation_dict
from fno.price_distribution.smile import contract_values, fit_smile
from fno.price_distribution.surface import otm_points
from fno.price_distribution.valuation import value_day
from tests.price_distribution.builders import FORWARD, NEAR, RATE, chain_day, expiry_chain, strikes

DAYS = 11


def values(chain):
    used = used_quotes(chain, SpreadFilter())
    smile, reason = fit_smile(otm_points(used, FORWARD, DAYS, RATE), FORWARD)
    return smile, reason, contract_values(used, smile, FORWARD, DAYS, RATE)


def test_a_flat_chain_s_smile_value_is_its_mid_within_a_paisa():
    smile, reason, found = values(expiry_chain())
    assert reason is None and smile.rmse_points < 1e-4
    assert max(abs(c.gap_rs) for c in found) < 0.01 and all(c.inside_spread for c in found)


def test_only_the_planted_off_curve_contract_is_outside_its_spread():
    """An in-the-money put: not in the out-of-the-money fit, so the curve itself does not move."""
    chain = expiry_chain()
    planted = tuple(Quote(q.strike, q.kind, q.price + 8, q.bid + 8, q.ask + 8) if (q.strike, q.kind) == (23_400, "PE")
                    else q for q in chain.quotes)  # fmt: skip
    _, _, found = values(ExpiryChain(NEAR, planted, None))
    outside = [(c.strike, c.kind) for c in found if not c.inside_spread]
    assert outside == [(23_400, "PE")]
    assert next(c for c in found if c.strike == 23_400 and c.kind == "PE").gap_rs == pytest.approx(-8, abs=0.5)


@pytest.mark.parametrize(("count", "fitted"), [(5, True), (4, False), (0, False)])
def test_a_smile_needs_five_out_of_the_money_ivs(count, fitted):
    grid = strikes(22_500, 22_500 + 50 * (count - 1)) if count else []
    smile, reason, found = values(expiry_chain(grid=grid)) if count else (*fit_smile((), FORWARD), ())
    assert (smile is not None) == fitted
    if not fitted:
        assert reason.startswith("too few out-of-the-money IVs") and all(c.smile_value is None for c in found)


def test_every_valuation_record_carries_the_no_signal_note():
    record = valuation_dict(value_day(chain_day(), SpreadFilter(), RATE), None)
    assert record["smile_value_note"] == SMILE_VALUE_NOTE and "no trade signal" in SMILE_VALUE_NOTE
