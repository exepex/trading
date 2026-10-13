"""Story B2 cycle dates on a hand-built calendar and panel: decision, entry and exit days, holidays and muhurat."""

from __future__ import annotations

from datetime import date

from fno.constants import SESSION_MUHURAT
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.panel_reader import FutureQuote, NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.cycles import Cycle, TradingDays, cycle_rows, monthly_cycles

SOURCE = "https://nsearchives.nseindia.com/content/circulars/test.pdf"
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n"
    f"2025-02-11,holiday,test holiday,{SOURCE}\n"
    f"2025-02-15,muhurat,test muhurat session on a Saturday,{SOURCE}\n"
    f"2025-03-06,holiday,test holiday,{SOURCE}\n"
)
MONTHLY, WEEKLY = date(2025, 3, 27), date(2025, 2, 20)


def panel(expiries: list[date], first=date(2025, 1, 1), last=date(2025, 3, 31), monthly=None) -> NiftyPanel:
    """Every session of the calendar (muhurat included) with a close, one option row per listed expiry and a future for
    each monthly expiry (`monthly`, default every expiry but the weekly 20 Feb)."""
    monthly = [e for e in expiries if e != WEEKLY] if monthly is None else monthly
    days = CALENDAR.sessions(first, last)
    sessions = tuple(SessionClose(d, CALENDAR.session_kind(d), 23000.0, 14.0) for d in days)
    rows = {d: tuple(OptionQuote(e, 23000.0, "CE", 100.0, 100.0, 1, 1) for e in expiries if e >= d) for d in days}
    futures = {d: tuple(FutureQuote(e, 23000.0, 23000.0, 1, 1) for e in monthly if e >= d) for d in days}
    return NiftyPanel(sessions, rows, futures)


def test_a_holiday_shortened_window_moves_entry_and_exit_to_trading_days():
    """Decision 10 Feb (45 days before 27 Mar); 11 Feb is a holiday, so entry is 12 Feb; 6 Mar (21 days before) is a
    holiday, so exit is 5 Mar. The weekly 20 Feb expiry has no future, so it is not monthly."""
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


def test_the_option_rows_the_simulator_needs_start_21_days_before_expiry():
    assert cycle_rows(date(2025, 3, 6), MONTHLY) and not cycle_rows(date(2025, 3, 7), MONTHLY)


def test_a_weekly_listed_far_ahead_or_moved_into_the_month_is_not_monthly():
    """2019-2022: NSE listed weeklies up to 69 days ahead (A5's 50-day horizon took them as monthly). A weekly moved to
    the month's end by a holiday (30 Apr 2025) is the month's last expiry. Neither has a future: neither is monthly."""
    far_weekly, moved_weekly = date(2025, 3, 20), date(2025, 3, 31)  # listed from 1 Jan: 78 and 89 days ahead
    cycles = monthly_cycles(panel([MONTHLY, far_weekly, moved_weekly], monthly=[MONTHLY]), CALENDAR)
    assert [c.expiry for c in cycles] == [MONTHLY]


def test_a_window_that_opened_before_the_panel_gives_no_cycle():
    """27 Mar's window opened on 10 Feb; a panel starting 12 Feb (11 Feb is a holiday) cannot know its first trading
    day."""
    assert monthly_cycles(panel([MONTHLY], first=date(2025, 2, 12)), CALENDAR) == []
    assert len(monthly_cycles(panel([MONTHLY], first=date(2025, 2, 10)), CALENDAR)) == 1
