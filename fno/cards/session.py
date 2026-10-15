"""Which days get a card (story T1 criterion 14): only the NSE session calendar (A7) decides, read as committed. A day
the calendar cannot answer (a year not yet in it) still gets a card that names the gap: a card on a holiday costs
nothing, a missing card on a session breaks the card's contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..research_data.calendar import CalendarError, CsvSessionCalendar
from .committed import CommittedRecords
from .sections import CardSection, UsedRecord

CALENDAR_PATH = "research/data/calendar/nse_sessions.csv"
SESSION_NOTE = "NSE {kind} session"
UNKNOWN_NOTE = "session unknown: calendar cannot answer"


@dataclass(frozen=True)
class SessionAnswer:
    is_session: bool
    note: str
    context: CardSection  # the calendar record used, or what is missing
    previous: date | None  # the session before, whose card the next card checks


class SessionCheck:
    def __init__(self, records: CommittedRecords):
        self.records = records

    def answer(self, day: date) -> SessionAnswer:
        data = self.records.read(CALENDAR_PATH)
        if data is None:
            return _unknown(f"{CALENDAR_PATH} not committed", ())
        used = (UsedRecord.of(CALENDAR_PATH, data),)
        try:
            calendar = CsvSessionCalendar(data.decode("utf-8"))
            kind = calendar.session_kind(day)
        except (CalendarError, UnicodeDecodeError) as error:
            return _unknown(f"session calendar cannot answer for {day} ({type(error).__name__})", used)
        try:
            previous = calendar.previous_session(day)
        except CalendarError:
            previous = None
        context = CardSection("session", (), used)
        return SessionAnswer(kind is not None, SESSION_NOTE.format(kind=kind), context, previous)


def _unknown(why: str, used: tuple[UsedRecord, ...]) -> SessionAnswer:
    return SessionAnswer(True, UNKNOWN_NOTE, CardSection("session", (), used, (why,)), None)
