"""Experiment 1's monthly cycles (story B2, protocol section 3): one opportunity per NIFTY monthly expiry.

Decision day: the first trading day on which a monthly expiry (as of that day, by A5's `monthly_as_of` rule) is 30-45
calendar days away. Entry: the next trading day. Exit: the last trading day with 21 or more calendar days to expiry.
Trading days come from NSE's session calendar (story A1), never from weekdays; Diwali's one-hour muhurat session is
not a trading day here (its closes are not normal daily closes, research/data/nifty-panel/README.md), so no cycle
decides, enters or exits on it. A session the panel left out has no listing, so it cannot be a decision day; a cycle
whose exit is after the panel's last session is not complete and is not returned.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from ..constants import SESSION_MUHURAT
from ..research_data.calendar import SessionCalendar
from ..research_data.expiries import DAYS_TO_EXPIRY, monthly_as_of
from ..research_data.panel_reader import NiftyPanel

EXIT_MIN_DAYS = 21  # exit: the last trading day with at least this many calendar days to expiry

Listings = dict[date, dict[date, int]]  # day -> {listed expiry: calendar days to it}
ExpiryRule = Callable[[Listings], dict[date, set[date]]]  # listings -> the monthly expiries known on each day


@dataclass(frozen=True)
class Cycle:
    expiry: date
    decision_day: date
    entry_day: date
    exit_day: date

    @property
    def has_entry_window(self) -> bool:
        """Protocol section 3: an entry day not before the exit day leaves no holding period (`no_entry_window`)."""
        return self.entry_day < self.exit_day


def cycle_rows(day: date, expiry: date) -> bool:
    """`keep` for `read_nifty_panel`: the option rows cycles and the simulator use (21 or more days to expiry). It keeps
    every expiry more than 50 days away, so `monthly_as_of` sees the same monthly expiries as on the full panel."""
    return (expiry - day).days >= EXIT_MIN_DAYS


def listed_expiries(panel: NiftyPanel) -> Listings:
    """Each panel day's listed option expiries (of the rows the panel holds) with their calendar days to expiry."""
    return {day: {q.expiry: (q.expiry - day).days for q in quotes} for day, quotes in panel.options.items()}


class TradingDays:
    """The session calendar's sessions without muhurat sessions."""

    def __init__(self, calendar: SessionCalendar):
        self.calendar = calendar

    def is_trading_day(self, day: date) -> bool:
        kind = self.calendar.session_kind(day)
        return kind is not None and kind != SESSION_MUHURAT

    def next_after(self, day: date) -> date:
        day += timedelta(days=1)
        while not self.is_trading_day(day):
            day += timedelta(days=1)
        return day

    def last_on_or_before(self, day: date) -> date:
        while not self.is_trading_day(day):
            day -= timedelta(days=1)
        return day


def monthly_cycles(
    panel: NiftyPanel, calendar: SessionCalendar, expiry_rule: ExpiryRule = monthly_as_of
) -> list[Cycle]:
    """Every complete cycle of the panel, in decision-day order."""
    days = TradingDays(calendar)
    monthly = expiry_rule(listed_expiries(panel))
    data_days = [s.day for s in panel.sessions if s.underlying is not None and days.is_trading_day(s.day)]
    last_day = data_days[-1] if data_days else None
    cycles, seen = [], set()
    for day in data_days:
        for expiry in sorted(monthly.get(day, ())):
            if expiry in seen or not DAYS_TO_EXPIRY[0] <= (expiry - day).days <= DAYS_TO_EXPIRY[1]:
                continue
            seen.add(expiry)
            exit_day = days.last_on_or_before(expiry - timedelta(days=EXIT_MIN_DAYS))
            if exit_day <= last_day:
                cycles.append(Cycle(expiry, day, days.next_after(day), exit_day))
    return cycles
