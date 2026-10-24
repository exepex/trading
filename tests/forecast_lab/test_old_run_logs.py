"""FL1-1d, the O1 builder's condition 2: O1's `lab_close` step is removed, and a run log that still names it (a run
from before the removal) breaks no reader. Readers that look a step up by name (the scoreboard's runs, the card's
rule checks, the desk's earlier-day checks) never ask for it; the readers that loop over a log's steps (O8's health
check, the day runner's problem list) count only failed or refused results, and an old entry was `not_live` (the step
never went live). No committed log names it today (journal/runs/ checked on 22 Oct); this test pins the behaviour."""

import json
from datetime import time

import pytest

from fno.constants import DAILY_RUN_STEPS, HEALTH_OK, STEP_NOT_LIVE, STEP_OK
from fno.desk.run_log import RUNS_FOLDER
from fno.health.desk_checks import RunLogCheck
from fno.health.model import Deadline
from tests.health.fakes import DAY, Repo, ist

AT = ist(DAY, 15, 12)


def _log(repo, old_status):
    def body(status):
        return {"started_at": AT.isoformat(), "finished_at": AT.isoformat(), "inputs": {}, "result": {"status": status}}

    steps = {s: body(STEP_OK) for s in DAILY_RUN_STEPS} | {"lab_close": body(old_status)}
    repo.write_json(f"journal/{RUNS_FOLDER}/{DAY.isoformat()}.json", {"day": DAY.isoformat(), "kind": "daily_run",
                                                                       "steps": steps})  # fmt: skip


@pytest.mark.parametrize("old_status", [STEP_NOT_LIVE, STEP_OK])
def test_an_old_lab_close_entry_is_neither_missing_nor_a_problem(tmp_path, old_status):
    repo = Repo(tmp_path)
    _log(repo, old_status)
    result = RunLogCheck(repo.root, Deadline(time(15, 12))).check(DAY, ist(DAY, 17, 51))
    assert "lab_close" not in DAILY_RUN_STEPS and result.status == HEALTH_OK
    assert "lab_close" not in result.detail


def test_no_committed_run_log_names_the_removed_step():
    from fno.config import ROOT

    logs = sorted((ROOT / "journal" / RUNS_FOLDER).glob("*.json"))
    assert all("lab_close" not in json.loads(p.read_text(encoding="utf-8"))["steps"] for p in logs)
