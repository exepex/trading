"""Story STR1b criteria 1 and 2 (C2 side): the capital split on NSE's real 14 Oct 2026 margin rows
(`fixtures/margins_2026-10-14.csv`, made by A14's builder from `nsccl.20261014.i1.zip`, SHA-256 d85b883a...e8b5b; see
research/2026-10-15-str1b-samples/real_rows.py), at the owner's factor 1.45 and one NIFTY lot of 65.

The owner's factor no longer adds 0.45 x premium to a paid-up long option or 0.45 x debit to a debit spread; a credit
spread's stressed SPAN figure is capped at the width less the credit; SF, SC and BF are uncapped, row by row. Story C2c:
k also stresses the exposure, outside the cap (LC and LP carry none, so they are unchanged)."""

import csv
from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.risk.capital import stress_cap_per_lot
from fno.risk.inputs import TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MarginTable, MultiplierMargin
from fno.risk.rules import MarginRoom, capital_at_entry
from fno.risk.settings import StressedMarginSettings
from fno.storage.table_source import FileTable
from tests.stress_factor_files import factor_file

REAL_ROWS = Path(__file__).parent / "fixtures" / "margins_2026-10-14.csv"
DAY, LOT, K = date(2026, 10, 14), 65, 1.45
ROWS = list(csv.DictReader(REAL_ROWS.open(encoding="utf-8")))
SETTINGS = StressedMarginSettings("multiplier", factor_file(K, DAY - timedelta(days=1)), 30, None)
MARGIN = MultiplierMargin(MarginTable(FileTable(REAL_ROWS), DaysOld(7), LOT), SETTINGS)


def row(code: str, width: float) -> dict[str, float]:
    found = next(r for r in ROWS if r["structure"] == code and float(r["width"]) == width)
    return {k: float(found[f"{k}_per_lot_rs"]) for k in ("scan", "nov", "exposure")}


def at_entry(code: str, width: float) -> float:
    return MARGIN.margin_at_entry(TradeTerms(code, width, 1), DAY)


def test_the_fixture_is_nse_s_real_rows_for_every_code_and_width():
    assert {r["source"].split()[-1] for r in ROWS} == {
        "sha256=d85b883ae4ca6015261a1ae126d8a3ed87a0a882c86932f2af842879270e8b5b"
    }
    assert len(ROWS) == 9 * 5 + 2  # nine codes at the five research widths, plus LC and LP at the ATM width 0
    assert row("CDS", 200) == {"scan": 7939.75, "nov": 7939.75, "exposure": 29538.53}  # judge 106's figures
    assert row("LC", 0) == {"scan": 35174.75, "nov": 35174.75, "exposure": 0.0}


@pytest.mark.parametrize(
    ("code", "width", "before"),
    [("LC", 0, 0.45 * 35174.75), ("LP", 300, 0.45 * 13224.25), ("CDS", 200, 0.45 * 7939.75 + 29538.53),
     ("PDS", 300, 0.45 * 5827.25 + 29538.53)],
)  # fmt: skip
def test_a_bought_option_or_debit_spread_carries_no_stress_reserve_on_its_premium(code, width, before):
    """Before STR1b: 0.45 x premium (Rs 15,828.64 on the ATM call) or 0.45 x debit (Rs 3,572.89 on CDS 200). Story
    C2c: the exposure (CDS, PDS: 29,538.53; LC, LP: 0) is stressed by k, the premium never is."""
    exposure = row(code, width)["exposure"]
    assert at_entry(code, width) == pytest.approx(K * exposure)
    assert at_entry(code, width) == pytest.approx({"LC": 0.0, "LP": 0.0}.get(code, 42_830.8685))  # was 29,538.53
    assert MARGIN.broker_margin(TradeTerms(code, width, 1), DAY) == pytest.approx(exposure)
    assert before + (K - 1) * exposure - at_entry(code, width) == pytest.approx(0.45 * row(code, width)["nov"])


@pytest.mark.parametrize(("code", "width"), [("CCS", 100), ("PCS", 100), ("CCS", 300), ("PCS", 300)])
def test_a_credit_spread_s_stress_extra_is_capped_at_the_width_less_the_credit(code, width):
    r = row(code, width)
    cap, broker = width * LOT + r["nov"], max(0.0, r["scan"] - r["nov"])  # the row's NOV is minus the credit
    expected = max(broker, min(max(0.0, K * r["scan"] - r["nov"]), cap)) + K * r["exposure"]  # exposure outside the cap
    assert at_entry(code, width) == pytest.approx(expected)
    assert at_entry(code, width) >= MARGIN.broker_margin(TradeTerms(code, width, 1), DAY)


def test_the_ccs_100_split_by_hand():
    """scan 2,957.50, NOV -3,935.75 (credit 3,935.75), exposure 29,538.53. The broker's own SPAN is 2,957.50 +
    3,935.75 = 6,893.25 (Groww's basis, judge 77 addendum 3). The stressed span 1.45 x 2,957.50 + 3,935.75 = 8,224.13 is
    capped at 100 x 65 - 3,935.75 = 2,564.25, below the broker's figure, so the broker's 6,893.25 stands: no reserve on
    the SPAN part. Story C2c: the exposure 29,538.53 is stressed, 1.45 x 29,538.53 = 42,830.87."""
    assert MARGIN.broker_margin(TradeTerms("CCS", 100, 1), DAY) == pytest.approx(6893.25 + 29538.53)
    assert at_entry("CCS", 100) == pytest.approx(6893.25 + 42830.8685)  # 49,724.12; before C2c 36,431.78


@pytest.mark.parametrize("code", ["SF", "SC", "BF"])
@pytest.mark.parametrize("width", [100, 150, 200, 250, 300])
def test_four_leg_margins_are_uncapped_on_every_real_row(code, width):
    r = row(code, width)
    assert at_entry(code, width) == max(0.0, K * r["scan"] - r["nov"]) + K * r["exposure"]
    assert MARGIN.margin(TradeTerms(code, width, 1), DAY) == (
        max(0.0, K * r["scan"] - r["nov"]) + min(0.0, r["nov"]) + K * r["exposure"]
    )


def test_the_cap_is_only_for_str1_codes():
    assert [stress_cap_per_lot(c, 100, -1000.0, LOT) for c in ("SF", "SC", "BF")] == [None] * 3
    assert stress_cap_per_lot("LC", 0, 5000.0, LOT) == 0.0
    assert stress_cap_per_lot("PCS", 100, -1000.0, LOT) == 5500.0
    assert stress_cap_per_lot("PCS", 100, -7000.0, LOT) == 0.0  # a credit above the width: nothing left to lose


def test_capital_tied_is_broker_margin_plus_premium_and_the_reserve_is_apart():
    lc = capital_at_entry(broker_margin=0.0, premium_paid=35_174.75 + 40.0, margin_at_entry=0.0)
    assert lc == {"broker_margin": 0.0, "premium_paid": 35_214.75, "stress_reserve": 0.0, "total_funds": 35_214.75,
                  "capital_tied": 35_214.75}  # fmt: skip
    sf = capital_at_entry(broker_margin=65_000.0, premium_paid=47_600.0, margin_at_entry=65_400.0)
    assert sf["stress_reserve"] == 400.0 and sf["capital_tied"] == 112_600.0 and sf["total_funds"] == 113_000.0


def test_margin_room_records_an_lc_s_capital_as_its_premium_plus_charges(tmp_path):
    """A bought ATM call on the real LC 0 row: broker margin 0, no stress reserve: capital tied = premium + charges."""
    from tests.risk.builders import book, market, proposal
    from tests.risk.test_funds_at_entry import CHARGES, GrowwCosts

    premium, charges = 35_174.75, CHARGES
    room = MarginRoom(MARGIN, GrowwCosts(premium, 0.0))
    expiry = date(2026, 11, 24)
    lc = proposal("lc", "LC", 0.0, [(22700.0, "CE", 1)], expiry)
    verdict = room.check(lc, book([], cash=500_000.0, marked=500_000.0),
                         market(22721.95, {(22700.0, "CE"): premium / LOT}, expiry, day=DAY))  # fmt: skip
    capital = verdict.numbers["capital_rs"]["lc"]
    assert verdict.ok and capital["broker_margin"] == 0.0 and capital["stress_reserve"] == 0.0
    assert capital["capital_tied"] == capital["total_funds"] == pytest.approx(premium + charges)


RESERVES = [
    ("LC", 0, 0.0),
    ("LP", 300, 0.0),
    ("CDS", 200, 13_292.3385),
    ("PDS", 300, 13_292.3385),
    ("CCS", 100, 13_292.3385),
]


@pytest.mark.parametrize(("code", "width", "reserve"), RESERVES)
def test_the_stress_reserve_is_the_capped_span_extra_plus_the_exposure_s_stress(code, width, reserve):
    """Story C2c changes STR1b's reserve: LC and LP keep 0 (no exposure); CDS, PDS and CCS 100 (whose SPAN extra is
    capped to 0 on these rows) carry 0.45 x 29,538.53 = 13,292.34, the exposure's stress, outside the cap."""
    terms = TradeTerms(code, width, 1)
    assert at_entry(code, width) - MARGIN.broker_margin(terms, DAY) == pytest.approx(reserve)
