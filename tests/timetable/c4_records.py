"""A committed D3 run holding one record with a given `validity.c4` (stories E3 and C4): written through D3's own
store, so its `records.sha256` is real; only the fields the C4 gate reads are in the record."""

from dataclasses import replace
from datetime import date

import pytest

from fno.constants import BOOK1_RULES
from fno.desk.daily_ports import CommittedDecision
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
