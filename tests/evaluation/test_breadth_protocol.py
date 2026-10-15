"""Story BR1a, criteria 1-3, 8 and 9: BR1's protocol in S1's format, frozen by the same freezer to its own record
and ledger row without the real-money gate, and refused while any item is a proposal. S1's own tests are unchanged."""

import argparse
import re
from datetime import date

import pytest

from fno.config import ROOT
from fno.evaluation import wiring
from fno.evaluation.breadth import BREADTH, BREADTH_ITEMS, BREADTH_PROTOCOL_FILE
from fno.evaluation.cli import EXIT_FAILED, add_evaluation_parser, cmd_evaluation
from fno.evaluation.completeness import completeness_problems, undecided_items
from fno.evaluation.freeze import FreezeRefused, read_record
from fno.evaluation.order import verify
from fno.evaluation.protocol import parse_protocol
from fno.research_engine.ledger import read_ledger
from tests.evaluation.builders import LEDGER_HEAD, decided
from tests.playbook.builders import commit_all, git

TEXT = (ROOT / BREADTH_PROTOCOL_FILE).read_text(encoding="utf-8")
README = (ROOT / "research/breadth/README.md").read_text(encoding="utf-8")
TODAY = date(2026, 10, 21)
CODE = "research/breadth/scoring.py"


def small_frozen_files(text: str) -> str:
    listed = f"- **Value:** `{BREADTH_PROTOCOL_FILE}`, `{CODE}`."
    return re.sub(r"(### `frozen_files` [^\n]*\n)- \*\*Value:\*\*.*?\n(- \*\*Status)", rf"\1{listed}\n\2", text,
                  flags=re.DOTALL)  # fmt: skip


def breadth_repo(root, text: str) -> None:
    git(root, "init", "-q")
    for name, body in {BREADTH_PROTOCOL_FILE: text, CODE: "SCORE = 1\n", "research/ledger.csv": LEDGER_HEAD}.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(body, encoding="utf-8")
    commit_all(root, "breadth protocol")


def test_the_committed_breadth_protocol_is_complete_for_its_own_items_and_every_item_is_a_proposal():
    protocol = parse_protocol(TEXT)
    assert completeness_problems(TEXT, protocol, BREADTH_ITEMS) == []
    assert set(protocol.items) == set(BREADTH_ITEMS) and undecided_items(protocol) == list(protocol.items)


def test_the_freezer_refuses_the_breadth_protocol_while_any_item_is_a_proposal(tmp_path):
    breadth_repo(tmp_path, small_frozen_files(TEXT))
    with pytest.raises(FreezeRefused, match="not decided by the owner"):
        wiring.build_freezer(tmp_path, "breadth").freeze(TODAY)
    assert not (tmp_path / BREADTH.freeze_path(1)).exists()


def test_a_decided_breadth_protocol_freezes_to_its_own_record_and_ledger_row_without_the_gate(tmp_path):
    breadth_repo(tmp_path, small_frozen_files(decided(TEXT)))
    record = wiring.build_freezer(tmp_path, "breadth").freeze(TODAY)
    written = (tmp_path / "research/breadth/FREEZE_v1.md").read_text()
    assert set(record.hashes) == {BREADTH_PROTOCOL_FILE, CODE} and read_record(written, BREADTH) == record
    assert written.startswith("# Breadth protocol freeze record") and not (tmp_path / "research/evaluation").exists()
    row = read_ledger((tmp_path / "research/ledger.csv").read_text())[-1]
    assert row["experiment"] == "breadth-protocol-v1" and row["protocol_commit"] == record.protocol_commit


def test_verify_finds_a_hashed_breadth_file_changed_after_its_freeze_and_s1_sees_nothing_frozen(tmp_path):
    breadth_repo(tmp_path, small_frozen_files(decided(TEXT)))
    wiring.build_freezer(tmp_path, "breadth").freeze(TODAY)
    assert verify(tmp_path, BREADTH) == []
    (tmp_path / CODE).write_text("SCORE = 2\n")
    assert verify(tmp_path, BREADTH) == [f"v1: {CODE} changed after the freeze (a change is a new version)"]
    assert verify(tmp_path) == []


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_evaluation_parser(parser.add_subparsers(dest="cmd"))
    return parser.parse_args(argv)


def _run(argv: list[str]) -> int:
    return cmd_evaluation(_parse(argv))


def test_the_freeze_command_takes_protocol_breadth_and_defaults_to_s1(tmp_path, monkeypatch):
    chosen = []
    real = wiring.build_freezer
    monkeypatch.setattr(wiring, "build_freezer", lambda protocol: chosen.append(protocol) or real(tmp_path, protocol))
    breadth_repo(tmp_path, small_frozen_files(TEXT))
    assert _run(["evaluation", "freeze", "--protocol", "breadth"]) == EXIT_FAILED  # undecided: refused
    (tmp_path / BREADTH_PROTOCOL_FILE).write_text(small_frozen_files(decided(TEXT)))
    commit_all(tmp_path, "decided")
    assert _run(["evaluation", "freeze", "--protocol", "breadth"]) == 0
    assert (tmp_path / BREADTH.freeze_path(1)).is_file()
    assert chosen == ["breadth", "breadth"]
    assert {_parse(["evaluation", action]).protocol for action in ("check", "freeze", "verify")} == {"evaluation"}


def test_the_suite_fails_when_a_frozen_breadth_target_changes():
    assert verify(ROOT, BREADTH) == []


def test_no_breadth_text_words_a_claim_as_beating_all_baselines():
    claim = parse_protocol(TEXT).items["claim_meaning"].value
    assert "family F beats the primary baseline on T1, end of day" in claim
    for text in (claim, TEXT, README):
        assert not re.search(r"beats? all", text, re.IGNORECASE)


@pytest.mark.parametrize("text", [TEXT, README], ids=["protocol", "readme"])
def test_the_owners_wording_appears_in_the_protocol_and_the_readme(text):
    flat = " ".join(text.split()).replace("**", "").lower()
    for wording in ("6 to 42", "about 9", "planning projections", "never deadlines",
                    "whether any forecaster beats the frozen primary baseline by 2-3% is unknown"):  # fmt: skip
        assert wording in flat


def test_the_verify_command_takes_protocol_breadth(capsys):
    assert _run(["evaluation", "verify", "--protocol", "breadth"]) == 0
    assert "unchanged" in capsys.readouterr().out
