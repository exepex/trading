"""Story A14c criterion 4: 2020's SPAN method read by hand. A history read (`allow_short_option_minimum`) takes one
GROSS short-option minimum per short unit, and a file without `scanTiers` as one tier; the SPAN figure is the larger of
the scanning risk and the minimum times the short units. A14's daily read still refuses both, and any other minimum
shape is refused by name even in a history read."""

import pytest

from fno.nse_margins.span_file import BadSpanFile, read_span_file

from .span_builder import DAY, EXPIRY, LOT, SF_100_SPAN, span_zip
from .test_calculator import SF_100, calculator

NAME = "nsccl.20200407.i1.zip"


def history(**kwargs):
    return read_span_file(span_zip(**kwargs), NAME, allow_short_option_minimum=True)


def test_a_binding_minimum_is_the_span_figure():
    """405 a short unit (2020's rate), 2 short legs, lot 65: 52,650, above the scan's 1,950."""
    figure = calculator().per_lot(history(som="405", som_method="GROSS"), EXPIRY, SF_100, DAY)
    assert figure.span == 405 * 2 * LOT == 52_650


def test_a_minimum_below_the_scan_leaves_the_scan():
    """10 a short unit: 1,300, below the scan's 1,950."""
    figure = calculator().per_lot(history(som="10", som_method="GROSS"), EXPIRY, SF_100, DAY)
    assert figure.span == SF_100_SPAN == 1950


def test_a_file_without_scan_tiers_is_one_tier_in_a_history_read_only():
    figure = calculator().per_lot(history(tiers=None, som="405", som_method="GROSS"), EXPIRY, SF_100, DAY)
    assert figure.span == 52_650
    with pytest.raises(BadSpanFile, match="no scan tier"):
        read_span_file(span_zip(tiers=None), NAME)


def test_a_daily_read_still_refuses_any_minimum():
    with pytest.raises(BadSpanFile, match="short-option minimum charge is not modelled"):
        read_span_file(span_zip(som="405", som_method="GROSS"), NAME)


@pytest.mark.parametrize("method", ["NET", ""], ids=["net", "no method"])
def test_a_minimum_other_than_one_gross_rate_is_refused_even_in_history(method):
    with pytest.raises(BadSpanFile, match="only one GROSS short-option minimum rate"):
        history(som="405", som_method=method)


def test_a_zero_minimum_reads_the_same_in_both_modes():
    daily, past = read_span_file(span_zip(), NAME), history()
    assert daily.short_option_minimum == past.short_option_minimum == 0.0
    assert calculator().per_lot(daily, EXPIRY, SF_100, DAY) == calculator().per_lot(past, EXPIRY, SF_100, DAY)
