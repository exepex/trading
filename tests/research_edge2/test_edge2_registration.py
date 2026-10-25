"""Every EDGE2 trial stays runnable under B4's ledger guard and every logged G1 row stays reproducible (judge 642 S1):
each idea card is committed and unchanged since its frozen protocol commit, and its G1 row recomputes exactly from
the card and its result-derived inputs sidecar."""

from pathlib import Path

import pytest

from fno.research_engine.ledger import Ledger

ROOT = Path(__file__).resolve().parents[2]
LEDGER = Ledger(ROOT)
EDGE2 = [row["trial_id"] for row in LEDGER.rows() if row["experiment"].startswith("edge2-") and row["protocol_commit"]]


def test_the_edge2_trials_are_in_the_ledger():
    assert [str(t) for t in range(109, 124)] == EDGE2


@pytest.mark.parametrize("trial", EDGE2)
def test_each_frozen_edge2_card_is_unchanged_since_its_freeze(trial):
    LEDGER.require_registered(trial)


def g1_rows():
    from fno.factory.wiring import build_gate_log

    first = {}
    for row in build_gate_log(ROOT).rows():
        if row.gate == "G1" and row.trial_id in EDGE2:
            first.setdefault(row.trial_id, row)  # the screen's own row
    return sorted(first.values(), key=lambda r: int(r.trial_id))


@pytest.mark.parametrize("row", g1_rows(), ids=lambda r: r.trial_id)
def test_each_logged_g1_row_recomputes_from_the_card_and_its_sidecar(row):
    from fno.config import load_app_config
    from fno.factory.cost_wall import screen
    from fno.factory.gate_numbers import screen_numbers
    from fno.factory.inputs import screen_inputs
    from fno.factory.wiring import read_all_ideas

    card = next(c for c in read_all_ideas(ROOT) if c.trial_id == row.trial_id)
    result = screen(screen_inputs(card, load_app_config()["charges"]))
    assert (result.outcome, screen_numbers(result)) == (row.outcome, row.numbers)


def test_every_edge2_screen_is_covered():
    assert [r.trial_id for r in g1_rows()] == [str(t) for t in range(109, 121)]
