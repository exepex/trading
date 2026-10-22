"""Part d's own checks on fakes (story MS-INS, criteria 7-8; orchestrator's conditions 1-3): the false-"Watching" share
of a driver with no edge, with the upper end of its 95% interval at 10% or less, and a planted edge of +1.0 found. The
full grid (2,000 seeds at every real hold and the sensitivity markets) is in the Claims; these pin part of it."""

import pytest

from fno.school.instructor.paired.nulls import Market, share_watching, wilson_upper


@pytest.mark.parametrize("hold, batch, sessions", [(10, 15, 30), (15, 23, 60), (3, 10, 60)])
def test_no_edge_reads_watching_at_most_ten_percent_with_its_interval(hold, batch, sessions):
    share = share_watching(0.0, sessions, range(2000), batch, Market(hold=hold))
    assert wilson_upper(share, 2000) <= 0.10


def test_the_rejected_rule_batch_equal_to_hold_fails_the_gate_at_hold_15():
    """Why the batch is 1.5 x the hold: batch = hold leaves neighbouring batches linked by open positions."""
    share = share_watching(0.0, 120, range(2000), 15, Market(hold=15))
    assert wilson_upper(share, 2000) > 0.10


def test_a_planted_edge_of_one_is_found():
    assert share_watching(1.0, 30, range(500), 15, Market(hold=10)) >= 0.5
    assert share_watching(1.0, 60, range(500), 15, Market(hold=10)) >= 0.95


def test_the_wilson_upper_end():
    """p 0.1, n 2000, z 1.96: centre 0.1 + 3.8416 / 4000 = 0.10096; spread 1.96 x sqrt(0.09 / 2000 + 3.8416 / 16e6)
    = 0.01318; (0.10096 + 0.01318) / 1.00192 = 0.11392."""
    assert wilson_upper(0.1, 2000) == pytest.approx(0.11392, abs=1e-5) and wilson_upper(0.0, 100) > 0
