"""The 20:05 "why" lines (story MS-INS, part e): one line per trade or ticket the instructor classified that session,
its net and its causes in plain words, from the instructor's own causes file. A port for g's evening section, joined
by one line in MS-P1j's wiring. Codes, rupees and words only: never a contract, strike, price or card internal."""

from datetime import date

from ..contracts import Classification
from ..ports import InstructorKind, InstructorStore
from .labels import MODIFIER_WORDS, UNCLASSIFIED, cause_words

LINE = "{driver} {road}{ticket}: net Rs {net:,.0f}; why: {why}{also}{modifier}"
UPDATED = " (updated)"


def why_line(record: Classification) -> str:
    winner = record.winner
    why = cause_words(record.primary, winner) if record.primary else UNCLASSIFIED
    also = f" (also: {', '.join(cause_words(c, winner) for c in record.secondary)})" if record.secondary else ""
    modifier = MODIFIER_WORDS[record.modifier]
    text = LINE.format(driver=record.driver_id, road=record.road, ticket=" ticket" if record.is_ticket else "",
                       net=record.net, why=why, also=also, modifier=f"; {modifier}" if modifier else "")  # fmt: skip
    return text + (UPDATED if record.corrects else "")


class WhyLineSource:
    def __init__(self, store: InstructorStore):
        self.store = store

    def lines(self, session: date) -> tuple[str, ...]:
        return tuple(why_line(r) for r in self.store.read(session, InstructorKind.CAUSES) or ())
