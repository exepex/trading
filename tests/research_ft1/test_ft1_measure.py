"""FT1 criteria 3, 5 (legs) and 8 (time part): signs and mirrors, stale and missing legs never substituted, the risk
scale, the hand Black-76 time part and the settled P&L of the flip share (PROTOCOL.md sections 6, 7, 9 and 14)."""

import math
from datetime import date, datetime, time

import pytest
from ft1study.days import DecisionDay
from ft1study.entries import build_entries
from ft1study.flips import FlipCounts, settled_pnl
from ft1study.observe import MISSING, NO_DEBIT, STALE, WIDTH_UNAVAILABLE
from ft1study.timepart import time_part
from ft1study.times import DECISION_15

from fno.research_engine.structures import BOUGHT, Leg
from tests.research_ft1.ft1_fakes import TERMS, FakeCalendar, Prices, chain, contracts, index_book, observer, structures

WED, THU, EXPIRY = date(2025, 1, 8), date(2025, 1, 9), date(2025, 1, 30)
CAL = FakeCalendar()
DAY = DecisionDay(WED, THU, EXPIRY, 16)
SPOT = 23010.0
INDEX = index_book({(WED, time(15, 0)): SPOT, (WED, time(15, 15)): 23005.0, (THU, time(9, 45)): 23300.0,
                    (THU, time(10, 15)): 23250.0})  # fmt: skip
MARKS = [(WED, time(15, 0)), (WED, time(15, 15)), (THU, time(9, 45)), (THU, time(10, 15))]


def price(strike: float, kind: str, mark: int) -> float:
    """A smooth synthetic price: decays with distance from 23000, every leg cheaper at each later mark."""
    return round(max(5.0, 150 - abs(strike - 23000) * 0.45) * (1 - 0.06 * mark) + (2 if kind == "PE" else 0), 2)


def priced(strikes=range(22400, 23650, 50)) -> Prices:
    prices = Prices()
    for k in strikes:
        for kind in ("CE", "PE"):
            for i, (d, t) in enumerate(MARKS):
                prices.option(EXPIRY, float(k), kind, d, t, price(float(k), kind, i))
    return prices


def entries():
    found, _ = build_entries([DAY], [DECISION_15], structures(), contracts([EXPIRY], WED, THU, CAL), INDEX)
    return {(e.family, e.width): e for e in found}


def test_a_falling_credit_is_a_positive_c_for_sf_and_the_mirrors_are_exact():
    built, watch = entries(), observer(priced(), INDEX, CAL)
    c = {code: watch.observe(built[(code, 200)], 5).c for code in ("SF", "BF", "CDS", "CCS", "PDS", "PCS")}
    assert c["SF"] > 0 and c["BF"] == -c["SF"]
    assert c["CDS"] == -c["CCS"] and c["PDS"] == -c["PCS"]
    legs = built[("SF", 200)].legs  # sold 23000 CE and PE, bought 23200 CE and 22800 PE
    v = [sum(leg.side * price(leg.strike, leg.kind, m) for leg in legs) for m in (0, 1)]
    assert c["SF"] == pytest.approx(v[1] - v[0], abs=1e-9)


def test_a_stale_leg_at_the_fill_removes_the_structure_even_when_the_decision_candle_traded():
    prices = priced()
    prices.option(EXPIRY, 23200.0, "CE", WED, time(15, 15), None)  # zero volume at the R = 5 fill
    built, watch = entries(), observer(prices, INDEX, CAL)
    found = watch.observe(built[("SF", 200)], 5)
    assert (found.excluded, found.c) == (STALE, None)
    assert watch.observe(built[("SF", 200)], 30).c is not None  # the other fill times keep it
    assert watch.observe(built[("PCS", 200)], 5).c is not None  # a structure without that leg is untouched


def test_a_missing_leg_is_left_out_and_no_other_price_stands_in():
    prices = priced()
    del prices.bars[("NSE-NIFTY-30Jan25-23000-PE", datetime.combine(THU, time(10, 15)))]
    found = observer(prices, INDEX, CAL).observe(entries()[("SF", 200)], 60)
    assert (found.excluded, found.c) == (MISSING, None)


def test_a_leg_not_listed_makes_the_width_unavailable():
    listed = contracts([EXPIRY], WED, THU, CAL)
    listed.listed[EXPIRY][WED] = chain([k for k in range(22000, 24000, 50) if k != 23200])
    found, _ = build_entries([DAY], [DECISION_15], structures(), listed, INDEX)
    sf = next(e for e in found if (e.family, e.width) == ("SF", 200))
    assert sf.legs is None
    assert observer(priced(), INDEX, CAL).observe(sf, 5).excluded == WIDTH_UNAVAILABLE


def test_the_risk_scale_is_the_width_or_a_long_options_debit():
    built, watch = entries(), observer(priced(), INDEX, CAL)
    assert watch.observe(built[("SF", 200)], 5).risk == 200.0
    assert watch.observe(built[("LC", 0)], 5).risk == price(23000.0, "CE", 0)
    prices = priced()
    prices.option(EXPIRY, 23000.0, "CE", WED, time(15, 0), 0.0)  # traded, at zero
    assert observer(prices, INDEX, CAL).observe(built[("LC", 0)], 5).excluded == NO_DEBIT


def _norm(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _black76_call(forward, strike, years, rate, sigma):
    d1 = (math.log(forward / strike) + 0.5 * sigma * sigma * years) / (sigma * math.sqrt(years))
    return math.exp(-rate * years) * (forward * _norm(d1) - strike * _norm(d1 - sigma * math.sqrt(years)))


def test_the_time_part_equals_a_hand_black_76_value():
    forward, strike, sigma = 23050.0, 23000.0, 0.15
    decided, filled = datetime(2025, 1, 8, 15, 0), datetime(2025, 1, 9, 10, 15)
    years = [(datetime(2025, 1, 30, 15, 30) - t).total_seconds() / 60 / (365 * 1440) for t in (decided, filled)]
    paid = _black76_call(forward, strike, years[0], 0.065, sigma)
    found = time_part([Leg(strike, "CE", BOUGHT)], [paid], forward, decided, filled, EXPIRY, 0.065)
    assert found == pytest.approx(_black76_call(forward, strike, years[1], 0.065, sigma) - paid, abs=1e-6)
    assert found < 0  # a bought option loses value overnight


def test_a_leg_without_an_iv_or_a_stale_future_leaves_the_time_part_not_computed():
    below_intrinsic = time_part([Leg(22000.0, "CE", BOUGHT)], [500.0], 23050.0, datetime(2025, 1, 8, 15),
                                datetime(2025, 1, 9, 10, 15), EXPIRY, 0.065)  # fmt: skip
    assert below_intrinsic is None
    prices = priced()
    prices.set("NSE-NIFTY-30Jan25-FUT", WED, time(15, 0), None)
    found = observer(prices, INDEX, CAL).observe(entries()[("SF", 200)], 60)
    assert found.c is not None and found.time_part is None


def test_the_settled_pnl_equals_a_hand_computation_with_c1_charges():
    legs, prices = [Leg(23000.0, "CE", BOUGHT)], [150.0]
    turnover = 150.0 * 65
    entry_fees = 20 + turnover * 0.03503 / 100 + turnover * 10 / 1e7 + turnover * 50 / 1e7
    entry = entry_fees + turnover * 0.003 / 100 + entry_fees * 0.18
    settlement = 20 + 300 * 65 * 0.15 / 100 + 20 * 0.18
    assert settled_pnl(legs, prices, 23300.0, 65, TERMS.charges) == pytest.approx(150 * 65 - entry - settlement)


def test_a_zero_pnl_is_not_a_win_and_flips_are_counted_both_ways():
    counts = FlipCounts().add(10.0, -1.0).add(5.0, 0.0).add(0.0, 3.0).add(-2.0, -1.0).add(4.0, 4.0)
    assert counts == FlipCounts(wins=3, bad=2, losses=2, good=1)


def test_the_flip_pnls_use_each_fills_own_prices_and_none_without_a_settlement():
    built = entries()
    settled = observer(priced(), INDEX, CAL, settlement={EXPIRY: 23100.0}).observe(built[("LC", 0)], 60)
    legs = built[("LC", 0)].legs
    assert settled.pnl_decision == pytest.approx(settled_pnl(legs, [price(23000.0, "CE", 0)], 23100.0, 65,
                                                             TERMS.charges))  # fmt: skip
    assert settled.pnl_fill == pytest.approx(settled_pnl(legs, [price(23000.0, "CE", 3)], 23100.0, 65, TERMS.charges))
    unsettled = observer(priced(), INDEX, CAL).observe(built[("LC", 0)], 60)
    assert unsettled.c is not None and unsettled.pnl_decision is None


def test_gap_vix_and_nights_come_from_the_index_the_vix_open_and_the_calendar():
    found = observer(priced(), INDEX, CAL, vix={WED: 14.2}).observe(entries()[("SF", 200)], 60)
    assert found.gap == pytest.approx(abs(23250.0 / SPOT - 1)) and found.vix == 14.2 and found.nights == 1
