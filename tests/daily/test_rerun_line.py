"""Owner, 24 Oct ("2 - yes"): the run's last line tells the routine when a rerun at once retries a failed step, because
a Slack alert that was sent is never printed. Only a step marked `retry`, and only on the run's own day."""

from datetime import timedelta

import pytest

from fno.daily.runner import RETRIES, WITH_PROBLEMS
from tests.timetable.test_daily_run import NORMAL

from .test_day_run import day  # noqa: F401 - the day's run fixture


def raising(*_):
    raise TimeoutError("planted: the Drive read timed out")


def test_a_failed_exits_step_ends_the_line_with_the_rerun_that_retries_it(day):  # noqa: F811
    runner, run, clock, *_ = day()
    run.steps.review_exits = raising
    code, line = runner.run(NORMAL)
    assert (code, line) == (1, WITH_PROBLEMS.format(steps="exits") + RETRIES.format(steps="exits"))
    assert runner.run(NORMAL)[1].endswith(RETRIES.format(steps="exits"))  # the rerun: retried, failing again
    clock.now += timedelta(days=1)
    assert runner.run(NORMAL)[1] == WITH_PROBLEMS.format(steps="exits")  # a later day's run retries nothing


def test_a_failed_fills_step_never_asks_for_a_rerun(day):  # noqa: F811
    runner, run, *_ = day()
    run.steps.fill = raising
    code, line = runner.run(NORMAL)
    assert (code, line) == (1, WITH_PROBLEMS.format(steps="fills"))
    run.steps.fill = lambda *_: pytest.fail("a failed fills step was retried")
    assert runner.run(NORMAL) == (1, line)
