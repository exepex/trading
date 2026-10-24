"""Story G11 criterion C8: BG1's budget stop, AI forecasters last. Good: `alert` fires. Bad: `stop` with the books'
own minutes at the cap is `not_fired` (a miss). Boundary: the books at 99.9% of the cap fire (the other roles stop
first). Empty: no BG1 reading fires the books with one #fno-desk line (fail open). The reading is BG1's own meter."""

from datetime import date
from types import SimpleNamespace

import pytest

from fno.ai.budget_stop import MeterBudgetStop
from fno.budget.constants import BUDGET_ALERT, BUDGET_OK, BUDGET_STOP, BUDGET_UNKNOWN
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from tests.ai.test_v4_fire import DAY, Desk

CAP = 100.0


def meter(level, book_minutes, role_minutes=40.0):
    rows = [{"book": BOOK2_HYBRID, "minutes": f"{book_minutes / 2:.2f}"},
            {"book": BOOK3_AI, "minutes": f"{book_minutes / 2:.2f}"},
            {"book": "", "minutes": f"{role_minutes:.2f}"}]  # fmt: skip
    return lambda month, today: SimpleNamespace(usage_rows=rows, cap=SimpleNamespace(level=level, cap_minutes=CAP))


@pytest.mark.parametrize(
    ("level", "books", "stopped"),
    [(BUDGET_ALERT, 120.0, False), (BUDGET_OK, 10.0, False), (BUDGET_UNKNOWN, 500.0, False),
     (BUDGET_STOP, 100.0, True), (BUDGET_STOP, 99.9, False)],
)  # fmt: skip
def test_the_books_stop_only_when_their_own_minutes_reach_the_cap_at_stop(level, books, stopped):
    check = MeterBudgetStop(meter(level, books)).check(DAY)
    assert bool(check.stop) is stopped and check.note == ""
    if stopped:
        assert check.stop.startswith("BG1 stop: 2026-10's level is stop and the books alone used 100.00 of 100.00")


def test_a_meter_that_cannot_be_read_fires_with_one_line():
    def broken(month, today):
        raise OSError("accounting/ai_usage.csv: unreadable")

    check = MeterBudgetStop(broken).check(date(2026, 11, 2))
    assert check.stop == "" and check.note.startswith("no BG1 reading for 2026-11 (accounting/ai_usage.csv")


class Fixed:
    def __init__(self, check):
        self.value = check

    def check(self, day):
        return self.value


def test_the_firer_writes_a_budget_stop_as_not_fired_and_fires_nothing(tmp_path):
    desk = Desk(tmp_path)
    desk.firer.budget = MeterBudgetStop(meter(BUDGET_STOP, 150.0))
    desk.firer.fire(DAY)
    entry = desk.log()["books"][BOOK3_AI]
    assert (entry["fired"], entry["budget_stop"]) == (False, True) and entry["reason"].startswith("BG1 stop")
    assert not desk.triggers[BOOK3_AI].fired and not desk.triggers[BOOK2_HYBRID].fired


def test_the_firer_fires_on_a_failed_reading_and_says_so_once(tmp_path):
    def broken(month, today):
        raise ValueError("budget missing in config.yaml")

    desk = Desk(tmp_path)
    desk.firer.budget = MeterBudgetStop(broken)
    desk.firer.fire(DAY)
    assert desk.triggers[BOOK3_AI].fired and desk.triggers[BOOK2_HYBRID].fired
    assert [line for line in desk.alerts.lines if "no BG1 reading" in line] == [desk.alerts.lines[0]]


def test_the_wiring_reads_bg1s_own_meter():
    from fno.ai.wiring import build_v4_firer
    from fno.budget.wiring import build_month_meter

    firer = build_v4_firer({})
    assert isinstance(firer.budget, MeterBudgetStop) and firer.budget.meter is build_month_meter
