"""Which NIFTY expiry is the monthly one, decided only from the expiries listed on that same day (as-of, never from
later files). Used by fetch.py (on each complete NSE file) and screen.py, so the rule exists once."""

from __future__ import annotations

from datetime import date

DAYS_TO_EXPIRY = (30, 45)  # the agreed entry window, calendar days


def monthly_expiries(listed: set[date]) -> set[date]:
    """The last listed expiry of each calendar month, from one day's complete list (weeklies included). A monthly
    expiry moved earlier for a holiday is still the month's last listed expiry."""
    last: dict[tuple[int, int], date] = {}
    for expiry in listed:
        key = (expiry.year, expiry.month)
        last[key] = max(expiry, last.get(key, expiry))
    return set(last.values())


def eligible_monthly(day: date, monthly: set[date]) -> date | None:
    """The nearest monthly expiry 30-45 calendar days away, or None (never a weekly substitute)."""
    window = [e for e in monthly if DAYS_TO_EXPIRY[0] <= (e - day).days <= DAYS_TO_EXPIRY[1]]
    return min(window) if window else None
