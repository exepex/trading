"""Results events (PROTOCOL.md section 4, amendment 1 sections D1-D2): meetings, filings, entry and reaction."""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .rules import DUPLICATE_MEETING_DAYS, FILING_SEARCH_DAYS, RESULTS_PURPOSE
from .sessions import Sessions, filed_before_entry_close, reaction_session

DUPLICATE, FILED_BEFORE_ENTRY, NOT_FO = "duplicate meeting", "filing before entry", "not F&O on the entry session"
NO_ENTRY, NO_REACTION = "no entry session in the archive", "no reaction session in the archive yet"


@dataclass(frozen=True)
class Meeting:
    symbol: str
    day: date  # D, the board-meeting date
    text: str  # purpose and description


@dataclass(frozen=True)
class Event:
    symbol: str
    results_day: date  # D
    entry: date
    reaction: date  # R
    filed_at: datetime | None


def is_results_meeting(meeting: Meeting) -> bool:
    return RESULTS_PURPOSE in meeting.text.lower()


class Filings:
    """Results filing times per stock (IST, timezone-naive), sorted."""

    def __init__(self, times: dict[str, list[datetime]]):
        self.times = {s: sorted(ts) for s, ts in times.items()}

    def first(self, symbol: str, start: date, end: date) -> datetime | None:
        """The earliest filing of a stock on a day from `start` to `end`, both included."""
        times = self.times.get(symbol, [])
        i = bisect_left(times, datetime.combine(start, datetime.min.time()))
        return times[i] if i < len(times) and times[i].date() <= end else None


def search_end(meeting: Meeting) -> date:
    return meeting.day + timedelta(days=FILING_SEARCH_DAYS)


def one_per_reschedule(meetings: list[Meeting], has_filing) -> tuple[list[Meeting], int]:
    """One stock's results meetings, sorted: meetings fewer than DUPLICATE_MEETING_DAYS apart form one group; the
    group keeps its latest meeting with a matched filing, else its latest meeting. Returns (kept, dropped)."""
    kept, group = [], []
    for meeting in sorted(set(meetings), key=lambda m: m.day):
        if group and (meeting.day - group[-1].day).days >= DUPLICATE_MEETING_DAYS:
            kept.append(_pick(group, has_filing))
            group = []
        group.append(meeting)
    if group:
        kept.append(_pick(group, has_filing))
    return kept, len(set(meetings)) - len(kept)


def _pick(group: list[Meeting], has_filing) -> Meeting:
    filed = [m for m in group if has_filing(m)]
    return (filed or group)[-1]


def build_events(meetings: list[Meeting], filings: Filings, sessions: Sessions, is_fo) -> tuple[list[Event], Counter]:
    """Events of F&O stocks (`is_fo(symbol, day)` on the entry session), with the counts of what was left out."""
    counts: Counter = Counter()
    by_stock: dict[str, list[Meeting]] = defaultdict(list)
    for meeting in meetings:
        if is_results_meeting(meeting):
            by_stock[meeting.symbol].append(meeting)
    events = []
    for symbol, own in by_stock.items():

        def has_filing(m: Meeting, symbol=symbol) -> bool:
            entry = sessions.before(m.day)
            return entry is not None and filings.first(symbol, entry, search_end(m)) is not None

        kept, dropped = one_per_reschedule(own, has_filing)
        counts[DUPLICATE] += dropped
        for meeting in kept:
            event = _event(meeting, filings, sessions, is_fo, counts)
            if event is not None:
                events.append(event)
    return sorted(events, key=lambda e: (e.reaction, e.symbol)), counts


def _event(meeting: Meeting, filings: Filings, sessions: Sessions, is_fo, counts: Counter) -> Event | None:
    entry = sessions.before(meeting.day)
    if entry is None:
        counts[NO_ENTRY] += 1
        return None
    if not is_fo(meeting.symbol, entry):
        counts[NOT_FO] += 1
        return None
    filed_at = filings.first(meeting.symbol, entry, search_end(meeting))
    if filed_before_entry_close(filed_at, entry):
        counts[FILED_BEFORE_ENTRY] += 1
        return None
    reaction = reaction_session(sessions, meeting.day, filed_at)
    if reaction is None:
        counts[NO_REACTION] += 1
        return None
    return Event(meeting.symbol, meeting.day, entry, reaction, filed_at)
