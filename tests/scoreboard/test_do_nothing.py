"""Story S6 criteria 5-8: against doing nothing, after tax, on NSE's real index-close files of 7-13 Oct 2026. Every
expected figure below is written from the files' "Nifty 50" closes and "Div Yield" by hand. The fixtures are the
archived bytes (Drive's raw area), each equal to its row's SHA-256 in research/data/manifests/index-close.csv."""

import csv
import hashlib
import re
from datetime import date
from pathlib import Path

from fno.config import ROOT
from fno.evaluation.protocol import PROTOCOL_FILE, parse_protocol
from fno.scoreboard.do_nothing import NO_CAPITAL, TAX_LABEL, DoNothing, Terms, fo_after_tax, fund_after_tax
from fno.scoreboard.series import DailySeries
from fno.scoreboard.sources import ArchivedIndexLevels
from fno.storage.raw_source import NseIndexCloseSource

FILES = Path(__file__).resolve().parents[1] / "fixtures" / "nse" / "index_close"
DAYS = (date(2026, 10, 7), date(2026, 10, 8), date(2026, 10, 9), date(2026, 10, 12), date(2026, 10, 13))
# "Nifty 50" close and Div Yield from each file (ind_close_all_<ddmmyyyy>.csv)
CLOSE = (22603.05, 22231.8, 22520.45, 22363.35, 22721.95)
YIELD = (1.22, 1.24, 1.52, 1.53, 1.51)
TERMS = Terms(account_rs=2_000_000.0)


class Raw:
    def get(self, path: str):
        name = path.rsplit("/", 1)[-1]
        file = FILES / name
        return file.read_bytes() if file.is_file() else None


def against(terms=TERMS) -> DoNothing:
    return DoNothing(ArchivedIndexLevels(Raw()), terms)


def series(nets, days=DAYS):
    return DailySeries(tuple(days), tuple(nets), tuple(0.0 for _ in nets))


def test_the_fixtures_are_the_archived_bytes_of_the_manifest():
    with (ROOT / "research/data/manifests/index-close.csv").open() as file:
        manifest = {row["date"]: row["sha256"] for row in csv.DictReader(file)}
    for day in DAYS:
        data = (FILES / NseIndexCloseSource.filename_for(day)).read_bytes()
        assert hashlib.sha256(data).hexdigest() == manifest[day.isoformat()], day


def test_the_cash_rate_in_the_code_is_the_protocol_s_number():
    """Judge 196: the freeze hashes `Terms.cash_rate`; the protocol states the same number, so setting it on the freeze
    day changes both or this fails."""
    value = parse_protocol((ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")).items["do_nothing_benchmark"].value
    stated = re.search(r"Cash rate \(owner[^)]*\):\*\* ([0-9.]+)% a year", value)
    assert stated is not None and float(stated.group(1)) / 100 == TERMS.cash_rate


def test_the_adapter_reads_the_nifty_50_close_and_yield_from_the_archived_files():
    index = ArchivedIndexLevels(Raw())
    assert [(index(d).close, index(d).dividend_yield) for d in DAYS] == list(zip(CLOSE, YIELD, strict=True))
    assert NseIndexCloseSource.filename_for(DAYS[0]) == "ind_close_all_07102026.csv"


def test_view_a_rs_1_lakh_tied_for_5_sessions_and_a_book_net_of_rs_2000():
    """By hand from the files: each interval's fund return = close change + (Div Yield of the earlier day / 100 - 0.05%)
    x calendar days / 365: -1.639272%, +1.301626%, -0.685506% (3 days), +1.607571%; on Rs 1,00,000 that is
    -1,639.27 + 1,301.63 - 685.51 + 1,607.57 = Rs 584.42, after 20.8% tax Rs 462.86. Cash: 1,00,000 x 5.5% x 6 days
    / 365 = Rs 90.41, after 31.2% Rs 62.20. The book: 2,000 less 31.2% = Rs 1,376."""
    view = against().compare(series([2000.0, 0, 0, 0, 0]), [100_000.0] * 5, 0.0, [])["view_a"]
    assert (view["capital_days_rs"], view["book_after_tax_rs"]) == (500_000.0, 1376.0)
    assert (view["fund_after_tax_rs"], view["cash_after_tax_rs"]) == (462.86, 62.2)
    assert (view["beats_index_after_tax"], view["beats_cash_after_tax"]) == (True, True)


def test_view_b_the_whole_account_with_idle_cash_at_the_cash_rate():
    """Idle Rs 19,00,000 at 5.5% for 6 days = Rs 1,717.81, after tax 1,181.85, plus the book's 1,376 = Rs 2,557.85;
    the fund on Rs 20,00,000 gains 20 x 584.42 = Rs 11,688.38, after tax 9,257.20; cash Rs 1,808.22, after tax
    1,244.05."""
    view = against().compare(series([2000.0, 0, 0, 0, 0]), [100_000.0] * 5, 0.0, [])["view_b"]
    assert (view["book_with_idle_cash_rs"], view["fund_rs"], view["cash_rs"]) == (2557.85, 9257.2, 1244.05)
    assert (view["beats_index_after_tax"], view["beats_cash_after_tax"]) == (False, True)


def test_every_tax_figure_carries_the_assumption_label_and_an_unreadable_index_names_its_cause():
    result = against().compare(series([2000.0, 0, 0, 0, 0]), [100_000.0] * 5, 0.0, [])
    assert result["cash_rate_basis"] == "placeholder until the S1 freeze sets the 91-day T-bill yield"
    assert result["tax"] == TAX_LABEL and result["comparison"].startswith("point")
    blind = DoNothing(ArchivedIndexLevels(None), TERMS, "not computable: the archived index files cannot be read")
    out = blind.compare(series([2000.0, 0, 0, 0, 0]), [100_000.0] * 5, 0.0, [])
    assert out["view_a"]["reason"] == out["view_b"]["reason"] == blind.unavailable


def test_with_no_trade_and_no_operating_cost_view_b_equals_cash_and_view_a_has_no_capital():
    result = against().compare(series([0.0] * 5), [0.0] * 5, 0.0, [])
    assert result["view_a"]["reason"] == NO_CAPITAL and result["view_a"]["beats_index_after_tax"] is None
    assert result["view_b"]["book_with_idle_cash_rs"] == result["view_b"]["cash_rs"]
    assert result["view_b"]["beats_index_after_tax"] is not None  # view (b) still computes: all idle


def test_the_whole_account_tied_leaves_no_idle_credit():
    view = against().compare(series([0.0] * 5), [2_000_000.0] * 5, 0.0, [])["view_b"]
    assert view["book_with_idle_cash_rs"] == 0.0


def test_a_missing_index_day_is_not_computable_never_true():
    days = (*DAYS, date(2026, 10, 14))  # no file for 14 Oct in the fixtures
    view = against().compare(series([2000.0, 0, 0, 0, 0, 0], days), [100_000.0] * 6, 0.0, [])["view_a"]
    assert view["beats_index_after_tax"] is None and "2026-10-14" in view["reason"]


def test_a_trade_without_recorded_capital_and_an_unknown_ai_cost_give_no_verdict():
    view = against().compare(series([2000.0, 0, 0, 0, 0]), [100_000.0] * 5, None, [])["view_a"]
    assert view["beats_index_after_tax"] is None and view["book_after_tax_rs"] == 1376.0
    refused = against().compare(series([2000.0, 0, 0, 0, 0]), [100_000.0] * 5, 0.0, ["t-1"])["view_a"]
    assert refused["beats_index_after_tax"] is None and "t-1" in refused["reason"]


def test_fo_tax_per_financial_year_a_losing_year_untaxed_and_nothing_carried_forward():
    s = DailySeries((date(2026, 3, 31), date(2026, 4, 1)), (-2000.0, 5000.0), (0.0, 0.0))
    assert fo_after_tax(s, 0.312) == -2000.0 + 5000.0 - 0.312 * 5000.0
    assert fo_after_tax(DailySeries((date(2026, 4, 1),), (-2000.0,), (0.0,)), 0.312) == -2000.0


def test_the_fund_is_taxed_once_at_13_percent_above_the_exemption_from_12_months_else_20_8_percent():
    first = date(2025, 10, 13)
    assert fund_after_tax(200_000.0, first, date(2026, 10, 13), TERMS) == 200_000.0 - 0.13 * 75_000.0
    assert fund_after_tax(200_000.0, first, date(2026, 10, 12), TERMS) == 200_000.0 - 0.208 * 200_000.0
    assert fund_after_tax(-5000.0, first, date(2026, 10, 13), TERMS) == -5000.0
