"""Judge 652 should-fix 1, the ledger half: Book 3's registrations only append to `research/ledger.csv` (its frozen
rows, 101-108 on main, never change), and a registration that rewrote an earlier row refuses the day, so F1t puts
every write path back and nothing is committed."""

import shutil
from pathlib import Path

import pytest

import fno.research_engine.ledger as ledger_module
from fno.book3.decider import DecisionRefused
from fno.research_engine.ledger import LEDGER_FILE
from tests.book3.builders import commit
from tests.book3.engine_builders import accepted, decider, decision, proposal, repository, spec

ROOT = Path(__file__).resolve().parents[2]


def with_real_ledger(tmp_path: Path) -> Path:
    root = repository(tmp_path)
    (root / LEDGER_FILE).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / LEDGER_FILE, root / LEDGER_FILE)
    commit(root, "the real trial ledger")
    return root


def test_a_registration_appends_to_the_real_ledger_and_keeps_every_earlier_byte(tmp_path):
    root = with_real_ledger(tmp_path)
    before = (root / LEDGER_FILE).read_bytes()
    decider(root).decide(accepted(root, decision(proposals=[proposal(spec("b3-new"))])))
    after = (root / LEDGER_FILE).read_bytes()
    assert after.startswith(before) and after.count(b"\n") == before.count(b"\n") + 1 and b"book3:b3-new" in after


def test_a_registration_that_rewrites_an_earlier_row_refuses_the_day(tmp_path, monkeypatch):
    root = with_real_ledger(tmp_path)
    real = ledger_module.write_ledger

    def rewrites_row_one(rows):
        return real([{**rows[0], "description": rows[0]["description"] + " (changed)"}, *rows[1:]])

    monkeypatch.setattr(ledger_module, "write_ledger", rewrites_row_one)
    with pytest.raises(DecisionRefused, match="append-only"):
        decider(root).decide(accepted(root, decision(proposals=[proposal(spec("b3-new"))])))
