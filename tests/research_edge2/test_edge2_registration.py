"""Every EDGE2 trial stays runnable under B4's ledger guard: its idea card is committed and unchanged since its
frozen protocol commit (judge J's S1: G1 inputs appended to a frozen card made the guard refuse it)."""

from pathlib import Path

import pytest

from fno.research_engine.ledger import Ledger

ROOT = Path(__file__).resolve().parents[2]
LEDGER = Ledger(ROOT)
EDGE2 = [row["trial_id"] for row in LEDGER.rows() if row["experiment"].startswith("edge2-") and row["protocol_commit"]]


def test_the_edge2_trials_are_in_the_ledger():
    assert len(EDGE2) >= 12


@pytest.mark.parametrize("trial", EDGE2)
def test_each_frozen_edge2_card_is_unchanged_since_its_freeze(trial):
    LEDGER.require_registered(trial)
