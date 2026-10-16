"""Story A14: the SPAN reader keeps the NIFTY parts and refuses any file outside the modelled method."""

from datetime import date, datetime

import pytest

from fno.models import IST
from fno.nse_margins.span_file import BadSpanFile, read_span_file
from fno.storage.content_checks import VALIDATORS
from fno.storage.raw_source import NseSpanBodSource
from fno.storage.wiring import FINGERPRINT_SOURCES, LIBRARIAN_DATASETS

from .span_builder import EXPIRY, UNDERLYING, default_options, span_xml, span_zip


def test_the_nifty_parts_are_read_and_other_symbols_skipped():
    span = read_span_file(span_zip(), "nsccl.20261014.i1.zip")
    assert span.created == datetime(2026, 10, 13, 21, 28, tzinfo=IST)
    assert span.underlying == UNDERLYING  # BANKNIFTY's 50000 is another symbol's
    assert span.monthly_expiries == (date(2026, 10, 27), EXPIRY)
    option = span.series[EXPIRY][(20000.0, "CE")]
    assert option.risk[2] == -100.0 and option.risk[3] == 15.0 and len(option.risk) == 16
    assert span.tiers_holding(EXPIRY) == 1


@pytest.mark.parametrize(
    "data, reason",
    [
        (b"not a zip", "not a readable zip"),
        (span_zip(xml="<spanFile><created>2026"), "not valid XML"),
        (span_zip(symbol="BANKNIFTY"), "no phyPf"),
        (span_zip(som="25"), "short-option minimum"),
        (span_zip(adj="1.10000"), "adjustment rate"),
        (span_zip(cvf="2.00"), "contract value factor"),
        (span_zip(sc="0.50000"), "scaled"),
        (span_zip(tiers=()), "no scan tier"),
        (span_zip(created="yesterday"), "created stamp"),
        (span_zip(member="readme.txt"), "one .spn file"),
    ],
    ids=["zip", "xml", "symbol", "som", "adj", "cvf", "sc", "tiers", "created", "member"],
)
def test_a_damaged_or_unmodelled_file_is_refused(data, reason):
    with pytest.raises(BadSpanFile, match=reason):
        read_span_file(data, "nsccl.20261014.i1.zip")


def test_a_short_risk_array_is_refused():
    options = default_options()
    options[("C", 20000.0)] = (1.0,) * 15
    with pytest.raises(BadSpanFile, match="15 scenarios"):
        read_span_file(span_zip(series={EXPIRY: options}), "f.zip")


def test_an_unreadable_risk_value_is_refused():
    xml = span_xml().replace("<a>-100.00</a>", "<a>n/a</a>", 1)
    with pytest.raises(BadSpanFile, match="unreadable value"):
        read_span_file(span_zip(xml=xml), "f.zip")


def test_the_expiring_weekly_series_gets_its_own_tier_on_its_expiry_day():
    tiers = ((date(2026, 10, 13), date(2026, 10, 13)), (date(2026, 10, 19), date(2031, 6, 24)))  # NSE, 13 Oct 2026
    span = read_span_file(span_zip(tiers=tiers), "f.zip")
    assert span.tiers_holding(EXPIRY) == 1 and span.tiers_holding(date(2026, 10, 13)) == 1


def test_the_span_dataset_is_archived_by_the_librarian_with_its_content_check():
    day = date(2026, 10, 14)
    assert NseSpanBodSource.path_for(day) == "nse/derivatives/span-bod/2026/10/nsccl.20261014.i1.zip"
    assert NseSpanBodSource.url_for(NseSpanBodSource.path_for(day)) == (
        "https://nsearchives.nseindia.com/archives/nsccl/span/nsccl.20261014.i1.zip"
    )
    assert NseSpanBodSource.day_for("nsccl.20261014.i1.zip") == day
    assert LIBRARIAN_DATASETS["span-bod"] is NseSpanBodSource and FINGERPRINT_SOURCES["span-bod"] is NseSpanBodSource
    VALIDATORS[NseSpanBodSource]("nsccl.20261014.i1.zip", span_zip())
    with pytest.raises(ValueError):
        VALIDATORS[NseSpanBodSource]("nsccl.20261014.i1.zip", span_zip(som="1"))  # a minimum with no GROSS method
    VALIDATORS[NseSpanBodSource]("nsccl.20200407.i1.zip", span_zip(som="405", som_method="GROSS", tiers=None))  # 2020
