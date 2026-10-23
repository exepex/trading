"""Story STR1 criterion 8 (C2 side): width 0 (the ATM strike) and a margin of 0 are accepted for a bought-only
structure (LC, LP: NSE blocks no margin on a paid-up long option) and still refused for every structure with a sold
leg."""

from datetime import date

import pytest

from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MARGIN_COLUMNS, MarginParts, MarginTable
from fno.storage.table_source import FileTable

DAY = date(2026, 10, 14)


@pytest.mark.parametrize("code", ["LC", "LP"])
def test_a_bought_only_structure_may_be_at_width_0(code):
    assert TradeTerms(code, 0.0, 1).bought_only


@pytest.mark.parametrize("code", ["SF", "SC", "BF", "CDS", "CCS", "PDS", "PCS"])
def test_a_structure_with_a_sold_leg_needs_a_positive_width(code):
    with pytest.raises(RiskInputError, match="width"):
        TradeTerms(code, 0.0, 1)


@pytest.mark.parametrize("code", ["LC", "SF"])
def test_a_negative_width_is_always_refused(code):
    with pytest.raises(RiskInputError, match="width"):
        TradeTerms(code, -50.0, 1)


# A bought ATM call's SPAN row: scan 975 below its own value 7,800, no exposure (tests/nse_margins, LC at width 0)
PAID_UP = {"scan": 975.0, "nov": 7_800.0, "exposure": 0.0}


def test_a_paid_up_long_option_needs_no_margin_initial_stressed_or_at_entry():
    parts = MarginParts(**PAID_UP, what="LC width 0", bought_only=True)
    assert (parts.initial(), parts.stressed(1.45), parts.at_entry(1.45)) == (0.0, 0.0, 0.0)


def test_the_same_figures_for_a_structure_with_a_sold_leg_are_refused():
    parts = MarginParts(**PAID_UP, what="CDS width 100")
    for margin in (parts.initial, lambda: parts.stressed(1.45), lambda: parts.at_entry(1.45)):
        with pytest.raises(RiskInputError, match="must be above 0"):
            margin()


def test_the_margin_table_knows_a_bought_only_code_from_the_trade_terms(tmp_path):
    path = tmp_path / "margins.csv"
    rows = [f"{code},{width},975.00,7800.00,0.00,NSE SPAN test,{DAY}" for code, width in (("LC", 0), ("CDS", 100))]
    path.write_text(",".join(MARGIN_COLUMNS) + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    table = MarginTable(FileTable(path), DaysOld(7), 65)
    assert table.margin(TradeTerms("LC", 0.0, 2), DAY) == 0.0
    with pytest.raises(RiskInputError, match="must be above 0"):
        table.margin(TradeTerms("CDS", 100.0, 1), DAY)
