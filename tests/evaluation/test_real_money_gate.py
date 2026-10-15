"""Story RM1: the real-money gate is checked like the protocol, frozen with it and never after it. The freeze refuses
while the gate is unlisted, missing, incomplete or not decided by the owner; a frozen gate edited later shows as
changed. Nothing in `fno/evaluation/` can reach a broker or the paper desk."""

import ast
from datetime import date

import pytest

from fno.config import ROOT
from fno.evaluation.freeze import FreezeRefused, ProtocolFreezer, freeze_path, read_record
from fno.evaluation.gate import GATE_FILE, GATE_ITEMS, gate_problems
from fno.evaluation.order import verify
from fno.evaluation.protocol import PROPOSAL, parse_protocol
from fno.playbook.history import PlaybookGit
from tests.evaluation.builders import GATE, decided, protocol_repo, small_frozen_files
from tests.playbook.builders import commit_all

TODAY = date(2026, 10, 21)
GATE_DECIDED = "decided by the owner on 2026-10-15"
UNDECIDED_GATE = GATE.replace(f"**Status:** {GATE_DECIDED}", f"**Status:** {PROPOSAL}", 2)


def freezer(root) -> ProtocolFreezer:
    return ProtocolFreezer(root, PlaybookGit(root))


def ledger_text(root) -> str:
    return (root / "research/ledger.csv").read_text()


def test_the_committed_gate_has_every_item_complete_and_decided_by_the_owner():
    assert set(parse_protocol(GATE).items) == set(GATE_ITEMS)
    assert gate_problems(GATE, decided=True) == []


def test_the_gate_needs_no_version_line_but_the_protocol_still_does():
    assert "Protocol version" not in GATE
    assert gate_problems(GATE, decided=False) == []


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("- **Evidence:** reasoning only", "- **Evidence:** a hunch", "evidence must be one of"),
        (f"- **Status:** {GATE_DECIDED}", "- **Status:** agreed", "status must be"),
        ("Real account Rs 2,00,000", "Real account to be decided", "'to be decided' is not a value or a rule"),
        ("Real account Rs 2,00,000", "Real account TBD", "'TBD' is not a value or a rule"),
    ],
)
def test_a_bad_label_status_or_open_value_in_the_gate_is_named(old, new, expected):
    assert any(expected in p for p in gate_problems(GATE.replace(old, new, 1), decided=False))


def test_a_missing_or_empty_gate_item_is_named():
    start, end = GATE.index("### `owner_approval`"), GATE.index("### `real_test_account`")
    assert gate_problems(GATE[:start] + GATE[end:], decided=False) == [
        f"owner_approval: missing ({GATE_ITEMS['owner_approval']})"
    ]
    reason = GATE[GATE.index("- **Reason:** 8.3 condition 7.") :].split("\n", 1)[0]
    assert gate_problems(GATE.replace(reason, "- **Reason:**", 1), decided=False) == ["owner_approval: no Reason"]


def test_an_undecided_gate_item_is_complete_but_not_decided():
    assert gate_problems(UNDECIDED_GATE, decided=False) == []
    assert gate_problems(UNDECIDED_GATE, decided=True) == ["not decided by the owner: scope, paper_evidence"]


def test_an_undecided_gate_refuses_the_freeze_and_writes_nothing(tmp_path):
    protocol_repo(tmp_path, gate=UNDECIDED_GATE)
    before = ledger_text(tmp_path)
    with pytest.raises(FreezeRefused, match="gate is not ready to freeze: not decided by the owner: scope, paper"):
        freezer(tmp_path).freeze(TODAY)
    assert not (tmp_path / freeze_path(1)).exists() and ledger_text(tmp_path) == before


def test_a_protocol_that_does_not_list_the_gate_is_never_frozen(tmp_path):
    unlisted = small_frozen_files(decided()).replace(", `research/evaluation/REAL_MONEY_GATE.md`", "")
    protocol_repo(tmp_path, unlisted)
    with pytest.raises(FreezeRefused, match="REAL_MONEY_GATE.md \\(the real-money gate, story RM1\\) must be listed"):
        freezer(tmp_path).freeze(TODAY)
    assert not (tmp_path / freeze_path(1)).exists()


def test_a_listed_gate_that_does_not_exist_refuses_the_freeze(tmp_path):
    protocol_repo(tmp_path)
    (tmp_path / GATE_FILE).unlink()
    commit_all(tmp_path, "gate removed")
    with pytest.raises(FreezeRefused, match="REAL_MONEY_GATE.md is listed in frozen_files but does not exist"):
        freezer(tmp_path).freeze(TODAY)


def test_an_uncommitted_gate_edit_refuses_the_freeze(tmp_path):
    protocol_repo(tmp_path)
    (tmp_path / GATE_FILE).write_text(GATE + "\n")
    with pytest.raises(FreezeRefused, match=f"commit {GATE_FILE} first"):
        freezer(tmp_path).freeze(TODAY)


def test_a_decided_gate_is_hashed_in_the_freeze_and_a_later_edit_shows(tmp_path):
    protocol_repo(tmp_path)
    record = freezer(tmp_path).freeze(TODAY)
    commit_all(tmp_path, "freeze v1")
    assert GATE_FILE in read_record((tmp_path / freeze_path(1)).read_text()).hashes == record.hashes
    assert verify(tmp_path) == []
    (tmp_path / GATE_FILE).write_text(GATE.replace("Rs 5,000 (2.5%)", "Rs 6,000 (3%)", 1))
    assert verify(tmp_path) == [f"v1: {GATE_FILE} changed after the freeze (a change is a new version)"]


def test_the_check_command_reports_the_gate(capsys):
    from fno.evaluation.cli import _check_gate

    assert _check_gate(ROOT, decided=True) is False
    assert f"{GATE_FILE}: complete and decided" in capsys.readouterr().out


def test_the_check_command_names_an_undecided_gate(tmp_path, capsys):
    from fno.evaluation.cli import _check_gate

    (tmp_path / GATE_FILE).parent.mkdir(parents=True)
    (tmp_path / GATE_FILE).write_text(UNDECIDED_GATE)
    assert _check_gate(tmp_path, decided=True) is True
    assert "gate: not decided by the owner: scope, paper_evidence" in capsys.readouterr().out


FORBIDDEN_IMPORTS = ("providers", "desk", "books", "broker", "groww", "orders")


def test_the_evaluation_package_imports_no_broker_provider_or_desk_module():
    imported = set()
    for path in (ROOT / "fno/evaluation").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                imported.add(f"{'.' * node.level}{node.module or ''}")
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
    assert [m for m in imported if any(part in FORBIDDEN_IMPORTS for part in m.strip(".").split("."))] == []
