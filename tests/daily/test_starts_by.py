"""MS-P1j2: `StartsBy`, the school step's last start (15:25 IST on its own day); ending is never checked."""

from datetime import UTC, date, datetime, time

import pytest

from fno.constants import STEP_OK, STEP_REFUSED
from fno.daily.steps import StartsBy
from fno.desk.daily_steps import StepOutcome
from fno.models import IST

DAY = date(2026, 10, 26)
BY = time(15, 25)


class Counted:
    def __init__(self):
        self.runs = []

    def run(self, day):
        self.runs.append(day)
        return StepOutcome({}, {"status": STEP_OK, "reason": "ran"})


def guarded(now: datetime) -> tuple[StartsBy, Counted]:
    step = Counted()
    return StartsBy(step, BY, lambda: now), step


@pytest.mark.parametrize("at", [time(15, 0), time(15, 24, 59), time(15, 25)])
def test_a_start_at_or_before_its_last_start_runs_the_step(at):
    starts_by, step = guarded(datetime.combine(DAY, at, IST))
    assert starts_by.run(DAY).result == {"status": STEP_OK, "reason": "ran"} and step.runs == [DAY]


@pytest.mark.parametrize("now", [datetime.combine(DAY, time(15, 25, 0, 1), IST),
                                 datetime.combine(DAY, time(15, 45), IST),
                                 datetime(2026, 10, 27, 9, 0, tzinfo=IST)])  # fmt: skip
def test_a_later_start_or_a_past_day_s_run_is_refused_and_the_step_never_runs(now):
    starts_by, step = guarded(now)
    done = starts_by.run(DAY)
    assert done.result["status"] == STEP_REFUSED and step.runs == []
    assert done.result["reason"].startswith("not started: ") and "after its last start, 15:25 IST on 2026-10-26" in (
        done.result["reason"])  # fmt: skip


def test_a_utc_clock_is_compared_in_ist():
    """09:55 UTC is 15:25 IST: the last start itself; one minute later is late."""
    assert guarded(datetime(2026, 10, 26, 9, 55, tzinfo=UTC))[0].run(DAY).result["status"] == STEP_OK
    assert guarded(datetime(2026, 10, 26, 9, 56, tzinfo=UTC))[0].run(DAY).result["status"] == STEP_REFUSED
