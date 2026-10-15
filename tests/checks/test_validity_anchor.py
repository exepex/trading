"""Story STR1 (self-review finding): C4 re-derives the ATM strike from the committed snapshot (its spot and the
strikes with an A4-usable quote) and refuses a one- or two-leg trade not anchored there, or when it cannot tell."""

from datetime import datetime

import pytest

from fno.checks.validity_evidence import Evidence, QuoteRow
from tests.checks.test_validity_shapes import ONE_SIDE, ROWS
from tests.checks.validity_builders import SPOT, check, committed_store, failed, proposal
from tests.checks.validity_proposal_builder import one_side_proposal
from tests.checks.validity_sources import Margins

EXPIRY = "2026-10-27"


def evidence(spot, usable=(24_950.0, 25_000.0, 25_050.0), unusable=()):
    rows = {(EXPIRY, k, "CE"): QuoteRow(f"c{k}", 10.0, 11.0, None) for k in usable}
    rows |= {(EXPIRY, k, "CE"): QuoteRow(f"c{k}", None, None, None, "no bid") for k in unusable}
    return Evidence("exec", datetime(2026, 10, 14, 14, 55), rows, spot)


@pytest.mark.parametrize(
    ("spot", "atm"),
    [(25_000.0, 25_000.0), (25_024.99, 25_000.0), (25_025.0, 25_000.0), (25_025.01, 25_050.0), (24_975.0, 24_950.0)],
)
def test_the_atm_strike_is_the_nearest_usable_strike_the_lower_on_a_tie(spot, atm):
    assert evidence(spot).atm_strike(EXPIRY) == atm


def test_unusable_quotes_other_expiries_and_a_missing_spot_give_no_atm():
    assert evidence(25_040.0, usable=(25_000.0,), unusable=(25_050.0,)).atm_strike(EXPIRY) == 25_000.0
    assert evidence(25_000.0).atm_strike("2026-11-24") is None
    assert evidence(None).atm_strike(EXPIRY) is None
    assert evidence(25_000.0, usable=()).atm_strike(EXPIRY) is None


OFF_ANCHOR = {
    "LC deep in the money, width 300": ("LC", [(24_500, "CE", 1)], 300.0),
    "LP at ATM but width 100 claimed": ("LP", [(25_000, "PE", 1)], 100.0),
    "CDS one strike above ATM": ("CDS", [(25_050, "CE", 1), (25_250, "CE", -1)], 200.0),
    "PCS one strike below ATM": ("PCS", [(24_950, "PE", -1), (24_850, "PE", 1)], 100.0),
}


@pytest.mark.parametrize("name", sorted(OFF_ANCHOR))
def test_a_trade_off_the_atm_anchor_fails_the_shape(name):
    code, spec, width = OFF_ANCHOR[name]
    report = check(one_side_proposal(code, spec, width), store=committed_store(spot=SPOT), margins=Margins(ROWS))
    shape = next(r for r in report.results if r.name == "shape")
    assert "shape" in failed(report) and "ATM strike rule" in shape.reason  # the dearer ones also break the cap


@pytest.mark.parametrize("code", sorted(ONE_SIDE))
def test_without_a_spot_in_the_snapshot_a_new_code_fails_closed(code):
    spec, width = ONE_SIDE[code]
    report = check(one_side_proposal(code, spec, width), store=committed_store(), margins=Margins(ROWS))
    assert failed(report) == {"shape"}


def test_four_leg_trades_do_not_need_the_spot_as_before():
    assert check(proposal("SF")).ok and check(proposal("SF"), store=committed_store(spot=SPOT)).ok


def test_a_bought_option_with_a_zero_margin_row_passes_c4_end_to_end():
    spec, width = ONE_SIDE["LC"]
    zero = [dict(r, scan_per_lot_rs="5000.0", nov_per_lot_rs="13000.0") if r["structure"] == "LC" else r for r in ROWS]
    report = check(one_side_proposal("LC", spec, width), store=committed_store(spot=SPOT), margins=Margins(zero))
    room = next(r for r in report.results if r.name == "margin_room")
    assert report.ok and room.numbers["stressed_margin_rs"] == {"str1-lc-v1:2026-10-27": 0.0}
