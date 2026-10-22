"""Story MS-P1m: the school's margin per trade, on its own legs, from the archived beginning-of-day SPAN file. It is
A14's figure for those legs, the trade's own lot, C2's cap and factor; every way it cannot be that refuses by name."""

import hashlib
from datetime import date

import pytest

from fno.constants import OPTION_CALL, OPTION_PUT
from fno.nse_margins import road_margin
from fno.nse_margins.calculator import NseIndexOptionExposure, SpanMarginCalculator
from fno.nse_margins.road_margin import FACTOR_LABEL, ArchivedSpanMargin, ArchivedSpanSource, RoadTradeTerms
from fno.nse_margins.span_file import read_span_file
from fno.research_engine.structures import Leg, ShortIronFly
from fno.risk.capital import stress_cap_per_lot
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margins import MarginParts
from fno.risk.stress_factor import FactorRow

from .span_builder import DAY, EXPIRY, span_xml, span_zip

FILE = span_zip()
NAME = "nsccl.20261014.i1.zip"
FACTOR = FactorRow(date(2026, 10, 13), 2.1, "applied", "e" * 64)
SPAN = read_span_file(FILE, NAME)
SF_LEGS = tuple(ShortIronFly().legs(frozenset(SPAN.series[EXPIRY]), SPAN.underlying, 100.0))
PCS_LEGS = (Leg(19_700.0, OPTION_PUT, -1), Leg(19_600.0, OPTION_PUT, 1))  # one expected move out, not ATM


def source(files=None, manifest=None, calls=None):
    files = {DAY: FILE} if files is None else files

    def day_file(day):
        if calls is not None:
            calls.append(day)
        return NAME, files.get(day)

    shas = {d: hashlib.sha256(data).hexdigest() for d, data in files.items()} if manifest is None else manifest
    return ArchivedSpanSource(day_file, lambda: shas, NseIndexOptionExposure(), lambda day: FACTOR)


def terms(structure="SF", width=100.0, lots=2, underlying="NIFTY", expiry=EXPIRY, legs=SF_LEGS, lot=65):
    return RoadTradeTerms(structure, width, lots, underlying, expiry, tuple(legs), lot)


def a14(legs, structure, width, lot=65) -> MarginParts:
    """A14's own calculator on the same file and legs: what the school's figure must equal."""
    figure = SpanMarginCalculator(NseIndexOptionExposure(), lot).per_lot(SPAN, EXPIRY, legs, DAY)
    cap = stress_cap_per_lot(structure, width, figure.nov, lot)
    return MarginParts(figure.span, figure.nov, figure.exposure, structure, False, cap)


@pytest.mark.parametrize(("structure", "width", "legs"), [("SF", 100.0, SF_LEGS), ("PCS", 100.0, PCS_LEGS)])
def test_the_margin_is_a14_s_figure_for_the_trade_s_own_legs_at_c2_s_factor(structure, width, legs):
    margin, expected = ArchivedSpanMargin(source()), a14(legs, structure, width)
    trade = terms(structure, width, 2, legs=legs)
    assert margin.margin(trade, DAY) == pytest.approx(expected.stressed(2.1) * 2)
    assert margin.margin_at_entry(trade, DAY) == pytest.approx(expected.at_entry(2.1) * 2)
    assert margin.broker_margin(trade, DAY) == pytest.approx(expected.at_entry(1.0) * 2)


def test_the_trade_s_own_lot_is_used():
    margin = ArchivedSpanMargin(source())
    assert margin.margin(terms(lot=75, lots=1), DAY) == pytest.approx(a14(SF_LEGS, "SF", 100.0, 75).stressed(2.1))
    assert margin.margin(terms(lot=75, lots=1), DAY) != pytest.approx(margin.margin(terms(lot=65, lots=1), DAY))


def test_c2_s_one_side_cap_applies_to_a_spread():
    parts = ArchivedSpanMargin(source()).parts(terms("PCS", 100.0, 1, legs=PCS_LEGS), DAY)
    assert parts.span_cap == stress_cap_per_lot("PCS", 100.0, parts.nov, 65)


def test_another_index_is_read_from_its_own_part_of_the_file():
    midcap = span_zip(span_xml(symbol="MIDCPNIFTY", underlying=20_000.0))
    margin = ArchivedSpanMargin(source({DAY: midcap}))
    found = margin.parts(terms(underlying="MIDCPNIFTY", lot=120), DAY)
    expected = SpanMarginCalculator(NseIndexOptionExposure(), 120).per_lot(
        read_span_file(midcap, NAME, symbol="MIDCPNIFTY"), EXPIRY, SF_LEGS, DAY
    )
    assert (found.scan, found.nov, found.exposure) == (expected.span, expected.nov, expected.exposure)
    with pytest.raises(RiskInputError, match="for NIFTY"):  # the file has no NIFTY part
        margin.parts(terms(), DAY)


@pytest.mark.parametrize(
    ("files", "manifest", "day", "trade", "said"),
    [
        ({}, None, DAY, terms(), "not in the archive"),
        (None, {DAY: "0" * 64}, DAY, terms(), "differs from its manifest SHA-256"),
        ({DAY: span_zip(created="202610140900")}, None, DAY, terms(), "not before 09:00 on 2026-10-14"),
        (None, None, EXPIRY, terms(), "not in the archive"),
        ({EXPIRY: FILE}, None, EXPIRY, terms(), "expiry-day"),
        (None, None, DAY, terms(legs=(Leg(30_000.0, OPTION_CALL, -1), *SF_LEGS[1:])), "not in the"),
        ({DAY: b"not a zip"}, None, DAY, terms(), "school margin nsccl"),
    ],
    ids=["not archived", "not the first copy", "written at 09:00", "no file that day", "expiry day", "leg not listed",
         "damaged file"],
)  # fmt: skip
def test_every_way_the_figure_cannot_be_had_refuses_by_name(files, manifest, day, trade, said):
    with pytest.raises(RiskInputError, match=said):
        ArchivedSpanMargin(source(files, manifest)).margin(trade, day)


@pytest.mark.parametrize(
    ("kwargs", "said"),
    [
        ({"underlying": "SENSEX"}, "SENSEX"),
        ({"lot": 0}, "lot 0"),
        ({"legs": ()}, "0 legs"),
        ({"structure": "PCS", "legs": (Leg(19_700.0, OPTION_PUT, -1), Leg(19_500.0, OPTION_PUT, 1))}, "200 wide"),
    ],
    ids=["index outside the four", "no lot", "no legs", "width not the legs'"],
)
def test_a_school_trade_s_terms_refuse_what_the_margin_cannot_price(kwargs, said):
    with pytest.raises(RiskInputError, match=said):
        terms(**kwargs)


def test_terms_without_legs_are_refused_by_name():
    with pytest.raises(RiskInputError, match="carries no legs"):
        ArchivedSpanMargin(source()).margin(TradeTerms("SF", 100.0, 1), DAY)


def test_a_drive_failure_refuses_by_its_class_name_only():
    def down(day):
        raise ConnectionError("token=secret")

    margin = ArchivedSpanMargin(ArchivedSpanSource(down, dict, NseIndexOptionExposure(), lambda day: FACTOR))
    with pytest.raises(RiskInputError, match=r"could not be read \(ConnectionError\)") as caught:
        margin.margin(terms(), DAY)
    assert "secret" not in str(caught.value)


def test_the_file_is_read_once_per_session_and_parsed_once_per_index(monkeypatch):
    calls, parsed, real = [], [], road_margin.read_span_file
    monkeypatch.setattr(road_margin, "read_span_file", lambda *a, **k: parsed.append(k["symbol"]) or real(*a, **k))
    margin = ArchivedSpanMargin(source(calls=calls))
    for trade in (terms(), terms("PCS", 100.0, 1, legs=PCS_LEGS), terms(lots=3)):
        margin.margin(trade, DAY)
        margin.margin_at_entry(trade, DAY)
    assert calls == [DAY] and parsed == ["NIFTY"]


def test_the_records_name_the_file_the_factor_and_its_label():
    margin = ArchivedSpanMargin(source())
    assert margin.record() == {"method": "archived_span_per_trade", "factor_label": FACTOR_LABEL}
    found = margin.trade_record(terms("PCS", 100.0, 1, legs=PCS_LEGS), DAY)
    assert found["span_file"] == NAME and found["span_sha256"] == hashlib.sha256(FILE).hexdigest()
    assert found["stress_factor_row"]["factor"] == "2.1" and found["factor_label"] == FACTOR_LABEL
    assert found["legs"] == "-1x19700PE +1x19600PE" and found["lot"] == "65" and found["expiry"] == "2026-11-23"
    assert FACTOR_LABEL == "k measured on NIFTY monthly only [reasoning only]"


def test_the_wiring_needs_no_drive_until_a_margin_is_asked_and_reads_c2_s_factor_file():
    from fno.config import load_app_config
    from fno.nse_margins.road_wiring import build_road_margin
    from fno.risk.wiring import build_risk_manager

    margin = build_road_margin(load_app_config(), env={})
    assert margin.record()["method"] == "archived_span_per_trade"
    assert margin.source.factor(date(2026, 10, 15)).factor == 1.45  # the owner's seed, the day after it
    with pytest.raises(RuntimeError, match="Drive"):  # no settings: refused when a figure is first asked
        margin.margin(terms(), DAY)
    assert build_risk_manager(load_app_config()).rules  # the desk's own C2 path builds as before


def test_the_day_s_file_is_downloaded_once_whatever_asks_for_it():
    calls = []
    margin = ArchivedSpanMargin(source(calls=calls))
    margin.record(DAY)
    margin.margin(terms(), DAY)
    with pytest.raises(RiskInputError, match="for MIDCPNIFTY"):  # a second index: same file, its own part
        margin.margin(terms(underlying="MIDCPNIFTY", lot=120), DAY)
    margin.trade_record(terms(), DAY)
    assert calls == [DAY]
