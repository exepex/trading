"""Story C2c: the owner's factor k multiplies the whole margin, scan and exposure, never the premium (owner, 15 Oct
2026). On NSE's real 14 Oct 2026 rows (`fixtures/margins_2026-10-14.csv`, lot 65): the story's five rows to the paisa in
C2 and C4; exactly k x what C2 counts for SF and SC, never below it for BF, between the two for the capped CCS and PCS;
never below the broker's unstressed figure for any code."""

import csv
from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.checks.validity_margin import stressed_per_lot
from fno.checks.validity_settings import MarginSettings
from fno.risk.inputs import TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MarginTable, MultiplierMargin
from fno.risk.settings import StressedMarginSettings
from fno.storage.table_source import FileTable
from tests.stress_factor_files import factor_file

REAL_ROWS = Path(__file__).parent / "fixtures" / "margins_2026-10-14.csv"
REAL = list(csv.DictReader(REAL_ROWS.open(encoding="utf-8")))
DAY, LOT, K = date(2026, 10, 14), 65, 1.45
KEYS = [(r["structure"], float(r["width"])) for r in REAL]


def c2(factor: float) -> MultiplierMargin:
    settings = StressedMarginSettings("multiplier", factor_file(factor, DAY - timedelta(days=1)), 30, None)
    return MultiplierMargin(MarginTable(FileTable(REAL_ROWS), DaysOld(7), LOT), settings)


def c4(code: str, width: float, factor: float) -> float:
    settings = MarginSettings(REAL_ROWS, 7, None, "multiplier", factor_file(factor, DAY - timedelta(days=1)), 30)
    return stressed_per_lot(REAL, (code, width, 1), DAY, settings, LOT)


def initial(code: str, width: float) -> float:
    return c2(1.0).margin(TradeTerms(code, width, 1), DAY)


@pytest.mark.parametrize(
    ("code", "width", "broker", "stressed", "at_entry"),
    [("SF", 100, 59_899.32, 86_854.01, 92_925.01), ("SF", 300, 62_679.37, 90_885.09, 108_019.09),
     ("SC", 300, 67_594.67, 98_012.27, 108_165.27), ("BF", 300, 59_077.07, 85_661.75, 85_661.75),
     ("CCS", 300, 38_968.08, 52_260.42, 63_567.17)],
)  # fmt: skip
def test_the_story_s_five_rows_to_the_paisa_in_c2_and_c4(code, width, broker, stressed, at_entry):
    terms = TradeTerms(code, width, 1)
    assert round(initial(code, width), 2) == broker
    assert round(c2(K).margin(terms, DAY), 2) == stressed
    assert round(c4(code, width, K), 2) == stressed
    assert round(c2(K).margin_at_entry(terms, DAY), 2) == at_entry


def test_ccs_300_by_hand():
    """Scan 9,429.55, NOV -11,306.75, exposure 29,538.53. The cap 300 x 65 - 11,306.75 = 8,193.25 is below the broker's
    SPAN 20,736.30, which stands; only the exposure is stressed: 20,736.30 - 11,306.75 + 1.45 x 29,538.53."""
    assert c2(K).margin(TradeTerms("CCS", 300, 1), DAY) == pytest.approx(20_736.30 - 11_306.75 + 1.45 * 29_538.53)
    assert c2(K).margin(TradeTerms("CCS", 300, 1), DAY) < K * initial("CCS", 300)  # 56,503.72


@pytest.mark.parametrize("key", KEYS, ids=str)
def test_the_stressed_margin_against_k_times_what_c2_counts(key):
    code, width = key
    stressed, whole = c2(K).margin(TradeTerms(code, width, 1), DAY), K * initial(code, width)
    if code in ("SF", "SC"):
        assert stressed == pytest.approx(whole)  # uncapped credit: exactly k x the whole margin
    elif code in ("CCS", "PCS"):
        assert initial(code, width) <= stressed <= whole + 1e-6  # the STR1 cap bounds the SPAN part
    else:
        assert stressed >= whole - 1e-6  # a debit: the premium paid is never multiplied (judge 75)
    assert stressed >= initial(code, width) - 1e-6  # never below the broker's unstressed figure


@pytest.mark.parametrize("factor", [1.0, 2.0])
@pytest.mark.parametrize("key", KEYS, ids=str)
def test_c2_and_c4_agree_at_any_factor(key, factor):
    code, width = key
    assert c4(code, width, factor) == pytest.approx(c2(factor).margin(TradeTerms(code, width, 1), DAY), abs=1e-6)


@pytest.mark.parametrize("key", [k for k in KEYS if k[0] in ("LC", "LP")], ids=str)
def test_a_bought_option_carries_no_exposure_so_k_leaves_it_at_the_broker_s_figure(key):
    code, width = key
    assert c2(K).margin_at_entry(TradeTerms(code, width, 1), DAY) == initial(code, width) == 0.0
