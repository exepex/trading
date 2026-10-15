"""Story S6 criteria 5-8: against doing nothing, after tax, on NSE's real index-close files of 7-13 Oct 2026. Every
expected figure below is written from the files' "Nifty 50" closes and "Div Yield" by hand."""

from datetime import date
from pathlib import Path

import pytest

from fno.scoreboard.do_nothing import NO_CAPITAL, DoNothing, Terms, fo_after_tax, fund_after_tax
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


def by_hand(capital: float):
    """The fund's and cash's gain on `capital` tied at each previous close, before tax."""
    fund = cash = 0.0
    for i in range(1, len(DAYS)):
        span = (DAYS[i] - DAYS[i - 1]).days
        fund += capital * (CLOSE[i] / CLOSE[i - 1] - 1 + (YIELD[i - 1] / 100 - 0.0005) * span / 365)
        cash += capital * 0.055 * span / 365
    return fund, cash


def test_the_adapter_reads_the_nifty_50_close_and_yield_from_the_archived_files():
    index = ArchivedIndexLevels(Raw())
    assert [(index(d).close, index(d).dividend_yield) for d in DAYS] == list(zip(CLOSE, YIELD, strict=True))
    assert NseIndexCloseSource.filename_for(DAYS[0]) == "ind_close_all_07102026.csv"


def test_view_a_rs_1_lakh_tied_for_5_sessions_and_a_book_net_of_rs_2000():
    fund, cash = by_hand(100_000.0)
    view = against().compare(series([2000.0, 0, 0, 0, 0]), [100_000.0] * 5, 0.0, [])["view_a"]
    fund_after = fund - 0.208 * max(fund, 0.0)  # under 12 months
    cash_after = cash - 0.312 * max(cash, 0.0)
    assert view["capital_days_rs"] == 500_000.0 and view["book_after_tax_rs"] == 2000.0 - 624.0
    assert view["fund_after_tax_rs"] == pytest.approx(round(fund_after, 2), abs=0.005)
    assert view["cash_after_tax_rs"] == pytest.approx(round(cash_after, 2), abs=0.005)
    assert view["beats_index_after_tax"] == (fund_after < 1376.0) and view["beats_cash_after_tax"] is True


def test_view_b_the_whole_account_with_idle_cash_at_the_cash_rate():
    fund, cash = by_hand(2_000_000.0)
    _, idle_cash = by_hand(1_900_000.0)
    view = against().compare(series([2000.0, 0, 0, 0, 0]), [100_000.0] * 5, 0.0, [])["view_b"]
    assert view["book_with_idle_cash_rs"] == pytest.approx(round(1376.0 + idle_cash * (1 - 0.312), 2), abs=0.005)
    assert view["fund_rs"] == pytest.approx(round(fund - 0.208 * max(fund, 0.0), 2), abs=0.005)
    assert view["cash_rs"] == pytest.approx(round(cash * (1 - 0.312), 2), abs=0.005)


def test_with_no_trade_and_no_operating_cost_view_b_equals_cash_and_view_a_has_no_capital():
    result = against().compare(series([0.0] * 5), [0.0] * 5, 0.0, [])
    assert result["view_a"]["reason"] == NO_CAPITAL and result["view_a"]["beats_index_after_tax"] is None
    assert result["view_b"]["book_with_idle_cash_rs"] == result["view_b"]["cash_rs"]


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
