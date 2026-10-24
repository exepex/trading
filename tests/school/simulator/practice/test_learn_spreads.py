"""The spreads are learned from the captures before today only (MS-SIM, 23 Oct): today's 15:00 capture is never asked
for, yesterday's is. A fake reader and a fixed calendar stand in for the Drive stores and the clock."""

from datetime import date

from fno.research_data.calendar import CsvSessionCalendar
from fno.school.constants import ClosureReason
from fno.school.contracts.roads import ROADS
from fno.school.roads.capture import CaptureProblem
from fno.school.simulator.practice import wiring

CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n2026-10-20,holiday,test holiday,https://example.test/circular\n"
)
TODAY = date(2026, 10, 23)  # a Friday: the sessions before it are 13 to 16, 19, 21 and 22 Oct


class AskedReader:
    def __init__(self):
        self.asked: list[tuple[str, date]] = []

    def read(self, road, session):
        self.asked.append((road.code, session))
        raise CaptureProblem(ClosureReason.CAPTURE_MISSING)


def test_today_is_never_asked_for_and_yesterday_is():
    reader = AskedReader()
    wiring.learn_spreads(reader, CALENDAR, TODAY)
    sessions = {session for _, session in reader.asked}
    assert TODAY not in sessions and date(2026, 10, 22) in sessions
    assert min(sessions) == wiring.FIRST_CAPTURE and date(2026, 10, 20) not in sessions


def test_every_road_is_asked_for_every_session_and_each_miss_is_named():
    reader = AskedReader()
    _, skipped = wiring.learn_spreads(reader, CALENDAR, TODAY)
    assert len(reader.asked) == len(ROADS) * len({s for _, s in reader.asked})
    assert len(skipped.reasons) == len(reader.asked) and all(r[1] != TODAY for r in skipped.reasons)
