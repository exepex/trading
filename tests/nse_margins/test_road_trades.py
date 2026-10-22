"""Story MS-P1m: a credit spread priced in rupees worked by hand (the credit's `min(0, NOV)` and C2's cap binding), and
C2's proposal and open trade built from the same terms as the margin, so the two can never disagree."""

import hashlib

import pytest

from fno.constants import OPTION_PUT
from fno.nse_margins.calculator import NseIndexOptionExposure
from fno.nse_margins.road_margin import ArchivedSpanMargin, ArchivedSpanSource
from fno.nse_margins.road_trades import RoadTradeTerms, road_open_trade, road_proposal
from fno.research_engine.structures import Leg
from fno.risk.inputs import RiskInputError

from . import span_builder
from .span_builder import DAY, EXPIRY, default_options, risk, span_zip
from .test_road_margin import FACTOR, NAME

LEGS = (Leg(19_700.0, OPTION_PUT, -1), Leg(19_600.0, OPTION_PUT, 1))  # a bull put spread, 300 points below 20,000


def planted_spread(monkeypatch) -> bytes:
    """Scenario 1: the sold 19,700 put loses 120 a unit and the bought 19,600 put gains 70 (risk is a bought unit's
    loss), so the spread's scan is 50 a unit; prices 40 and 25, so the credit (NOV) is -15 a unit."""
    monkeypatch.setitem(span_builder.SF_PRICES, ("P", 19_700.0), 40.0)
    monkeypatch.setitem(span_builder.SF_PRICES, ("P", 19_600.0), 25.0)
    options = default_options() | {("P", 19_700.0): risk({1: -120.0}), ("P", 19_600.0): risk({1: -70.0})}
    return span_zip(series={EXPIRY: options})


def margin_on(data: bytes) -> ArchivedSpanMargin:
    shas = {DAY: hashlib.sha256(data).hexdigest()}
    return ArchivedSpanMargin(
        ArchivedSpanSource(lambda day: (NAME, data), lambda: shas, NseIndexOptionExposure(), lambda day: FACTOR)
    )


def test_a_credit_spread_in_rupees_worked_by_hand_with_c2_s_cap_binding(monkeypatch):
    """Per lot of 65: scan 3,250; NOV -975; exposure 2% x 20,000 x 65 = 26,000 (the short is 1.5% out of the money).
    At k 2.1 the SPAN part is max(0, 2.1 x 3,250 + 975) = 7,800, above C2's cap 100 x 65 - 975 = 5,525, so 5,525
    (never below the broker's own max(0, 3,250 + 975) = 4,225). Stressed: 5,525 - 975 + 2.1 x 26,000 = 59,150 a lot;
    at entry 5,525 + 54,600 = 60,125; the broker's 4,225 + 26,000 = 30,225."""
    margin, trade = margin_on(planted_spread(monkeypatch)), RoadTradeTerms("PCS", 100.0, 2, "NIFTY", EXPIRY, LEGS, 65)
    parts = margin.parts(trade, DAY)
    assert (parts.scan, parts.nov, parts.exposure, parts.span_cap) == pytest.approx((3_250.0, -975.0, 26_000.0,
                                                                                      5_525.0))  # fmt: skip
    assert margin.margin(trade, DAY) == pytest.approx(2 * 59_150.0)
    assert margin.margin_at_entry(trade, DAY) == pytest.approx(2 * 60_125.0)
    assert margin.broker_margin(trade, DAY) == pytest.approx(2 * 30_225.0)


def contract_of(underlying, expiry, leg):
    return f"{underlying}{expiry:%y%m%d}{leg.strike:g}{leg.kind}"


def test_c2_s_proposal_and_open_trade_carry_the_terms_own_lot_and_legs():
    trade = RoadTradeTerms("PCS", 100.0, 3, "BANKNIFTY", EXPIRY, LEGS, 30)
    proposal = road_proposal("p1", trade, contract_of)
    assert proposal.terms is trade and proposal.lot_size == 30
    assert [(p.contract, p.leg) for p in proposal.legs] == [("BANKNIFTY26112319700PE", LEGS[0]),
                                                            ("BANKNIFTY26112319600PE", LEGS[1])]  # fmt: skip
    held = road_open_trade("t1", trade, contract_of, -450.0)
    assert held.terms is trade and held.cash_flow == -450.0
    assert held.units == {"BANKNIFTY26112319700PE": -90, "BANKNIFTY26112319600PE": 90}  # side x 30 x 3


def test_the_record_carries_each_per_lot_figure_in_its_own_field(monkeypatch):
    found = margin_on(planted_spread(monkeypatch)).trade_record(
        RoadTradeTerms("PCS", 100.0, 1, "NIFTY", EXPIRY, LEGS, 65), DAY
    )
    assert (found["scan_per_lot_rs"], found["nov_per_lot_rs"], found["exposure_per_lot_rs"]) == (
        "3250.00", "-975.00", "26000.00"
    )  # fmt: skip


C, P = "CE", "PE"
SPREADS = {  # code: (the right legs, the same strikes with the other leg sold)
    "PCS": ((Leg(19_700.0, P, -1), Leg(19_600.0, P, 1)), (Leg(19_700.0, P, 1), Leg(19_600.0, P, -1))),
    "CCS": ((Leg(20_300.0, C, -1), Leg(20_400.0, C, 1)), (Leg(20_300.0, C, 1), Leg(20_400.0, C, -1))),
    "CDS": ((Leg(20_000.0, C, 1), Leg(20_100.0, C, -1)), (Leg(20_000.0, C, -1), Leg(20_100.0, C, 1))),
    "PDS": ((Leg(20_000.0, P, 1), Leg(19_900.0, P, -1)), (Leg(20_000.0, P, -1), Leg(19_900.0, P, 1))),
}


@pytest.mark.parametrize("code", sorted(SPREADS))
def test_each_spread_accepts_its_own_shape_and_refuses_the_other_leg_sold(code):
    right, wrong = SPREADS[code]
    RoadTradeTerms(code, 100.0, 1, "NIFTY", EXPIRY, right, 65)  # judge 492: each rule caught by its own plant
    with pytest.raises(RiskInputError, match="the wrong leg is sold"):
        RoadTradeTerms(code, 100.0, 1, "NIFTY", EXPIRY, wrong, 65)


@pytest.mark.parametrize(
    ("code", "call", "put"),
    [("SF", 20_000.0, 20_000.0), ("SC", 20_300.0, 19_700.0), ("BF", 20_000.0, 20_000.0)],
)
def test_a_fly_or_condor_with_only_its_put_wing_off_width_is_refused(code, call, put):
    body = -1 if code in ("SF", "SC") else 1
    legs = (Leg(call, C, body), Leg(put, P, body), Leg(call + 100.0, C, -body), Leg(put - 150.0, P, -body))
    with pytest.raises(RiskInputError, match="wings not 100 out"):
        RoadTradeTerms(code, 100.0, 1, "NIFTY", EXPIRY, legs, 65)
    RoadTradeTerms(code, 100.0, 1, "NIFTY", EXPIRY, (*legs[:3], Leg(put - 100.0, P, -body)), 65)
