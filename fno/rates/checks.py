"""The rates capture's checks (story A21): staleness and the home page against the auction release, with the grace
rule of judge 355 SF3. Each returns one named problem, or None when clean."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from .constants import GRACE_HOURS, STALE_AUCTION_DAYS, STALE_HOME_HOURS, TBILL_91
from .rows import RateRow

STALE_AUCTION = "stale: the latest 91-day T-bill auction is {day} ({days} days before {today}; limit {limit})"
STALE_HOME = "stale: RBI's home page was last read at {at} ({hours:.1f} hours before this run; limit {limit})"
DISAGREE = "disagreement: the home page shows 91-day {home:.4f}% but the auction release {release} says {value:.4f}%"


def stale_auction(rows: list[RateRow], today: date) -> str | None:
    days = sorted({date.fromisoformat(r.value_date) for r in rows if r.rate == TBILL_91})
    if not days:
        return None  # a first run has nothing to be stale against
    gap = (today - days[-1]).days
    if gap <= STALE_AUCTION_DAYS:
        return None
    return STALE_AUCTION.format(day=days[-1], days=gap, today=today, limit=STALE_AUCTION_DAYS)


def stale_home(last_read: datetime | None, now: datetime) -> str | None:
    if last_read is None:
        return None
    age = now - last_read
    if age <= timedelta(hours=STALE_HOME_HOURS):
        return None
    return STALE_HOME.format(at=last_read.isoformat(), hours=age.total_seconds() / 3600, limit=f"{STALE_HOME_HOURS} h")


def disagreement(rows: list[RateRow], home_91: float, now: datetime) -> str | None:
    """The home page must show the newest release's 91-day yield, or, while the newest release is under 24 hours
    old, the one before it."""
    releases = sorted((r for r in rows if r.rate == TBILL_91), key=lambda r: (r.value_date, r.seen_at), reverse=True)
    if not releases:
        return None
    accepted = [releases[0]]
    if now - releases[0].seen_at < timedelta(hours=GRACE_HOURS) and len(releases) > 1:
        accepted.append(releases[1])
    if any(abs(r.value - home_91) < 5e-5 for r in accepted):
        return None
    return DISAGREE.format(home=home_91, release=releases[0].release_no, value=releases[0].value)
