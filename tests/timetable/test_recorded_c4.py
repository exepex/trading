"""Judge 83's ruling for E3: the fill reads C4's completed pass from the committed D3 record (`validity.c4`), written
against the decision's own capture; it never runs C4 again at the 15:15 capture. A record without a pass, with a failed
pass, edited after commit, or missing is never filled."""

import json
from dataclasses import replace
from datetime import date

import pytest

from fno.constants import BOOK1_RULES
from fno.desk.daily_ports import CommittedDecision
from fno.desk.recorded_c4 import RecordedC4Pass
from fno.playbook import decision_store
from fno.playbook.decision_store import DecisionStore
from tests.desk.builders import at, fly_order

DAY = date(2026, 10, 14)
OPPORTUNITY = "sc-a-v1:2026-11-24"
PASSED = {"mode": "playbook", "ok": True, "checks": [{"check": "max_loss", "ok": True, "reason": "", "numbers": {}}]}


def record(c4):
    return {"opportunity_id": OPPORTUNITY, "validity": {"c4": c4, "candidate": "built"}}


@pytest.fixture
def committed_run(tmp_path, monkeypatch):
    """A D3 run written through D3's own store (its records and their `records.sha256`); only the fields this gate
    reads are in the record, so D3's full schema check is skipped."""
    monkeypatch.setattr(decision_store, "validate_record", lambda r: None)

    def write(c4, folder="a") -> CommittedDecision:
        run = DecisionStore(tmp_path / folder, BOOK1_RULES).write(DAY, "2026-10-14-r1", None, [record(c4)])
        order = replace(fly_order("t1"), decision_id=OPPORTUNITY)
        return CommittedDecision(BOOK1_RULES, run.name, "c1", at(15, 5), (order,), run)

    return write


def problems(decision):
    return RecordedC4Pass().problems(decision, decision.orders[0])


def test_a_recorded_completed_pass_lets_the_order_fill(committed_run):
    assert problems(committed_run(PASSED)) == []


@pytest.mark.parametrize(("c4", "why"), [
    (None, "no completed C4 pass recorded (validity.c4 is null)"),
    ({"mode": "playbook", "ok": True, "checks": []}, "no completed C4 pass recorded"),
    ({**PASSED, "ok": False, "checks": [{"check": "leg_price", "ok": False}]}, "C4 failed: leg_price"),
    ({**PASSED, "ok": "yes"}, "no completed C4 pass recorded"),
])  # fmt: skip
def test_no_pass_a_failed_pass_or_a_malformed_one_never_fills(committed_run, c4, why):
    assert why in problems(committed_run(c4))[0]


def test_a_record_edited_after_commit_or_missing_never_fills(committed_run):
    decision = committed_run({**PASSED, "ok": False, "checks": [{"check": "leg_price", "ok": False}]})
    path = next(p for p in decision.run.glob("*.json"))
    body = json.loads(path.read_text())
    body["validity"]["c4"] = PASSED  # someone turns the failure into a pass by hand
    path.write_text(json.dumps(body))
    assert "files changed after they were committed" in problems(decision)[0]
    other = replace(decision.orders[0], decision_id="sc-b-v1:2026-11-24")
    assert "no D3 record sc-b-v1_2026-11-24.json" in RecordedC4Pass().problems(decision, other)[0]
    assert "names no D3 run folder" in problems(CommittedDecision(BOOK1_RULES, "r", "c", at(15, 5), decision.orders))[0]


def test_c4_is_never_run_again_at_the_execution_capture():
    """The gate takes no market, snapshot or validator: it can only read what was committed (by construction)."""
    import inspect

    assert list(inspect.signature(RecordedC4Pass.problems).parameters) == ["self", "decision", "order"]
    assert inspect.signature(RecordedC4Pass).parameters == {}
