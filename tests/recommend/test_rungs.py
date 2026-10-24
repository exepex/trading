"""REC1 criteria 3, 5, 6 and 13: the rung rule, the point-in-time cutoff (judge 620 S2, m2), the day conditions and the
calibration threshold, each with good, bad, boundary and empty cases."""

from datetime import date, timedelta

import pytest

from fno.recommend.constants import EvidenceRung, OutcomeSource
from fno.recommend.rungs import (
    EstablishedTest,
    ForwardOutcome,
    calibration_shown,
    counted_sessions,
    evidence,
    lowered,
    rung_for,
)
from tests.recommend.builders import DAY, MADE_AT

V = "school:CS1@1"
ALL_THREE = EstablishedTest(True, True, True)


def outcome(days_back: int = 1, source=OutcomeSource.FORWARD, counted=True, receipt=timedelta(hours=-1),
            version: str = V) -> ForwardOutcome:  # fmt: skip
    return ForwardOutcome(version, DAY - timedelta(days=days_back), source, counted,
                          None if receipt is None else MADE_AT + receipt)  # fmt: skip


def sessions(n: int) -> list[ForwardOutcome]:
    return [outcome(days_back=k) for k in range(1, n + 1)]


@pytest.mark.parametrize(("n", "review", "rung"), [
    (0, True, EvidenceRung.UNPROVEN), (1, False, EvidenceRung.EXPLORATORY), (29, True, EvidenceRung.EXPLORATORY),
    (30, False, EvidenceRung.EXPLORATORY), (30, True, EvidenceRung.WATCHING), (31, True, EvidenceRung.WATCHING),
])  # fmt: skip
def test_the_rung_follows_the_counted_sessions_and_the_review(n, review, rung):
    assert evidence(sessions(n), V, DAY, MADE_AT, review, EstablishedTest()).rung is rung


def test_established_needs_all_three_conditions_and_each_removed_gives_watching():
    assert rung_for(30, True, ALL_THREE) is EvidenceRung.ESTABLISHED
    for missing in range(3):
        flags = [True, True, True]
        flags[missing] = False
        assert rung_for(30, True, EstablishedTest(*flags)) is EvidenceRung.WATCHING
    assert rung_for(29, True, ALL_THREE) is EvidenceRung.EXPLORATORY
    assert rung_for(30, False, ALL_THREE) is EvidenceRung.EXPLORATORY


@pytest.mark.parametrize("source", [OutcomeSource.BACKTEST, OutcomeSource.SIMULATOR, OutcomeSource.REHEARSAL])
def test_only_forward_outcomes_count(source):
    planted = [outcome(days_back=k, source=source) for k in range(1, 40)]
    assert evidence(planted, V, DAY, MADE_AT, True, ALL_THREE).rung is EvidenceRung.UNPROVEN


def test_an_outcome_the_counting_rule_refused_never_counts():
    assert counted_sessions([outcome(counted=False)], V, DAY, MADE_AT) == []


def test_the_receipt_must_reach_main_strictly_before_the_decision():
    early = outcome(receipt=timedelta(seconds=-1))
    assert counted_sessions([early], V, DAY, MADE_AT) == [early.session]
    for late in (timedelta(0), timedelta(seconds=1)):
        assert counted_sessions([outcome(receipt=late)], V, DAY, MADE_AT) == []


def test_an_unknown_receipt_fails_closed():
    assert counted_sessions([outcome(receipt=None)], V, DAY, MADE_AT) == []


def test_day_d_never_counts_even_with_an_early_receipt():
    planted = outcome(days_back=0, receipt=timedelta(hours=-5))
    assert counted_sessions([planted], V, DAY, MADE_AT) == []


def test_a_session_counts_once_and_other_versions_are_apart():
    twice = [outcome(days_back=2), outcome(days_back=2), outcome(days_back=3, version="school:DB1@1")]
    found = evidence(twice, V, DAY, MADE_AT, False, EstablishedTest())
    assert (found.counted_sessions, found.first_session, found.last_session) == (
        1,
        DAY - timedelta(2),
        DAY - timedelta(2),
    )


def test_no_history_is_unproven_with_no_dates():
    found = evidence([], V, DAY, MADE_AT, True, ALL_THREE)
    assert (found.rung, found.counted_sessions, found.first_session, found.last_session) == (
        EvidenceRung.UNPROVEN,
        0,
        None,
        None,
    )


def test_the_record_shows_the_first_and_last_counted_sessions():
    found = evidence(sessions(3), V, DAY, MADE_AT, False, EstablishedTest())
    assert (found.first_session, found.last_session) == (DAY - timedelta(3), DAY - timedelta(1))


@pytest.mark.parametrize(("rung", "conditions", "shown"), [
    (EvidenceRung.ESTABLISHED, 0, EvidenceRung.ESTABLISHED), (EvidenceRung.ESTABLISHED, 1, EvidenceRung.WATCHING),
    (EvidenceRung.ESTABLISHED, 3, EvidenceRung.UNPROVEN), (EvidenceRung.EXPLORATORY, 2, EvidenceRung.UNPROVEN),
    (EvidenceRung.UNPROVEN, 1, EvidenceRung.UNPROVEN), (EvidenceRung.WATCHING, -2, EvidenceRung.WATCHING),
])  # fmt: skip
def test_day_conditions_only_lower_one_step_each_never_below_zero(rung, conditions, shown):
    assert lowered(rung, conditions) is shown


@pytest.mark.parametrize(("outcomes", "sessions_", "shown"), [
    (99, 60, False), (100, 59, False), (100, 60, True), (0, 0, False), (500, 200, True),
])  # fmt: skip
def test_calibration_needs_100_outcomes_over_60_sessions(outcomes, sessions_, shown):
    assert calibration_shown(outcomes, sessions_) is shown


def test_the_day_before_counts_at_the_boundary():
    assert counted_sessions([outcome(days_back=1)], V, DAY, MADE_AT) == [date(2026, 11, 1)]
