"""A card's result-derived G1-G3 inputs in a sidecar beside it (EDGE2, judge 642 S1): the frozen card stays byte for
byte as frozen, the gates read card and sidecar together, the sidecar holds only G1-G3 inputs and never repeats a card
field, it is never listed as a card, and an uncommitted sidecar stops a gate."""

from datetime import date

import pytest

from fno.factory.card import CardError
from fno.factory.card_paths import all_card_paths
from fno.factory.constants import DATA_SPEND_FILE
from fno.factory.gate_order import GateStepError
from fno.factory.wiring import build_gate_steps, build_registration, read_idea

from .helpers import BLOCK, INPUTS, REGISTER, commit, init_repo, write_card

DAY = date(2026, 10, 25)
SIDECAR = "research/ideas/X1.inputs.md"
SCREEN_AND_PLAN = "\n".join(line for line in INPUTS.splitlines() if not line.startswith(("data_sets", "measures")))
SPEND = "\n".join(line for line in INPUTS.splitlines() if line.startswith(("data_sets", "measures"))) + "\n"


def write_sidecar(root, text):
    (root / SIDECAR).write_text(f"# Inputs\n\n```factory-inputs\n{text}\n```\n")


@pytest.fixture
def repo(tmp_path):
    init_repo(tmp_path)
    (tmp_path / DATA_SPEND_FILE).write_text(REGISTER)
    write_card(tmp_path, BLOCK + SPEND)
    build_registration(tmp_path).register(read_idea("X1", tmp_path), DAY)
    commit(tmp_path, "register X1")
    return tmp_path


def test_the_gates_read_the_card_and_its_sidecar_together(repo):
    card_before = (repo / "research/ideas/X1.md").read_text()
    write_sidecar(repo, SCREEN_AND_PLAN)
    commit(repo, "inputs")
    assert build_gate_steps(repo).screen(read_idea("X1", repo), DAY).figures["net"] == pytest.approx(450.0)
    assert (repo / "research/ideas/X1.md").read_text() == card_before


def test_without_a_sidecar_the_card_alone_is_read(repo):
    assert "gross" not in read_idea("X1", repo).inputs.values


@pytest.mark.parametrize("extra", ["trial: 4", 'measures: "again"', "playbook_name: x"])
def test_the_sidecar_holds_only_screen_and_plan_inputs(repo, extra):
    write_sidecar(repo, SCREEN_AND_PLAN + "\n" + extra)
    with pytest.raises(CardError):
        read_idea("X1", repo)


def test_a_field_in_both_the_card_and_the_sidecar_is_refused(repo, tmp_path):
    card = repo / "research/ideas/X1.md"
    card.write_text(card.read_text().replace("measures:", "pass_level: 0.01\nmeasures:"))
    write_sidecar(repo, SCREEN_AND_PLAN)
    with pytest.raises(CardError, match="'pass_level' is in both the card and its sidecar"):
        read_idea("X1", repo)


def test_a_sidecar_without_its_block_is_refused(repo):
    (repo / SIDECAR).write_text("# Inputs\n\n```factory\ngross: 1\n```\n")
    with pytest.raises(CardError, match="sidecar: needs exactly one"):
        read_idea("X1", repo)


def test_a_sidecar_is_never_listed_as_a_card(repo):
    write_sidecar(repo, SCREEN_AND_PLAN)
    assert all_card_paths(repo) == ["research/ideas/X1.md"]


def test_an_uncommitted_or_untracked_sidecar_stops_the_gate(repo):
    write_sidecar(repo, SCREEN_AND_PLAN)
    with pytest.raises(GateStepError, match="uncommitted changes: commit its inputs"):
        build_gate_steps(repo).screen(read_idea("X1", repo), DAY)
    commit(repo, "inputs")
    write_sidecar(repo, SCREEN_AND_PLAN.replace("least_favourable: 1200", "least_favourable: 5000"))
    with pytest.raises(GateStepError, match="uncommitted changes: commit its inputs"):
        build_gate_steps(repo).screen(read_idea("X1", repo), DAY)
