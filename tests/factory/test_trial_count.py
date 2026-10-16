"""The trial count (story R1a, criteria 3 and 10): "trial k of K" in ledger order; no measurement in false passes."""

import pytest

from fno.factory.card import IdeaCard
from fno.factory.gate_log import GateRow
from fno.factory.status import false_pass_line, idea_line
from fno.factory.trial_count import TrialCount

COUNT = TrialCount([{"trial_id": t} for t in ("1", "2", "10", "3")])


def card(trial, measurement=False):
    return IdeaCard("X1", 1, trial, "x1", "x", "q", not measurement, measurement, "research/ideas/X1.md")


def test_k_follows_the_ledger_order_and_k_is_its_row_count():
    assert COUNT.total == 4 and COUNT.position("10") == 3 and COUNT.label("3") == "trial 4 of 4"
    with pytest.raises(KeyError):
        COUNT.position("99")


def test_expected_false_passes_leave_out_measurements_only():
    passes = COUNT.false_passes(0.01, ["3", "77"])
    assert (passes.tests, passes.measurements) == (3, ("3",)) and passes.expected == pytest.approx(0.03)
    assert COUNT.false_passes(0.05, []).expected == pytest.approx(0.2)
    assert false_pass_line(COUNT, passes) == (
        "4 trials in the ledger; expected false passes at 0.01 one-sided: 0.03 "
        "(3 trials; measurement trials left out: 3)"
    )


def test_the_idea_line_shows_the_place_the_last_gate_and_the_labels():
    row = GateRow("10", "G0", "idea", "2026-10-15", "abc", "backfilled=yes")
    assert idea_line(card("10", measurement=True), COUNT, row) == (
        "X1 v1 (measurement): trial 3 of 4; last gate G0 idea on 2026-10-15 (back-filled)"
    )
    assert idea_line(card("2"), COUNT, None) == "X1 v1: trial 2 of 4; no gate-log row (register or back-fill it)"
