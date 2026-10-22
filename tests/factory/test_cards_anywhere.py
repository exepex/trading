"""Cards kept beside their own story (story R1, orchestrator 22 Oct 2026): every reader of cards finds a registered card
wherever its ledger row says it lives, the ideas folder keeps working unchanged, and a card outside it is a
measurement or a test exactly like one inside."""

import pytest

from fno.cli import main
from fno.config import ROOT
from fno.factory.card import CardError
from fno.factory.card_paths import all_card_paths, card_path
from fno.factory.constants import IDEAS_FOLDER
from fno.factory.wiring import build_trial_count, read_all_ideas, read_idea
from fno.research_engine.ledger import Ledger
from tests.factory.helpers import BLOCK, CARD, commit, init_repo, write_card

SCHOOL = "research/school/MEAS.md"
MEASUREMENT = """id: MEAS
version: 1
trial: 3
experiment: meas-test
description: "MEAS: a planted measurement kept beside its story"
question: planted-measurement
hypothesis: no
measurement: yes
"""


def repo_with_a_card_elsewhere(tmp_path):
    root = init_repo(tmp_path)
    write_card(root, BLOCK.replace("trial: 3", "trial: 4"), CARD)
    write_card(root, MEASUREMENT, SCHOOL)
    ledger = Ledger(root)
    ledger.register("3", "meas-test", "MEAS: a planted measurement kept beside its story", "prospective", False, SCHOOL)
    ledger.register("4", "x1-test", "X1: a planted idea", "prospective", True, CARD)
    (root / "research/exp").mkdir()
    (root / "research/exp/PROTOCOL.md").write_text("# a protocol: no factory block here\n")
    ledger.register("5", "exp", "a protocol trial", "prospective", True, "research/exp/PROTOCOL.md")
    commit(root, "cards")
    return root


def test_a_card_the_ledger_names_outside_the_ideas_folder_is_read_with_the_ones_inside(tmp_path):
    root = repo_with_a_card_elsewhere(tmp_path)
    assert all_card_paths(root) == [CARD, SCHOOL], "the protocol file holds no block and is not a card"
    assert sorted((c.idea_id, c.measurement) for c in read_all_ideas(root)) == [("MEAS", True), ("X1", False)]


def test_one_idea_is_found_by_its_id_in_the_ideas_folder_first_then_by_the_ledger(tmp_path):
    root = repo_with_a_card_elsewhere(tmp_path)
    assert card_path("X1", root) == CARD and card_path("MEAS", root) == SCHOOL
    assert read_idea("MEAS", root).path == SCHOOL and read_idea("X1", root).path == CARD


def test_an_unknown_id_still_names_the_ideas_folder_path_in_its_error(tmp_path):
    root = repo_with_a_card_elsewhere(tmp_path)
    assert card_path("NOPE", root) == f"{IDEAS_FOLDER}/NOPE.md"
    with pytest.raises(CardError, match="no such card"):
        read_idea("NOPE", root)


def test_a_card_outside_the_ideas_folder_that_cannot_be_read_is_an_error_not_skipped(tmp_path):
    root = repo_with_a_card_elsewhere(tmp_path)
    write_card(root, "id: MEAS\nversion: 1\n", SCHOOL)  # the block is there but incomplete
    with pytest.raises(CardError, match="trial"):
        read_all_ideas(root)


def test_a_ledger_path_that_is_not_in_the_repository_is_ignored(tmp_path):
    root = init_repo(tmp_path)
    Ledger(root).register("3", "gone", "a path that was never written", "prospective", True, "research/gone/CARD.md")
    assert all_card_paths(root) == []


def test_the_report_lists_a_card_outside_the_ideas_folder_as_a_measurement_and_leaves_it_out_of_the_false_passes(
    tmp_path, monkeypatch, capsys
):
    root = repo_with_a_card_elsewhere(tmp_path)
    from fno.factory import wiring

    for name in ("read_all_ideas", "build_trial_count", "build_gate_log"):
        original = getattr(wiring, name)
        monkeypatch.setattr(wiring, name, lambda root=root, original=original: original(root))
    assert main(["factory", "report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "5 trials in the ledger" in lines[0] and "(4 trials; measurement trials left out: 3)" in lines[0]
    assert any(line.startswith("MEAS v1 (measurement): trial 3 of 5") for line in lines)


def test_every_card_the_ledger_names_in_the_real_repository_is_read():
    named = {row["protocol_path"] for row in Ledger(ROOT).rows() if row["protocol_path"].endswith(".md")}
    cards = {card.path for card in read_all_ideas(ROOT)}
    holding_a_block = {p for p in named if "```factory" in (ROOT / p).read_text(encoding="utf-8")}
    assert holding_a_block <= cards


def test_the_market_school_card_is_a_listed_measurement_in_the_real_report(capsys):
    if not any(row["trial_id"] == "99" for row in Ledger(ROOT).rows()):
        pytest.skip("trial 99 (the market school pilot) is not registered on this branch yet")
    assert main(["factory", "report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    total = build_trial_count(ROOT).total
    assert any(line.startswith(f"CARD_P1 v2 (measurement): trial 99 of {total}") for line in lines)
    assert "99" in lines[0].split("measurement trials left out:")[1]


def test_the_ideas_folder_wins_when_an_id_is_found_there_and_elsewhere(tmp_path):
    root = repo_with_a_card_elsewhere(tmp_path)
    twin = "research/school/X1.md"
    write_card(root, BLOCK.replace("trial: 3", "trial: 6"), twin)
    Ledger(root).register("6", "x1-test", "X1 twin", "prospective", True, twin)
    commit(root, "a twin")
    assert card_path("X1", root) == CARD
