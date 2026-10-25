"""REC1 criteria 3, 5, 6 and 13: the rung rule, the point-in-time cutoff (judge 620 S2, m2), the day conditions and the
calibration threshold, each with good, bad, boundary and empty cases."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from fno.recommend.constants import EvidenceRung, OutcomeSource
from fno.recommend.rungs import (
    EvidenceReports,
    ForwardOutcome,
    VersionEvidence,
    calibration_shown,
    counted_sessions,
    evidence,
    lowered,
    rung_for,
)
from tests.recommend.builders import DAY, ESTABLISHED, MADE_AT, REVIEWED

V = "school:CS1@1"
NONE = EvidenceReports()


def outcome(days_back: int = 1, source=OutcomeSource.FORWARD, counted=True, receipt=timedelta(hours=-1),
            version: str = V) -> ForwardOutcome:  # fmt: skip
    return ForwardOutcome(version, DAY - timedelta(days=days_back), source, counted,
                          None if receipt is None else MADE_AT + receipt)  # fmt: skip


def sessions(n: int) -> list[ForwardOutcome]:
    return [outcome(days_back=k) for k in range(1, n + 1)]


@pytest.mark.parametrize(("n", "reports", "rung"), [
    (0, REVIEWED, EvidenceRung.UNPROVEN), (1, NONE, EvidenceRung.EXPLORATORY), (29, REVIEWED, EvidenceRung.EXPLORATORY),
    (30, NONE, EvidenceRung.EXPLORATORY), (30, REVIEWED, EvidenceRung.WATCHING), (31, REVIEWED, EvidenceRung.WATCHING),
    (0, ESTABLISHED, EvidenceRung.UNPROVEN), (29, ESTABLISHED, EvidenceRung.EXPLORATORY),
])  # fmt: skip
def test_the_rung_follows_the_counted_sessions_and_the_reports(n, reports, rung):
    assert evidence(sessions(n), V, DAY, MADE_AT, reports).rung is rung


def test_established_needs_all_three_reports_and_each_removed_gives_watching():
    assert rung_for(30, ESTABLISHED) is EvidenceRung.ESTABLISHED
    for missing in ("sample_plan", "lower_bound", "second_window"):
        assert rung_for(30, replace(ESTABLISHED, **{missing: None})) is EvidenceRung.WATCHING
    assert rung_for(29, ESTABLISHED) is EvidenceRung.EXPLORATORY
    assert rung_for(30, replace(ESTABLISHED, review=None)) is EvidenceRung.EXPLORATORY


@pytest.mark.parametrize("source", [OutcomeSource.BACKTEST, OutcomeSource.SIMULATOR, OutcomeSource.REHEARSAL])
def test_only_forward_outcomes_count(source):
    planted = [outcome(days_back=k, source=source) for k in range(1, 40)]
    assert evidence(planted, V, DAY, MADE_AT, ESTABLISHED).rung is EvidenceRung.UNPROVEN


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
    found = evidence(twice, V, DAY, MADE_AT, NONE)
    assert (found.counted_sessions, found.first_session, found.last_session) == (
        1,
        DAY - timedelta(2),
        DAY - timedelta(2),
    )


def test_no_history_is_unproven_with_no_dates():
    found = evidence([], V, DAY, MADE_AT, ESTABLISHED)
    assert (found.rung, found.counted_sessions, found.first_session, found.last_session) == (
        EvidenceRung.UNPROVEN,
        0,
        None,
        None,
    )


def test_the_record_shows_the_first_and_last_counted_sessions():
    found = evidence(sessions(3), V, DAY, MADE_AT, NONE)
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


FIRST, LAST = date(2026, 9, 1), date(2026, 11, 1)


@pytest.mark.parametrize(("rung", "count", "reports"), [
    (EvidenceRung.ESTABLISHED, 0, ESTABLISHED),  # judge 629: "proven" with no evidence
    (EvidenceRung.WATCHING, 29, REVIEWED),  # below the rung-2 count
    (EvidenceRung.WATCHING, 30, NONE),  # no P2 review report
    (EvidenceRung.EXPLORATORY, 0, NONE),
    (EvidenceRung.UNPROVEN, 5, NONE),  # a label lower than the evidence is refused too: one truth per count
])  # fmt: skip
def test_a_rung_that_its_own_count_and_reports_do_not_give_is_refused(rung, count, reports):
    first, last = (None, None) if count == 0 else (FIRST, LAST)
    with pytest.raises(ValueError, match="rung is not what"):
        VersionEvidence(V, rung, count, first, last, reports)


@pytest.mark.parametrize("missing", ["review", "sample_plan", "lower_bound", "second_window"])
def test_a_rung_3_label_with_one_report_missing_is_refused(missing):
    with pytest.raises(ValueError, match="rung is not what"):
        VersionEvidence(V, EvidenceRung.ESTABLISHED, 30, FIRST, LAST, replace(ESTABLISHED, **{missing: None}))


@pytest.mark.parametrize(("count", "first", "last"), [
    (1, LAST, FIRST),  # first after last
    (0, FIRST, None), (0, None, LAST), (3, None, None), (3, FIRST, None),
    (3, LAST, LAST),  # three sessions cannot fit in one day
])  # fmt: skip
def test_first_and_last_must_fit_the_count(count, first, last):
    with pytest.raises(ValueError, match="do not fit its count"):
        VersionEvidence(V, rung_for(count, NONE), count, first, last, NONE)


def test_good_evidence_at_every_rung_is_accepted():
    assert VersionEvidence(V, EvidenceRung.UNPROVEN, 0, None, None, NONE).rung is EvidenceRung.UNPROVEN
    assert VersionEvidence(V, EvidenceRung.EXPLORATORY, 1, LAST, LAST, NONE).rung is EvidenceRung.EXPLORATORY
    assert VersionEvidence(V, EvidenceRung.WATCHING, 30, FIRST, LAST, REVIEWED).rung is EvidenceRung.WATCHING
    assert VersionEvidence(V, EvidenceRung.ESTABLISHED, 30, FIRST, LAST, ESTABLISHED).rung is EvidenceRung.ESTABLISHED
