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
    hand = [row for row in gates.rows() if row.trial_id in ("53", "54", "55")]
    assert [(r.trial_id, r.gate, r.outcome, r.numbers) for r in hand] == [
        (t, "G0", "idea", BACKFILLED) for t in ("53", "54", "55")
    ]


def test_the_readable_ledger_states_the_trial_count():
    text = (ROOT / "research" / "LEDGER.md").read_text(encoding="utf-8")
    assert int(re.search(r"Total trials so far: (\d+)", text).group(1)) == build_trial_count(ROOT).total


def test_the_report_command_prints_the_count_and_every_card(capsys):
    from fno.cli import main

    assert main(["factory", "report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith(f"{build_trial_count(ROOT).total} trials in the ledger; expected false passes at 0.01")
    assert any(line.startswith("B0 v1 (measurement: never promoted): trial 55 of") for line in lines)
