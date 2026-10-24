"""DRY2 SF1: `RunLog.done` never counts a failed entry marked for a retry, and `record` replaces such an entry, and only
such an entry: a finished step, a refused one and one failed for good (an O1 command step, a step not safe to repeat)
are never replaced."""

from datetime import date, datetime

import pytest

from fno.constants import STEP_FAILED, STEP_OK, STEP_REFUSED
from fno.desk.run_log import RETRY, RunLog
from fno.health.desk_checks import _problems
from fno.models import IST

DAY = date(2026, 10, 23)
AT = datetime(2026, 10, 23, 15, 15, tzinfo=IST)
RETRIED = {"status": STEP_FAILED, "reason": "TimeoutError: planted", RETRY: True}
FINAL = [
    {"line": "Book 1 version v1 unchanged"},  # finished
    {"status": STEP_OK, "reason": "command:ok"},
    {"status": STEP_REFUSED, "reason": "needs snapshot, which failed today"},
    {"status": STEP_FAILED, "reason": "command:exit_1"},  # an O1 command step's failure (`Alerted`): no retry key
    {"status": STEP_FAILED, "reason": "KeyError: 'planted'", RETRY: False},  # not safe to repeat
    {"status": STEP_OK, RETRY: True},  # the key alone never reopens a step that did not fail
]


def logged(root, name, result):
    log = RunLog.open(root, DAY)
    log.record("pack", AT, AT, {}, {"built": True})
    log.record(name, AT, AT, {}, result)
    return RunLog.open(root, DAY)


def test_a_failed_entry_marked_for_a_retry_is_not_done_and_a_rerun_replaces_it(tmp_path):
    log = logged(tmp_path, "exits", RETRIED)
    assert not log.done("exits") and "exits" in log.steps
    log.record("exits", AT, AT, {}, dict(RETRIED))  # failing again: replaced, still open for a retry
    assert not RunLog.open(tmp_path, DAY).done("exits")
    log.record("exits", AT, AT, {}, {"book": {"reviewed": True}})
    again = RunLog.open(tmp_path, DAY)
    assert again.done("exits") and again.result("exits") == {"book": {"reviewed": True}}
    assert list(again.steps) == ["pack", "exits"]


@pytest.mark.parametrize("result", FINAL)
def test_a_finished_refused_or_finally_failed_entry_is_done_and_never_replaced(tmp_path, result):
    log = logged(tmp_path, "exits", result)
    assert log.done("exits")
    with pytest.raises(ValueError, match="never repeats a step"):
        log.record("exits", AT, AT, {}, {"book": {"reviewed": True}})
    assert RunLog.open(tmp_path, DAY).result("exits") == result


def test_the_health_check_names_a_step_awaiting_its_retry_failed_not_missing(tmp_path):
    problems = _problems(logged(tmp_path, "exits", RETRIED))
    not_run, not_ok = problems.split("; steps not ok: ")
    assert "exits" not in not_run.removeprefix("steps not run: ").split(", ") and not_ok.startswith("exits failed")
