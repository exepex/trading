"""Part b on part a's one correction resolver (orchestrator, after judge 501): a trade corrected on a later session is
attributed once, as its correction, on its original close day, and nothing on the correction's own day."""

from fno.school.instructor.attribution.attribute import attribute
from tests.school.instructor.builders import RULES, SESSIONS
from tests.school.instructor.test_reader import LATER, WriteRefusingDashcam, correct_later, held_trade, reader


def test_a_corrected_trade_is_attributed_once_on_its_original_day():
    dashcam = WriteRefusingDashcam()
    fixed = correct_later(dashcam, held_trade(dashcam))
    read = reader(dashcam)
    days = read.calendar.sessions(SESSIONS[0], LATER)
    attributed = [(day, attribute(p, 0.0, RULES)) for day in days for p in read.closed_on(day).paths]
    assert [(day, a.net) for day, a in attributed] == [(SESSIONS[2], fixed.net)]
    assert attributed[0][1].closed_on == SESSIONS[2]
