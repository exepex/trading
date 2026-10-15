"""T2: the card reports C3's and C4's committed outcomes, never re-checks them, and says "not yet decided" until the
desk has recorded each step (final times from the desk's own timetable)."""

import ast
import json
from datetime import date, time

import pytest

from fno.cards.rule_checks import DecisionOutcome, ExecutionOutcome, RunLogReader, failures_path, run_log_path
from fno.cards.ruled_status import NO_BREACH, NOT_COMPLETE, REFUSED, RuleChecks, RuledStatus
from fno.cards.sections import CardSection, StatusReading, StatusSource
from fno.config import ROOT
from fno.constants import CardStatus
from fno.desk.timetable import Timetable
from tests.import_graph import full_imports, refused

from .fakes import FakeRecords

DAY, BEFORE = date(2026, 10, 15), date(2026, 10, 14)
TODAY_TIMES = Timetable(time(14, 58), time(15, 10), time(15, 12), time(15, 15), time(15, 20), 60)
G10_TIMES = Timetable(time(14, 32), time(15, 0), time(15, 10), time(15, 15), time(15, 20), 60)
HEADER = "day,book,opportunity_id,mode,check,reason,numbers\n"


def _log(**steps) -> bytes:
    return json.dumps({"day": DAY.isoformat(), "kind": "daily_run", "steps": {
        name: {"started_at": "", "finished_at": "", "inputs": {}, "result": result} for name, result in steps.items()
    }}).encode()  # fmt: skip


ON_TIME = {"book1_rules": {"run_id": "r1", "commit": "c", "committed_at": ""},
           "book2_hybrid": {"decision": "no_decision_late", "reason": "nothing visible at the deadline"}}  # fmt: skip


class Base(StatusSource):
    def status(self, day):
        lines = ("Status: NO TRADE (no_approved_strategy)", "Reason: no strategy has passed", "Paper trades so far: 0")
        return StatusReading(CardStatus.NO_TRADE, "no_approved_strategy", CardSection("status", lines))


def _status(files: dict, times: Timetable = TODAY_TIMES) -> StatusReading:
    records = FakeRecords(files)
    runs = RunLogReader(records)
    rules = (DecisionOutcome(records, runs, times, ("book1_rules", "book2_hybrid")),
             ExecutionOutcome(runs, times, lambda d: BEFORE))  # fmt: skip
    return RuledStatus(Base(), RuleChecks(rules)).status(DAY)


def test_no_run_log_is_not_yet_decided_never_no_breach():
    reading = _status({})
    assert reading.reason_code == "no_approved_strategy" and NOT_COMPLETE in reading.section.lines
    assert "- decisions: not yet decided: the desk has not run today" in reading.section.lines


def test_before_the_steps_each_outcome_names_its_final_time_from_the_timetable():
    files = {
        run_log_path(DAY): _log(versions={}, pack={"built": True}),
        run_log_path(BEFORE): _log(snapshot={"valid": False, "reason": "no new risk: no valid snapshot"}),
    }
    lines = _status(files).section.lines
    assert "- decisions: not yet decided (final at 15:12 IST)" in lines
    assert ("- execution: not yet decided (final at 15:15 IST); last session (2026-10-14): no valid execution "
            "snapshot (no new risk: no valid snapshot)") in lines  # fmt: skip
    assert "- decisions: not yet decided (final at 15:10 IST)" in _status(files, G10_TIMES).section.lines


def test_a_c4_row_of_the_day_is_a_hard_rule_breach_and_other_days_are_ignored():
    rows = (
        HEADER
        + "2026-10-15,book1_rules,o1,playbook,margin_room,short,{}\n2026-10-14,book1_rules,o0,playbook,caps,x,{}\n"
    )
    files = {run_log_path(DAY): _log(decisions=ON_TIME), failures_path("book1_rules"): rows.encode()}
    reading = _status(files)
    assert (
        reading.reason_code == "hard_rule_breach" and reading.section.lines[0] == "Status: NO TRADE (hard_rule_breach)"
    )
    assert REFUSED in reading.section.lines
    assert ("- decisions: late or not committed: book2_hybrid, C4 refused: book1_rules (margin_room)"
            in reading.section.lines)  # fmt: skip
    assert any(u.path == failures_path("book1_rules") for u in reading.section.used)  # in the card's footer


def test_an_invalid_execution_snapshot_is_data_check_failed_and_wins_over_a_breach():
    rows = HEADER + "2026-10-15,book1_rules,o1,playbook,caps,full,{}\n"
    files = {run_log_path(DAY): _log(decisions=ON_TIME, snapshot={"valid": False, "reason": "stale"}),
             failures_path("book1_rules"): rows.encode()}  # fmt: skip
    reading = _status(files)
    assert reading.reason_code == "data_check_failed"
    assert "- execution: no valid execution snapshot (stale)" in reading.section.lines


def test_all_final_and_clean_is_no_breach_with_t1_s_reason_kept():
    files = {run_log_path(DAY): _log(decisions={"book1_rules": ON_TIME["book1_rules"]}, snapshot={"valid": True})}
    reading = _status(files)
    assert reading.reason_code == "no_approved_strategy" and NO_BREACH in reading.section.lines
    assert reading.section.lines[1] == "Reason: no strategy has passed"


def test_an_unreadable_record_is_data_check_failed_naming_it():
    reading = _status({run_log_path(DAY): b"{not json"})
    assert reading.reason_code == "data_check_failed"
    assert any(f"{run_log_path(DAY)}: not readable (JSONDecodeError)" in line for line in reading.section.lines)


RULE_CHECKS = ROOT / "fno" / "cards" / "rule_checks.py"
NEVER = ("fno.checks", "fno.playbook.registry")  # C3/C4 rules and D1's registry: read their outcomes, never re-run them


def test_t2_recomputes_no_rule_and_reads_no_registry():
    assert refused(full_imports(RULE_CHECKS), NEVER) == set()
    tree = ast.parse(RULE_CHECKS.read_text(encoding="utf-8"))
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not calls & {"write", "write_text", "write_bytes", "mkdir", "open"}  # it writes nothing under journal/


@pytest.mark.parametrize("planted", ["from fno.checks import validity\n", "import fno.playbook.registry\n",
                                     "from ..checks.gate import DataGate\n", "from fno import checks\n"])  # fmt: skip
def test_the_import_rule_catches_every_import_form(tmp_path, planted):
    """Judge 182: absolute and plain imports were not caught. Each planted form must be refused."""
    plant = tmp_path / "planted.py"
    plant.write_text(planted, encoding="utf-8")
    assert refused(full_imports(plant, package="fno.cards"), NEVER)


def test_an_unreadable_failures_file_is_data_check_failed_naming_it():
    files = {run_log_path(DAY): _log(decisions=ON_TIME), failures_path("book1_rules"): b"date,book\n2026-10-15,x\n"}
    reading = _status(files)  # no `day` column: the file is not C4's shape
    assert reading.reason_code == "data_check_failed"
    assert f"- decisions: {failures_path('book1_rules')}: not readable (KeyError)" in reading.section.lines
