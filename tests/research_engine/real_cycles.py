"""Decision contexts on the real panel for the look-ahead tests: the monthly expiry 30 to 45 calendar days away
(the furthest listed future expiry inside that range), entry the next session, exit 21 days before expiry."""

from __future__ import annotations

from datetime import date, timedelta

from fno.research_engine.features import DecisionContext, ResearchData

MIN_DAYS, MAX_DAYS, EXIT_DAYS = 30, 45, 21


def real_context(data: ResearchData, day: date) -> DecisionContext | None:
    expiries = [q.expiry for q in data.panel.futures.get(day, ()) if MIN_DAYS <= (q.expiry - day).days <= MAX_DAYS]
    later = [s.day for s in data.panel.sessions if s.day > day]
    if not expiries or not later:
        return None
    expiry = max(expiries)
    return DecisionContext(expiry, later[0], expiry - timedelta(days=EXIT_DAYS))


def decision_days(data: ResearchData, first: date, last: date) -> list[date]:
    """Sessions in the range that have a real context."""
    return [s.day for s in data.panel.sessions if first <= s.day <= last and real_context(data, s.day)]
