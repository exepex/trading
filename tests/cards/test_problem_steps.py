"""Story T1d: the card names the steps that failed or were refused today, with O1's own rule, read through T2's
run-log reader (criteria 1-5); since T1e the list is the warning's detail, never a status line. Since O1's R2 a failed
decisions step is never read as books (criterion 6)."""

import json
from datetime import datetime
from types import SimpleNamespace

from fno.cards.problem_steps import DETAIL, UNREADABLE, ProblemSteps
from fno.cards.rule_checks import DecisionOutcome, ExecutionOutcome, RunLogReader, failures_path, run_log_path
from fno.cards.ruled_status import REFUSED, RuleChecks, RuledStatus
from fno.constants import (
    CARD_DATA_CHECK_FAILED,
    CARD_HARD_RULE_BREACH,
    STEP_FAILED,
    STEP_NOT_LIVE,
    STEP_OK,
    STEP_REFUSED,
)
from fno.daily import runner
from fno.desk import run_log

from .fakes import FakeRecords
from .test_rule_checks import BEFORE, DAY, HEADER, ON_TIME, TODAY_TIMES, Base, _log

FAILED_SNAPSHOT = {"status": STEP_FAILED, "reason": "raised:NotImplementedError"}
REFUSED_FILLS = {"status": STEP_REFUSED, "reason": "needs snapshot, which failed today"}
C4_TODAY = HEADER + "2026-10-15,book1_rules,o1,playbook,caps,full,{}\n"


def status_reading(files: dict):
    records = FakeRecords(files)
    runs = RunLogReader(records)
    rules = (DecisionOutcome(records, runs, TODAY_TIMES, ("book1_rules", "book2_hybrid")),
             ExecutionOutcome(runs, TODAY_TIMES, lambda d: BEFORE))  # fmt: skip
    return RuledStatus(Base(), RuleChecks(rules), ProblemSteps(runs)).status(DAY)


def status_lines(files: dict) -> tuple[str, ...]:
    return status_reading(files).section.lines


def listed(files: dict) -> str | None:
    """T1e: T1d's step list is now the warning's detail (never a status line), or None with no warning."""
    warning = ProblemSteps(RunLogReader(FakeRecords(files))).warning(DAY)
    return warning and warning.detail


def detail(steps: str) -> str:
    return DETAIL.format(steps=steps)


def no_list(lines) -> bool:
    return not any("Steps with problems" in line for line in lines)


def test_failed_and_refused_steps_are_named_with_their_status_in_run_order():
    log = _log(weather={"status": STEP_OK}, decisions=ON_TIME, snapshot=FAILED_SNAPSHOT, fills=REFUSED_FILLS,
               exits={"status": STEP_OK})  # fmt: skip
    files = {run_log_path(DAY): log}
    assert listed(files) == detail("snapshot (failed), fills (refused)") and no_list(status_lines(files))
    assert "needs snapshot" not in listed(files)  # the reason stays in the step's own alert


def test_no_line_when_every_step_is_ok_or_not_live_or_the_desk_has_not_run():
    log = _log(weather={"status": STEP_OK}, forecasts_v4={"status": STEP_NOT_LIVE}, decisions=ON_TIME)
    assert listed({run_log_path(DAY): log}) is None and no_list(status_lines({run_log_path(DAY): log}))
    assert listed({}) is None and no_list(status_lines({}))


def test_boundaries_one_failed_one_refused_and_an_empty_log():
    """Rule 5: a single failed step, a single refused step, and a run log with no steps at all."""
    one_failed = listed({run_log_path(DAY): _log(decisions=ON_TIME, snapshot=FAILED_SNAPSHOT)})
    one_refused = listed({run_log_path(DAY): _log(decisions=ON_TIME, fills=REFUSED_FILLS)})
    assert one_failed == detail("snapshot (failed)") and one_refused == detail("fills (refused)")
    assert listed({run_log_path(DAY): _log()}) is None


def test_the_run_s_last_line_and_the_card_share_o1_s_one_rule():
    """Criterion 4: one rule, moved not copied: the runner calls `run_log.problem_steps`, and has no rule of its own."""
    assert runner.problem_steps is run_log.problem_steps and not hasattr(runner, "PROBLEMS")
    steps = {"snapshot": {"result": FAILED_SNAPSHOT}, "fills": {"result": REFUSED_FILLS}, "exits": {"result": {}}}
    assert run_log.problem_steps(steps) == [("snapshot", STEP_FAILED), ("fills", STEP_REFUSED)]


def test_the_runner_s_last_line_and_the_card_name_the_same_steps_for_one_log(tmp_path):
    """Test plan 4: the runner's real last line and the card's line, each built from the same run log."""
    results = {"weather": {"status": STEP_OK}, "snapshot": FAILED_SNAPSHOT, "fills": REFUSED_FILLS, "exits": {}}
    log = run_log.RunLog(DAY, tmp_path / "log.json", {name: {"result": r} for name, r in results.items()})
    daily = SimpleNamespace(steps=SimpleNamespace(root=tmp_path), run=lambda day: log)
    parts = SimpleNamespace(start=lambda day: None, busy=lambda: False)
    code, last = runner.DayRunner(daily, parts, waiter=None).run(DAY)
    card = listed({run_log_path(DAY): _log(**results)})
    assert (code, last) == (1, "day done with problems: snapshot, fills")
    assert card == detail("snapshot (failed), fills (refused)")


def test_a_failed_decisions_step_is_a_data_check_failure_never_late_books_status_and_reason():
    """Criterion 6 (judge 567): O1's R2 commits a raised decisions step as {status, reason}."""
    lines = status_lines({run_log_path(DAY): _log(decisions=FAILED_SNAPSHOT)})
    assert f"Status: NO TRADE ({CARD_DATA_CHECK_FAILED})" == lines[0] and REFUSED in lines
    assert "- decisions: decisions step failed: raised:NotImplementedError, no C4 refusal" in lines
    assert not any("late or not committed" in line for line in lines)
    assert listed({run_log_path(DAY): _log(decisions=FAILED_SNAPSHOT)}) == detail("decisions (failed)")


def test_a_decisions_step_with_another_step_level_status_is_shown_as_it_is_never_as_books():
    """Self-review: any step-level `status` (a later desk freeze, say) is never read as book names."""
    lines = status_lines({run_log_path(DAY): _log(decisions={"status": "frozen", "reason": "desk frozen"})})
    assert "- decisions: decisions step frozen: desk frozen, no C4 refusal" in lines
    assert lines[0].endswith("(no_approved_strategy)")


def test_c4_refusals_are_read_on_a_step_level_decisions_result_too():
    """Self-review (both reviewers): a step-level decisions result never hides today's C4 refusal."""
    frozen = {run_log_path(DAY): _log(decisions={"status": "frozen"}), failures_path("book1_rules"): C4_TODAY.encode()}
    failed = {run_log_path(DAY): _log(decisions=FAILED_SNAPSHOT), failures_path("book1_rules"): C4_TODAY.encode()}
    frozen_lines, failed_lines = status_lines(frozen), status_lines(failed)
    assert frozen_lines[0] == f"Status: NO TRADE ({CARD_HARD_RULE_BREACH})"
    assert "- decisions: decisions step frozen, C4 refused: book1_rules (caps)" in frozen_lines
    assert failed_lines[0] == f"Status: NO TRADE ({CARD_DATA_CHECK_FAILED})"
    assert (
        "- decisions: decisions step failed: raised:NotImplementedError, C4 refused: book1_rules (caps)" in failed_lines
    )


def test_a_decisions_status_that_is_not_a_string_is_never_read_as_a_book():
    """Self-review: `{"status": None}` once crashed the card on `"run_id" not in None`."""
    lines = status_lines({run_log_path(DAY): _log(decisions={"status": None})})
    assert "- decisions: decisions step None, no C4 refusal" in lines


def test_a_refused_decisions_step_is_a_data_check_failure_too():
    lines = status_lines({run_log_path(DAY): _log(decisions={"status": STEP_REFUSED, "reason": "needs pack"})})
    assert lines[0] == f"Status: NO TRADE ({CARD_DATA_CHECK_FAILED})"
    assert "- decisions: decisions step refused: needs pack, no C4 refusal" in lines


def test_a_failed_snapshot_fails_closed_with_its_raise_and_is_named_as_failed():
    """T2's execution line is unchanged (story Scope); it carries the step's own reason code, not a C3 check name."""
    files = {run_log_path(DAY): _log(decisions=ON_TIME, snapshot=FAILED_SNAPSHOT)}
    lines = status_lines(files)
    assert lines[0] == f"Status: NO TRADE ({CARD_DATA_CHECK_FAILED})"
    assert "- execution: no valid execution snapshot (raised:NotImplementedError)" in lines
    assert listed(files) == detail("snapshot (failed)")


ODD_STEPS = ([], {"x": "text"}, {"y": {"result": []}}, {"z": {"inputs": {}}})


def test_odd_run_log_shapes_are_unreadable_at_the_reader_never_a_crash():
    """O1's `problem_steps` assumes name -> {"result": {...}}; T2's reader refuses any other shape once, so neither
    O1's rule nor a card rule meets it (the earlier copy of the rule tolerated these shapes itself)."""
    for steps in ODD_STEPS:
        log = json.dumps({"day": DAY.isoformat(), "kind": "daily_run", "steps": steps}).encode()
        files = {run_log_path(DAY): log}
        lines = status_lines(files)
        assert lines[0] == f"Status: NO TRADE ({CARD_DATA_CHECK_FAILED})", steps
        assert any("not readable (steps are not name -> {result: {...}})" in line for line in lines), steps
        warning = ProblemSteps(RunLogReader(FakeRecords(files))).warning(DAY)
        assert warning == UNREADABLE and no_list(lines), steps  # T1e: the doubt is in the headline


def test_the_app_s_card_wires_the_problem_warning():
    """Self-review: dropping `ProblemSteps` from the wiring must fail a test, not silently remove the warning."""
    from fno.cards.committed import GitHeadRecords
    from fno.cards.wiring import build_daily_card, build_status
    from fno.config import ROOT

    assert isinstance(build_status(GitHeadRecords(ROOT), ROOT).problems, ProblemSteps)
    builder = build_daily_card(ROOT).builder
    assert builder.warning_source is builder.status_source.problems  # T1e: the card shows the same findings


def _written_by_run_log(tmp_path, *entries) -> bytes:
    """The run log as O1's `RunLog` writes it (round 2: a failed step carries `retry`; its retry replaces it)."""
    log = run_log.RunLog(DAY, tmp_path / "log.json")
    for name, result in entries:
        log.record(name, datetime(2026, 10, 15, 15, 0), datetime(2026, 10, 15, 15, 1), {}, result)
    return log.path.read_bytes()


def test_a_failed_step_waiting_for_its_retry_is_named_as_failed(tmp_path):
    """O1 round 2: `fills` failed with `retry: true` is not done for the run, and is still a failed step today."""
    failed_fills = {"status": STEP_FAILED, "reason": "OSError: disk", run_log.RETRY: True}
    final_decisions = {"status": STEP_FAILED, "reason": "raised:KeyError", run_log.RETRY: False}
    data = _written_by_run_log(tmp_path, ("decisions", final_decisions), ("fills", failed_fills))
    lines = status_lines({run_log_path(DAY): data})
    assert listed({run_log_path(DAY): data}) == detail("decisions (failed), fills (failed)")
    assert "- decisions: decisions step failed: raised:KeyError, no C4 refusal" in lines


def test_a_step_retried_and_then_ok_is_no_longer_named(tmp_path):
    """The retry's entry replaces the failed one (it moves last, in the order the steps ran): no problem remains."""
    failed_fills = {"status": STEP_FAILED, "reason": "OSError: disk", run_log.RETRY: True}
    data = _written_by_run_log(tmp_path, ("decisions", ON_TIME), ("fills", failed_fills), ("exits", {}),
                               ("fills", {"t1": {"outcome": "filled"}}))  # fmt: skip
    assert list(json.loads(data)["steps"]) == ["decisions", "exits", "fills"]
    assert listed({run_log_path(DAY): data}) is None
