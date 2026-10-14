"""Story E6 criteria 2 and 4: a statistical decision only on a review date and only past the gate (20 completed
positions and 3 months); keep, pause or retire by the plan's expected low; promotion only on shown net profit; open
positions never counted. Simulated paper histories through the real records."""

from datetime import date, timedelta

import pytest

from fno.constants import BOOK1_RULES, REVIEW_KEEP, REVIEW_PAUSE, REVIEW_RETIRE
from fno.scorecard.review import decide, full_months, interval

from .conftest import REVIEW, START
from .history import trade


def history(root, debits, first=START):
    """One completed position per debit (credit Rs 50 a unit), a day apart from `first`."""
    for n, debit in enumerate(debits):
        day = first + timedelta(days=n)
        trade(root, BOOK1_RULES, "fly-a-v1", f"t{n}", day, day + timedelta(days=1), credit=50, debit=debit)


def judged(make_run, on=REVIEW):
    cards, _ = make_run().run(on, {}, BOOK1_RULES, "fly-a-v1", pause=False)
    return cards[0].review


def test_a_winner_past_the_gate_is_kept_and_promotable(root, make_run):
    history(root, [10, 12, 8, 11, 9] * 4)  # about +Rs 2,500 a position, 20 positions over 3 months by the review
    verdict = judged(make_run)
    assert (verdict.gate_met, verdict.positions, verdict.months) == (True, 20, 3)
    assert verdict.decision == REVIEW_KEEP and verdict.promotable and "net profit shown" in verdict.reason


def test_below_the_gate_nothing_is_judged_and_nothing_promoted(root, make_run):
    history(root, [10] * 19)
    verdict = judged(make_run)
    assert verdict.decision == REVIEW_KEEP and not verdict.gate_met and not verdict.promotable
    assert "gate is not met (19 of 20 positions" in verdict.reason


def test_three_months_are_needed_even_with_twenty_positions(root, make_run):
    history(root, [10] * 20, first=date(2026, 11, 1))  # 2 full months by 20 Jan 2027
    verdict = judged(make_run)
    assert verdict.months == 2 and not verdict.gate_met and not verdict.promotable


def test_no_statistical_decision_outside_a_review_date(root, make_run):
    history(root, [80] * 20)  # a clear loser, yet the day is not a review date
    verdict = judged(make_run, REVIEW + timedelta(days=1))
    assert verdict.decision is None and "not a review date" in verdict.reason


def test_a_clear_loser_is_retired_on_the_review_date(root, make_run):
    history(root, [72, 70, 74, 71, 73] * 4)  # about -Rs 1,500 a position, far below the expected low of -500
    verdict = judged(make_run)
    assert verdict.decision == REVIEW_RETIRE and verdict.interval_rs[1] < -500 and not verdict.promotable


def test_an_inconclusive_winner_is_kept_but_never_promoted(root, make_run):
    history(root, [0, 90] * 10)  # +Rs 3,250 and -Rs 2,600 in turn: a positive total, but the interval spans zero
    verdict = judged(make_run)
    cards, _ = make_run().run(REVIEW, {}, BOOK1_RULES, "fly-a-v1", pause=False)
    assert cards[0].total_net > 0 and verdict.mean_rs > 0  # a profit on paper, not shown beyond chance
    assert verdict.decision == REVIEW_KEEP and verdict.interval_rs[0] < 0 and not verdict.promotable
    assert "inconclusive: not promoted" in verdict.reason


def test_an_open_position_is_never_counted(root, make_run):
    history(root, [10] * 20)
    trade(root, BOOK1_RULES, "fly-a-v1", "open", START)  # open, whatever its marks
    assert judged(make_run).positions == 20


def test_the_decision_rule_by_hand():
    assert decide(-600.0, (-900.0, -510.0), -500.0)[0] == REVIEW_RETIRE  # upper end below the expected low
    assert decide(-600.0, (-900.0, -500.0), -500.0)[0] == REVIEW_PAUSE  # mean below, interval reaches it
    assert decide(-500.0, (-900.0, -100.0), -500.0)[0] == REVIEW_KEEP  # mean at the expected low
    assert interval([7.0] * 25) == (7.0, 7.0)
    assert full_months(date(2026, 10, 14), date(2027, 1, 13)) == 2
    assert full_months(date(2026, 10, 14), date(2027, 1, 14)) == 3


def test_the_interval_is_the_seeded_bootstrap_of_the_mean():
    values = [float(v) for v in range(-10, 10)]
    low, high = interval(values)
    assert low < sum(values) / len(values) < high and interval(values) == (low, high)  # fixed seed: reproducible
    assert low == pytest.approx(-3.1, abs=0.5) and high == pytest.approx(2.1, abs=0.5)  # about mean +- 1.96 s/sqrt(n)
