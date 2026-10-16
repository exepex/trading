"""Story O8 criterion 2 for the desk run (in-file `decisions` finish), A16's marks (its own per-mark status, counted)
and the evening data jobs (push receipt of the commit that first added the session's row)."""

import json
from datetime import time, timedelta

import pytest

from fno.constants import HEALTH_LATE, HEALTH_MISSED, HEALTH_NOT_DUE, HEALTH_NOT_EXPECTED, HEALTH_OK
from fno.desk.run_log import RUNS_FOLDER
from fno.health.data_checks import PanelDayCheck, SessionRowCheck
from fno.health.desk_checks import DESK_RUN_STEPS, MarksCheck, RunLogCheck
from fno.health.expectations import CLOSES_FILE, FLOWS_BY, INDEX_CLOSE_BY, PANEL_DAY_BY, PANEL_MANIFEST
from fno.health.model import Deadline
from fno.intraday.slots import MARKS_PER_SESSION

from .fakes import DAY, Repo, ist

EVENING = ist(DAY, 17, 51)
DESK_DEADLINE = Deadline(time(15, 12))
AT_DEADLINE = ist(DAY, 15, 12)


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


def _run_log(repo, steps=DESK_RUN_STEPS, decided=AT_DEADLINE):
    body = {"started_at": decided.isoformat(), "finished_at": decided.isoformat(), "inputs": {}, "result": {}}
    repo.write_json(f"journal/{RUNS_FOLDER}/{DAY.isoformat()}.json",
                    {"day": DAY.isoformat(), "kind": "daily_run", "steps": {s: body for s in steps}})  # fmt: skip


@pytest.mark.parametrize(("decided", "status"), [(ist(DAY, 15, 12), HEALTH_OK), (ist(DAY, 15, 12, 1), HEALTH_LATE)])
def test_the_desk_run_is_on_time_by_its_decisions_finish(repo, decided, status):
    _run_log(repo, decided=decided)
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == status


@pytest.mark.parametrize("missing", ["exits", "trade_marks"])  # story E2d: the marking step after the exits
def test_a_run_log_missing_a_step_is_a_miss_naming_it(repo, missing):
    _run_log(repo, steps=tuple(step for step in DESK_RUN_STEPS if step != missing))
    result = RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and missing in result.detail


def test_a_run_log_without_decisions_and_no_run_log_at_all(repo):
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).detail.startswith("never ran")
    _run_log(repo, steps=("versions", "pack"))
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, ist(DAY, 15, 0)).status == HEALTH_NOT_DUE
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == HEALTH_MISSED


def test_a_skipped_run_is_not_expected(repo):
    _run_log(repo, steps=("skipped",))
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == HEALTH_NOT_EXPECTED


def test_the_desk_steps_are_the_daily_runs_own_in_order():
    import re

    from fno.config import ROOT

    source = (ROOT / "fno/desk/daily_run.py").read_text(encoding="utf-8")
    plan = source[source.index("plan = (") : source.index("for name, moment, action in plan")]
    names = [m.group(1) or "decisions" for m in re.finditer(r'\(\s*(?:"(\w+)"|RUN_LOG_DECISIONS_STEP),', plan)]
    assert tuple(names) == DESK_RUN_STEPS


def _marks(repo, statuses):
    for i, status in enumerate(statuses):
        mark = ist(DAY, 9, 15) + timedelta(minutes=15 * i)
        repo.write(f"research/data/intraday/slots/2026/10/15/nifty_20261015_{mark:%H%M}.csv",
                   f"session,mark,status\n{DAY},{mark.isoformat()},{status}\n")  # fmt: skip


@pytest.mark.parametrize(
    ("statuses", "status"),
    [
        (["good"] * MARKS_PER_SESSION, HEALTH_OK),
        (["good"] * (MARKS_PER_SESSION - 1) + ["late"], HEALTH_LATE),
        (["good"] * (MARKS_PER_SESSION - 1) + ["missed"], HEALTH_MISSED),
        (["good"] * (MARKS_PER_SESSION - 1), HEALTH_MISSED),  # 25 of 26: one never written
    ],
)
def test_a16_marks_are_counted_by_their_own_status(repo, statuses, status):
    _marks(repo, statuses)
    result = MarksCheck(repo.root / "research/data/intraday").check(DAY, EVENING)
    assert result.status == status and f"of {MARKS_PER_SESSION} good" in result.detail


def test_no_marks_is_not_due_before_the_last_mark_and_missed_after(repo):
    check = MarksCheck(repo.root / "research/data/intraday")
    assert check.check(DAY, ist(DAY, 15, 29)).status == HEALTH_NOT_DUE
    assert check.check(DAY, ist(DAY, 15, 31)).status == HEALTH_MISSED


@pytest.mark.parametrize(("deadline", "on_time", "late"), [
    (INDEX_CLOSE_BY, ist(DAY + timedelta(1), 12, 0), ist(DAY + timedelta(1), 12, 0, 1)),
    (FLOWS_BY, ist(DAY + timedelta(1), 12, 0), ist(DAY + timedelta(1), 12, 0, 1)),
])  # fmt: skip
def test_a_session_row_is_on_time_by_the_push_that_first_added_it(repo, deadline, on_time, late):
    repo.write(CLOSES_FILE, f"date,close\n2026-10-14,1\n{DAY},2\n")
    check = SessionRowCheck(repo.evidence, CLOSES_FILE, deadline)
    repo.receipts.row(CLOSES_FILE, f"{DAY},", on_time)
    assert check.check(DAY, ist(DAY + timedelta(2), 17, 51)).status == HEALTH_OK
    repo.receipts.row(CLOSES_FILE, f"{DAY},", late)
    assert check.check(DAY, ist(DAY + timedelta(2), 17, 51)).status == HEALTH_LATE


def test_a_missing_row_is_not_due_until_its_deadline_then_missed(repo):
    repo.write(CLOSES_FILE, "date,close\n2026-10-14,1\n")
    check = SessionRowCheck(repo.evidence, CLOSES_FILE, INDEX_CLOSE_BY)
    assert check.check(DAY, EVENING).status == HEALTH_NOT_DUE  # an evening job at 17:51
    assert check.check(DAY, ist(DAY + timedelta(1), 12, 0, 1)).status == HEALTH_MISSED


def test_a_panel_day_needs_status_ok_and_its_push(repo):
    repo.write(PANEL_MANIFEST, json.dumps({"days": {DAY.isoformat(): {"status": "ok"}}}, indent=1))
    repo.receipts.row(PANEL_MANIFEST, f'"{DAY.isoformat()}": {{', ist(DAY + timedelta(1), 1, 40))
    assert PanelDayCheck(repo.evidence, PANEL_MANIFEST, PANEL_DAY_BY).check(DAY, EVENING).status == HEALTH_OK
    repo.write(PANEL_MANIFEST, json.dumps({"days": {DAY.isoformat(): {"status": "failed"}}}, indent=1))
    result = PanelDayCheck(repo.evidence, PANEL_MANIFEST, PANEL_DAY_BY).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and "failed" in result.detail
