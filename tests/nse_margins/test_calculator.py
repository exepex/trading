"""Story A14: SPAN scanning risk plus NSE's exposure margin equals a hand calculation; unmodelled cases are refused."""

from datetime import date

import pytest

from fno.nse_margins.calculator import MarginOutsideModel, NseIndexOptionExposure, SpanMarginCalculator, months_later
from fno.nse_margins.rows import MarginRowBuilder, span_source
from fno.nse_margins.span_file import read_span_file
from fno.research_engine.structures import BOUGHT, SOLD, Leg, LongIronFly, ShortCondor, ShortIronFly

from .span_builder import (
    DAY,
    EXPIRY,
    LOT,
    SF_100_EXPOSURE,
    SF_100_NOV,
    SF_100_SPAN,
    UNDERLYING,
    default_options,
    span_zip,
)

SF_100 = [Leg(20000.0, "CE", SOLD), Leg(20000.0, "PE", SOLD), Leg(20100.0, "CE", BOUGHT), Leg(19900.0, "PE", BOUGHT)]


def calculator() -> SpanMarginCalculator:
    return SpanMarginCalculator(NseIndexOptionExposure(), LOT)


def span(**kwargs):
    return read_span_file(span_zip(**kwargs), "nsccl.20261014.i1.zip")


def test_a_short_iron_fly_matches_the_hand_calculation():
    figure = calculator().per_lot(span(), EXPIRY, SF_100, DAY)
    assert figure.span == SF_100_SPAN == 1950  # largest scenario loss 30 per unit x 65
    assert figure.exposure == pytest.approx(SF_100_EXPOSURE) == pytest.approx(52000)  # 2 short legs x 2% x 20000 x 65
    assert figure.nov == SF_100_NOV == -5_525  # sold 120 + 110, bought 75 + 70, x 65


def test_a_structure_that_gains_in_every_scenario_has_no_span_margin():
    long_fly = [Leg(leg.strike, leg.kind, -leg.side) for leg in SF_100]
    assert calculator().per_lot(span(), EXPIRY, long_fly, DAY).span == 0


def test_a_short_option_more_than_10_percent_out_of_the_money_pays_3_percent():
    far_call, near_put = Leg(22100.0, "CE", SOLD), Leg(19000.0, "PE", SOLD)  # 10.5% and 5% out of the money
    exposure = NseIndexOptionExposure().per_unit([far_call, near_put, Leg(20000.0, "CE", BOUGHT)], UNDERLYING,
                                                 EXPIRY, DAY)  # fmt: skip
    assert exposure == pytest.approx(0.03 * UNDERLYING + 0.02 * UNDERLYING)


@pytest.mark.parametrize("expiry", [DAY, date(2026, 10, 13), date(2027, 7, 15)])
def test_expiry_day_and_beyond_9_months_are_not_modelled(expiry):
    with pytest.raises(MarginOutsideModel, match="not modelled"):
        NseIndexOptionExposure().per_unit(SF_100, UNDERLYING, expiry, DAY)


def test_nine_months_ends_on_the_last_day_of_a_shorter_month():
    assert months_later(date(2026, 5, 31), 9) == date(2027, 2, 28)
    assert months_later(DAY, 9) == date(2027, 7, 14)


def test_a_leg_missing_from_the_series_is_refused():
    options = default_options()
    del options[("C", 20100.0)]
    with pytest.raises(MarginOutsideModel, match="not in the"):
        calculator().per_lot(span(series={EXPIRY: options}), EXPIRY, SF_100, DAY)


def test_an_expiry_in_two_overlapping_scan_tiers_is_refused():
    tiers = ((date(2026, 10, 19), date(2031, 6, 24)), (date(2026, 11, 1), date(2026, 12, 31)))
    with pytest.raises(MarginOutsideModel, match="scan tier"):
        calculator().per_lot(span(tiers=tiers), EXPIRY, SF_100, DAY)


def builder(widths=(100.0,)) -> MarginRowBuilder:
    return MarginRowBuilder((ShortIronFly(), ShortCondor(), LongIronFly()), widths, calculator(), 30)


def test_rows_use_the_first_monthly_expiry_30_days_out_and_name_the_file_and_its_sha256():
    found = builder().rows(span(), "ab" * 32, DAY)
    sf = next(r for r in found.rows if r.structure == "SF")
    source = f"NSE SPAN nsccl.20261014.i1.zip sha256={'ab' * 32}"
    assert sf.as_csv() == {"structure": "SF", "width": "100", "scan_per_lot_rs": "1950.00",
                           "nov_per_lot_rs": "-5525.00", "exposure_per_lot_rs": "52000.00", "source": source,
                           "as_of": "2026-10-14"}  # fmt: skip
    assert span_source("f.zip", "00") == "NSE SPAN f.zip sha256=00"
    assert [r.structure for r in found.rows] == ["SF", "SC", "BF"] and found.skipped == []
    assert builder().expiry_for(span(), DAY) == EXPIRY  # 27 Oct is only 13 days out


def test_a_width_with_an_unlisted_leg_gets_no_row_and_a_reason():
    found = builder(widths=(100.0, 5000.0)).rows(span(), "00", DAY)
    assert len(found.rows) == 3 and len(found.skipped) == 3
    assert all("width 5000: a leg is not listed" in reason for reason in found.skipped)


def test_no_monthly_expiry_far_enough_out_is_refused():
    with pytest.raises(MarginOutsideModel, match="no monthly expiry"):
        builder().expiry_for(span(futures=(date(2026, 10, 27),)), DAY)
