"""Criterion 7 (readers): NSDL's monthly answer, one row per reporting date and category; anything else refused."""

from __future__ import annotations

from datetime import date

import pytest

from fno.flow_history.nsdl import BadAnswer, read_fpi_month

from .nsdl_pages import _day, page


def test_every_reporting_date_category_and_route_with_the_days_rate():
    month = read_fpi_month(page(), date(2019, 1, 2))
    assert sorted({r.reporting_date for r in month.rows}) == [date(2019, 1, 1), date(2019, 1, 2)]
    assert len(month.rows) == 2 * 7 and month.usd_inr == {date(2019, 1, 1): 11.1111, date(2019, 1, 2): 11.1111}
    first = month.rows[0]
    assert (first.category, first.route, first.values) == ("Equity", "Stock Exchange", (10.0, 13.0, -3.0, -0.3))
    carried = month.rows[1]
    assert (carried.category, carried.route) == ("Equity", "Primary market & others")
    total = month.rows[6]
    assert (total.category, total.route, total.values[2]) == ("Total", "", 2.0)


def test_the_month_and_year_totals_and_the_derivatives_are_left_out():
    month = read_fpi_month(page(), date(2019, 1, 2))
    assert all(r.category in ("Equity", "Debt", "Total") for r in month.rows)


def test_a_month_without_a_reporting_date_is_empty_not_an_error():
    assert read_fpi_month(page(days=()), date(2019, 1, 2)).rows == []


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (page(up_to="03-Jan-2019"), "title"),
        ("<html>Service unavailable</html>", "title"),
        (page(days=("01-Jan-2019", "03-Jan-2019")), "outside"),
        (page(days=("31-Dec-2018",)), "outside"),
        (page(days=("01-Jan-2019",)).replace("<tr><td>Total</td>", "<tr><td>Grand</td><td>x</td><td>y</td>"), "cells"),
        (page(days=("01-Jan-2019",)).replace("Total</td><td>16.00", "Overall</td><td>16.00"), "no Total row"),
        (page(days=("01-Jan-2019",)).replace(">10.00<", ">ten<"), "not a number"),
        (page(days=("01-Jan-2019",)).replace("Rs.11.1111", "11.1111"), "rate"),
        (page().replace("Investment Route", "Route"), "unexpected columns"),
    ],
)
def test_a_page_outside_the_layout_is_refused_whole(text, message):
    with pytest.raises(BadAnswer, match=message):
        read_fpi_month(text, date(2019, 1, 2))


def test_a_figures_row_before_any_date_is_refused():
    stray = "<tr><td>Sub-total</td><td>1</td><td>1</td><td>1</td><td>1</td></tr>"
    with pytest.raises(BadAnswer, match="before any reporting date"):
        read_fpi_month(page(days=("01-Jan-2019",)).replace(_day("01-Jan-2019"), stray + _day("01-Jan-2019")),
                       date(2019, 1, 2))  # fmt: skip
