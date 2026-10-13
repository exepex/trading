"""Story B2 cycle dates on a hand-built calendar and panel: decision, entry and exit days, holidays and muhurat."""

from __future__ import annotations

from datetime import date

from fno.constants import SESSION_MUHURAT
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.panel_reader import NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.cycles import Cycle, TradingDays, cycle_rows, monthly_cycles

SOURCE = "https://nsearchives.nseindia.com/content/circulars/test.pdf"
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n"
    f"2025-02-11,holiday,test holiday,{SOURCE}\n"
    f"2025-02-15,muhurat,test muhurat session on a Saturday,{SOURCE}\n"
    f"2025-03-06,holiday,test holiday,{SOURCE}\n"
)
MONTHLY, WEEKLY = date(2025, 3, 27), date(2025, 2, 20)


def panel(expiries: list[date], first=date(2025, 1, 1), last=date(2025, 3, 31)) -> NiftyPanel:
    """Every session of the calendar (muhurat included) with a close and one option row per listed expiry."""
    days = CALENDAR.sessions(first, last)
    sessions = tuple(SessionClose(d, CALENDAR.session_kind(d), 23000.0, 14.0) for d in days)
    rows = {d: tuple(OptionQuote(e, 23000.0, "CE", 100.0, 100.0, 1, 1) for e in expiries if e >= d) for d in days}
    return NiftyPanel(sessions, rows, {})


def test_a_holiday_shortened_window_moves_entry_and_exit_to_trading_days():
    """Decision 10 Feb (45 days before 27 Mar); 11 Feb is a holiday, so entry is 12 Feb; 6 Mar (21 days before) is a
    holiday, so exit is 5 Mar. The weekly 20 Feb expiry is never listed 50+ days ahead, so it is not monthly."""
    assert monthly_cycles(panel([MONTHLY, WEEKLY]), CALENDAR) == [
        Cycle(MONTHLY, decision_day=date(2025, 2, 10), entry_day=date(2025, 2, 12), exit_day=date(2025, 3, 5))
    ]


def test_a_muhurat_session_is_never_a_cycle_day():
    """1 Apr is 45 days after the 15 Feb muhurat session: the decision is the next trading day, 17 Feb."""
    april = date(2025, 4, 1)
    cycles = monthly_cycles(panel([april], last=date(2025, 3, 31)), CALENDAR)
    assert [(c.decision_day, c.entry_day) for c in cycles] == [(date(2025, 2, 17), date(2025, 2, 18))]
    days = TradingDays(CALENDAR)
    assert CALENDAR.session_kind(date(2025, 2, 15)) == SESSION_MUHURAT and not days.is_trading_day(date(2025, 2, 15))
    assert days.next_after(date(2025, 2, 14)) == date(2025, 2, 17)
    assert days.last_on_or_before(date(2025, 2, 16)) == date(2025, 2, 14)


def test_a_cycle_whose_exit_is_after_the_panel_is_not_returned():
    assert monthly_cycles(panel([MONTHLY], last=date(2025, 3, 4)), CALENDAR) == []
    assert len(monthly_cycles(panel([MONTHLY], last=date(2025, 3, 5)), CALENDAR)) == 1


def test_the_panel_rows_cycles_need_start_21_days_before_expiry():
    assert cycle_rows(date(2025, 3, 6), MONTHLY) and not cycle_rows(date(2025, 3, 7), MONTHLY)
