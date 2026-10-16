"""The repository's own factory records (story R1a): the three hand-registered cards read, match their ledger rows,
have back-filled `idea` rows only, and the gate log was only ever appended to (judge 259 notes 3 and 4)."""

import re

from fno.config import ROOT
from fno.factory.constants import BACKFILLED
from fno.factory.wiring import build_gate_log, build_trial_count, read_all_ideas
from fno.research_engine.ledger import Ledger


def test_every_card_matches_its_ledger_row():
    ledger = {row["trial_id"]: row for row in Ledger(ROOT).rows()}
    cards = {card.idea_id: card for card in read_all_ideas(ROOT)}
    assert {"R2": "53", "FT1": "54", "B0": "55"}.items() <= {k: c.trial_id for k, c in cards.items()}.items()
    for card in cards.values():
        row = ledger[card.trial_id]
        assert (row["experiment"], row["description"]) == (card.experiment, card.description)
        assert row["hypothesis"] == ("yes" if card.hypothesis else "no")
    assert cards["B0"].measurement


def test_the_hand_registered_cards_have_back_filled_idea_rows_only():
    gates = build_gate_log(ROOT)
    assert gates.history_problems() == []
    ideas = [row for row in gates.rows() if row.gate == "G0" and row.trial_id in ("53", "54", "55")]
    assert [(r.trial_id, r.outcome, r.numbers) for r in ideas] == [(t, "idea", BACKFILLED) for t in ("53", "54", "55")]


def test_r2s_code_screen_agrees_with_its_hand_screen():
    """R2 stopped at the cost wall by hand (results.md); R1b's code says screened_out, no stated edge (assumed hurdle).
    B0 and FT1 are measurements: never screened, so their last gate stays G0."""
    gates = build_gate_log(ROOT)
    r2 = gates.last("53")
    assert (r2.gate, r2.outcome, r2.numbers) == ("G1", "screened_out", "reason=no_stated_edge;assumed_hurdle=yes")
    assert gates.last("54").gate == gates.last("55").gate == "G0"


def test_the_readable_ledger_states_the_trial_count():
    text = (ROOT / "research" / "LEDGER.md").read_text(encoding="utf-8")
    assert int(re.search(r"Total trials so far: (\d+)", text).group(1)) == build_trial_count(ROOT).total


def test_the_report_command_prints_the_count_and_every_card(capsys):
    from fno.cli import main

    assert main(["factory", "report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith(f"{build_trial_count(ROOT).total} trials in the ledger; expected false passes at 0.01")
    assert any(line.startswith("B0 v1 (measurement): trial 55 of") for line in lines)


def test_b0s_card_agrees_with_its_playbook_version():
    """The playbook's edge_family stays the one source of a measurement version (R3); the card's flag must agree."""
    import yaml

    from fno.playbook.measurement import MEASUREMENT

    version = yaml.safe_load((ROOT / "playbook" / "b0-monthly-sc-v1.yaml").read_text(encoding="utf-8"))
    cards = {card.idea_id: card for card in read_all_ideas(ROOT)}
    assert cards["B0"].measurement is (version["edge_family"] == MEASUREMENT) is True
