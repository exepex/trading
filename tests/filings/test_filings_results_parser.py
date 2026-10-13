from datetime import date
from decimal import Decimal

import pytest

from fno.filings.results_parser import parse_results
from fno.filings.xbrl import NotXbrl, read_facts
from tests.filings.xbrl_fixtures import results_xbrl


def test_reads_quarter_profit_and_half_year_cash_flow():
    f = parse_results(results_xbrl())
    assert f.period_end == date(2025, 9, 30)
    assert (f.revenue, f.profit_before_tax, f.net_profit, f.eps) == (1000, 200, 150, Decimal("12.5"))
    assert (f.total_debt, f.cash, f.total_assets, f.equity) == (300, 400, 9000, 5000)
    assert (f.operating_cash_flow, f.investing_cash_flow, f.financing_cash_flow) == (300, -120, -80)
    assert f.cash_flow_months == 6
    assert f.has_balance_sheet and f.has_cash_flow


def test_segment_figures_are_never_read_as_the_company_total():
    assert parse_results(results_xbrl()).revenue == 1000  # the 400 is one segment's (a dimension)


def test_legacy_files_use_the_periods_their_own_facts_declare():
    """NSE's pre-2025 files give the half-year context the quarter's dates; its facts say April to September."""
    f = parse_results(results_xbrl(legacy=True))
    assert f.revenue == 1000 and f.operating_cash_flow == 300 and f.cash_flow_months == 6


def test_a_quarter_without_balance_sheet_reports_none_never_a_guess():
    f = parse_results(results_xbrl(half_year=False))
    assert f.revenue == 1000
    assert f.total_assets is None and f.operating_cash_flow is None and f.cash_flow_months is None
    assert not f.has_balance_sheet and not f.has_cash_flow


def test_bank_names_total_income_borrowings_and_equity_parts():
    f = parse_results(results_xbrl(bank=True))
    assert (f.revenue, f.total_debt, f.equity) == (1000, 700, 100)


def test_an_error_page_is_not_xbrl():
    with pytest.raises(NotXbrl):
        read_facts(b"<html><body>Access Denied</body></html>")
    with pytest.raises(NotXbrl):
        read_facts(b"not xml at all")
