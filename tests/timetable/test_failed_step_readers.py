"""DRY2 R2, judge 567: a failed or refused step's committed result is exactly `{"status", "reason"}`. Every reader of
a per-book step (the decisions, the exits) reads it through `book_results`, so the failure's own fields are never
taken for books; `problem_steps` is the one rule naming the failed steps. A step whose input step has not run is
refused too (fail closed)."""

import json
from datetime import date, datetime

from fno.constants import BOOK1_RULES, JOURNAL_FOLDER, STEP_FAILED, STEP_OK, STEP_REFUSED
from fno.desk.daily_run import NEEDS_MISSING, DailyRun
from fno.desk.run_log import RUNS_FOLDER, RunLog, book_results, problem_steps
from fno.models import IST
from fno.scoreboard.committed_runs import NOT_REVIEWED, CommittedRuns

DAY = date(2026, 10, 23)
FAILED = {"status": STEP_FAILED, "reason": "NotImplementedError: planted"}


def step(result):
    at = datetime(2026, 10, 23, 15, 12, tzinfo=IST).isoformat()
    return {"started_at": at, "finished_at": at, "inputs": {}, "result": result}


def logged(root, steps):
    path = root / JOURNAL_FOLDER / RUNS_FOLDER / f"{DAY}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"day": DAY.isoformat(), "kind": "daily_run", "steps": steps}))
    return RunLog.open(root, DAY)


def test_problem_steps_names_each_failed_or_refused_step_in_run_order():
    steps = {"quotes": step({"status": STEP_OK}), "snapshot": step(FAILED),
             "fills": step({"status": STEP_REFUSED, "reason": "needs snapshot, which failed today"})}  # fmt: skip
    assert problem_steps(steps) == [("snapshot", STEP_FAILED), ("fills", STEP_REFUSED)]


def test_book_results_never_reads_a_failure_s_fields_as_books():
    assert book_results(FAILED) == {} and book_results({BOOK1_RULES: {"run_id": "r1"}}) == {
        BOOK1_RULES: {"run_id": "r1"}
    }


def test_the_scoreboard_reads_a_failed_decisions_and_exits_step_as_no_run_and_no_review(tmp_path):
    logged(tmp_path, {"decisions": step(FAILED), "snapshot": step(FAILED), "exits": step(FAILED)})
    runs = CommittedRuns(tmp_path)
    assert runs.runs() == [] and runs.uncollected([BOOK1_RULES]) == {BOOK1_RULES: []}  # was AttributeError
    missed = runs.missed_runs(BOOK1_RULES, [date(2026, 10, 22), DAY], lambda day: True)  # 22 Oct has no log either
    assert missed[-1] == {"day": DAY.isoformat(), "missed_decision": True, "missed_exit_review": True,
                          "exit_review": NOT_REVIEWED}  # fmt: skip


def test_a_step_whose_input_step_has_not_run_is_refused(tmp_path):
    log = logged(tmp_path, {"decisions": step({BOOK1_RULES: {"run_id": "r1"}})})
    refused = DailyRun._refused(None, log, "fills")
    assert refused.result == {"status": STEP_REFUSED, "reason": NEEDS_MISSING.format(needed="snapshot")}
