"""Story C5, design 6.1a: for the books, margin data older than one session means no new entry, counted on NSE's
session calendar (A7); the Manual account keeps C2's 7 calendar days."""

from datetime import date

import pytest

from fno.research_engine.cycles import TradingDays
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margin_age import DaysOld, SessionsOld
from fno.risk.margins import MARGIN_COLUMNS, MarginTable
from fno.storage.table_source import FileTable
from fno.storage.wiring import build_session_calendar

ONE_SESSION = SessionsOld(TradingDays(build_session_calendar()), 1)
TERMS = TradeTerms("SF", 200.0, 1)


@pytest.mark.parametrize(
    ("as_of", "day", "fresh"),
    [
        (date(2026, 10, 14), date(2026, 10, 14), True),  # the day's own row
        (date(2026, 10, 13), date(2026, 10, 14), True),  # the previous session's
        (date(2026, 10, 12), date(2026, 10, 14), False),  # two sessions back, though two days old
        (date(2026, 10, 16), date(2026, 10, 19), True),  # Friday's row on Monday: a weekend never ages a row
        (date(2026, 10, 15), date(2026, 10, 19), False),
        (date(2026, 10, 19), date(2026, 10, 21), True),  # 20 Oct is an NSE holiday (calendar)
        (date(2026, 11, 6), date(2026, 11, 9), True),  # Sun 8 Nov muhurat: A14 writes no row for it (judge 105)
        (date(2026, 11, 5), date(2026, 11, 9), False),
        (date(2026, 1, 30), date(2026, 2, 2), False),  # Sun 1 Feb special session: A14 writes a row, so it counts
        (date(2026, 2, 1), date(2026, 2, 2), True),
    ],
)
def test_one_session_is_the_previous_trading_day_as_a14_counts_them(as_of, day, fresh):
    assert ONE_SESSION.fresh(as_of, day) is fresh


def test_the_manual_account_keeps_seven_calendar_days():
    assert DaysOld(7).fresh(date(2026, 10, 7), date(2026, 10, 14))
    assert not DaysOld(7).fresh(date(2026, 10, 6), date(2026, 10, 14))


def test_a_books_margin_row_two_sessions_old_refuses_the_trade_with_the_reason(tmp_path):
    path = tmp_path / "margins.csv"
    path.write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,40000,0,0,test calculator,2026-10-12\n")
    assert MarginTable(FileTable(path), DaysOld(7), 65).margin(TERMS, date(2026, 10, 14)) == 40_000
    with pytest.raises(RiskInputError, match="from 2026-10-12, older than 1 session"):
        MarginTable(FileTable(path), ONE_SESSION, 65).margin(TERMS, date(2026, 10, 14))
