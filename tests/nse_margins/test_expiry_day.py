"""Story MS-P1m round 2 (judge 491): a school trade on its own expiry day is priced, not refused, with SEBI's extra 2%
ELM on the short options expiring that day (SEBI/HO/MRD/TPD-1/P/CIR/2024/132 para 5.6, from 20 Nov 2024); so an
account holding an expiring position still enters on its other roads that day."""

import hashlib
from datetime import date, timedelta

import pytest

from fno.constants import OPTION_CALL
from fno.nse_margins.calculator import NseIndexOptionExposure
from fno.nse_margins.expiry_day_exposure import ExpiryDayIndexExposure
from fno.nse_margins.road_margin import ArchivedSpanMargin, ArchivedSpanSource
from fno.nse_margins.road_trades import RoadTradeTerms, road_open_trade, road_proposal
from fno.nse_margins.span_file import read_span_file
from fno.research_engine.structures import Leg, ShortIronFly
from fno.risk.inputs import RiskInputError
from fno.risk.rules import MarginRoom
from tests.risk.builders import book, contract, market
from tests.risk.test_rules import FixedCosts

from .span_builder import DAY, EXPIRY, default_options, span_zip
from .test_road_margin import FACTOR, NAME, PCS_LEGS

BOTH = {DAY: default_options(), EXPIRY: default_options()}  # a weekly expiring today and the monthly
TIERS = ((DAY, date(2031, 6, 24)),)


def margin_on(day: date, data: bytes) -> ArchivedSpanMargin:
    shas = {day: hashlib.sha256(data).hexdigest()}
    return ArchivedSpanMargin(
        ArchivedSpanSource(lambda d: (NAME, data), lambda: shas, ExpiryDayIndexExposure(), lambda d: FACTOR)
    )


def expiring_fly(data: bytes, expiry: date = DAY) -> RoadTradeTerms:
    span = read_span_file(data, NAME)
    legs = ShortIronFly().legs(frozenset(span.series[expiry]), span.underlying, 100.0)
    return RoadTradeTerms("SF", 100.0, 1, "NIFTY", expiry, tuple(legs), 65)


def test_an_expiring_fly_carries_2_plus_2_percent_on_each_short_worked_by_hand():
    """Index 20,000; two shorts at 20,000 (at the money): (2% + 2%) x 20,000 = 800 a unit each, so 1,600 a unit and
    104,000 a lot of 65 (A14's rule alone would give 52,000)."""
    data = span_zip(series=BOTH, futures=(DAY, EXPIRY), tiers=TIERS)
    margin = margin_on(DAY, data)
    assert margin.parts(expiring_fly(data), DAY).exposure == pytest.approx(104_000.0)
    assert margin.trade_record(expiring_fly(data), DAY)["expiry_day_extra_elm"].endswith("(SEBI 2024/132 para 5.6)")


def test_a_deep_out_of_the_money_short_carries_3_plus_2_percent():
    """Index 19,900; a call spread sold at 21,900, 2,000 out (more than 10% = 1,990): (3% + 2%) x 19,900 = 995 a unit,
    64,675 a lot."""
    data = span_zip(series=BOTH, futures=(DAY, EXPIRY), tiers=TIERS, underlying=19_900.0)
    legs = (Leg(21_900.0, OPTION_CALL, -1), Leg(22_000.0, OPTION_CALL, 1))
    trade = RoadTradeTerms("CCS", 100.0, 1, "NIFTY", DAY, legs, 65)
    assert margin_on(DAY, data).parts(trade, DAY).exposure == pytest.approx(64_675.0)


def test_any_other_day_is_a14_s_rule_unchanged():
    legs, rule = tuple(PCS_LEGS), ExpiryDayIndexExposure()
    assert rule.per_unit(legs, 20_000.0, EXPIRY, DAY) == NseIndexOptionExposure().per_unit(legs, 20_000.0, EXPIRY, DAY)


@pytest.mark.parametrize(
    ("day", "expiry"),
    [(date(2024, 11, 19), date(2024, 11, 19)), (DAY + timedelta(days=1), DAY)],
    ids=["an expiry day before SEBI's rule (not modelled)", "a day after expiry"],
)
def test_what_the_rule_does_not_model_still_refuses(day, expiry):
    data = span_zip(series={expiry: default_options()}, futures=(expiry,), tiers=((expiry, date(2031, 6, 24)),),
                    created=f"{day - timedelta(days=1):%Y%m%d}2128")  # fmt: skip
    with pytest.raises(RiskInputError, match="expiry-day"):
        margin_on(day, data).margin(expiring_fly(data, expiry), day)


def test_an_account_holding_an_expiring_trade_still_enters_another_road_that_day():
    """Judge 491's case: the held weekly expires today; the proposal is on the monthly. C2's room prices both."""
    data = span_zip(series=BOTH, futures=(DAY, EXPIRY), tiers=TIERS)
    margin, held_terms = margin_on(DAY, data), expiring_fly(data)
    new = RoadTradeTerms("PCS", 100.0, 1, "NIFTY", EXPIRY, tuple(PCS_LEGS), 65)

    def contract_of(underlying, expiry, leg):
        return contract(leg.strike, leg.kind, expiry)

    held = road_open_trade("weekly", held_terms, contract_of, 0.0)
    prices = {(leg.strike, leg.kind): 0.0 for leg in (*held_terms.legs, *new.legs)}
    quotes = market(20_000.0, prices, EXPIRY, day=DAY)
    quotes.quotes.update({contract_of("NIFTY", DAY, leg): quotes.quotes[contract(leg.strike, leg.kind, EXPIRY)]
                          for leg in held_terms.legs})  # fmt: skip
    needed = margin.margin(held_terms, DAY) + margin.margin(new, DAY)
    verdict = MarginRoom(margin, FixedCosts(0.0)).check(road_proposal("new", new, contract_of),
                                                       book([held], cash=needed, marked=needed), quotes)  # fmt: skip
    assert verdict.ok and verdict.numbers["needed_rs"] == pytest.approx(needed)


def test_the_school_s_wiring_prices_with_the_expiry_day_rule():
    """Judge 491.1: dropping the expiry-day rule from the wiring must fail a test (it would refuse expiring trades)."""
    from fno.config import load_app_config
    from fno.nse_margins.road_wiring import build_road_margin

    assert type(build_road_margin(load_app_config(), env={}).source.exposure) is ExpiryDayIndexExposure
