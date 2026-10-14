"""Story C4 inside story D3: every trade D2 chooses is checked by C4 before its record is written. `validity.c4` holds
the result; a failure turns the trade into "no trade, blocked by C4", leaves it out of the day's chosen list and is
logged in `journal/<book>/validity_failures.csv`; a replay with the same validator reproduces all of it."""

import csv
import json
from datetime import datetime, time

from fno.checks.validity import Limits, ValidityChecker
from fno.checks.validity_adapter import BookTradeValidator
from fno.checks.validity_evidence import EvidenceReader
from fno.checks.validity_failures import ValidityFailureLog
from fno.checks.wiring import validity_modes
from fno.composition import DESK_DECISION_TIME
from fno.models import IST
from fno.playbook.decision_run import DecisionRun, replay
from fno.playbook.decision_store import DecisionStore
from fno.playbook.decision_validity import BLOCKED
from fno.quotes.recorder import DATASET
from tests.checks.builders import committed_record
from tests.desk.builders import DictStore, row, write_snapshot
from tests.playbook.evaluation_builders import (
    DAY,
    EXPIRY,
    Counts,
    FixedValues,
    OwnShadowBooks,
    chain_market,
    evaluator,
    price,
)
from tests.risk.builders import ZERO_CHARGES, book

from .builders import CONTEXT, SAME_CODE, doc, snapshot

CHOSEN = "sc-a-v1_2026-11-27"


class Captures:
    def __init__(self, record):
        self.given = record

    def record(self, day):
        return self.given


def quote_store() -> DictStore:
    """The A4 capture of DAY holding D2's test chain (mid = D2's price), received at 14:55:10."""
    store = DictStore()
    rows = [row(k, t, price(k, t) - 0.5, price(k, t) + 0.5, expiry=EXPIRY) for k in range(24_000, 26_050, 50)
            for t in ("CE", "PE")]  # fmt: skip
    for r in rows:
        r["response_received_at"] = datetime.combine(DAY, time(14, 55, 10), IST).isoformat()
    write_snapshot(store, "exec", rows, datetime.combine(DAY, time(14, 55), IST),
                   datetime.combine(DAY, time(14, 56), IST), day=DAY)  # fmt: skip
    return store


def validator(root, committed=True, log=True) -> BookTradeValidator:
    """D2's test evaluator models no charges, so C4 reads the same (zero) charge table."""
    store = quote_store()
    checker = ValidityChecker(EvidenceReader(store, DATASET), ZERO_CHARGES, Limits(10_000, 3), validity_modes())
    record = committed_record(store, DAY, "exec") if committed else None
    log_to = ValidityFailureLog(root) if log else None
    return BookTradeValidator("book1_rules", checker, Captures(record), DESK_DECISION_TIME, log_to)


def decide(root, check):
    return DecisionRun(evaluator(), DecisionStore(root, "book1_rules"), check).decide(
        DAY, snapshot(doc("sc-a")), chain_market(), FixedValues(), book(), Counts(), OwnShadowBooks(), CONTEXT
    )


def records(run):
    return {p.stem: json.loads(p.read_text()) for p in run.glob("*.json") if p.name != "inputs.json"}


def test_a_valid_trade_carries_its_c4_result_and_stays_chosen(tmp_path):
    run = decide(tmp_path, validator(tmp_path))
    stored = records(run)
    c4 = stored[CHOSEN]["validity"]["c4"]
    assert c4["ok"] and c4["mode"] == "playbook" and {c["check"] for c in c4["checks"]} >= {"evidence", "max_loss"}
    assert stored[CHOSEN]["chosen_action"] == "trade"
    assert stored["no_trade"]["decision"]["reason"] == "chosen: ['sc-a-v1:2026-11-27']"
    assert not (tmp_path / "journal" / "book1_rules" / "validity_failures.csv").exists()
    assert replay(run, evaluator(), SAME_CODE, validator=validator(tmp_path, log=False)) == []


def test_a_failed_trade_is_blocked_logged_and_replayed(tmp_path):
    run = decide(tmp_path, validator(tmp_path, committed=False))
    stored = records(run)
    record = stored[CHOSEN]
    assert record["validity"]["c4"]["ok"] is False
    assert record["chosen_action"] == "no trade" and record["decision"]["action"] == "no trade"
    assert record["reason"].startswith(f"{BLOCKED}: evidence: no committed capture record")
    assert record["decision"]["outcome"] == "chosen"  # D2's own outcome is kept; C4's block is in action and reason
    assert stored["no_trade"]["decision"]["action"] == "no trade"
    with open(tmp_path / "journal" / "book1_rules" / "validity_failures.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [(r["opportunity_id"], r["check"]) for r in rows] == [("sc-a-v1:2026-11-27", "evidence")]
    assert replay(run, evaluator(), SAME_CODE, validator=validator(tmp_path, committed=False, log=False)) == []
    assert any("validity differs" in d for d in replay(run, evaluator(), SAME_CODE, validator=validator(tmp_path)))


def test_without_a_validator_the_c4_field_stays_empty(tmp_path):
    assert records(decide(tmp_path, None))[CHOSEN]["validity"]["c4"] is None
