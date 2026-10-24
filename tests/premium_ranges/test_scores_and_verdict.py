"""Criteria 3 and 3b: hand scores (below, inside, above), a point baseline's score is its absolute error, the floor,
unscored reasons, session-first averaging, and the verdict's four answers read only at the fixed looks."""

from datetime import date

import numpy as np
import pytest

from fno.premium_ranges.constants import (
    BEATS_CARRY,
    COVERS_WELL,
    DECAY_ONLY,
    FAILS,
    LEVELS,
    NO_CHANGE,
    NO_NEXT_CHAIN,
    NO_NEXT_QUOTE,
    NOT_YET,
    OTHER_SOURCE,
    RULE,
)
from fno.premium_ranges.report import Issued, underlying_report
from fno.premium_ranges.scores import Scored, days_bucket, delta_bucket, method_scores, score_record
from fno.premium_ranges.sessions import Session, looks, session_of, summary, verdict

from .builders import contract, expiry, g13_record

E1 = date(2026, 11, 23)
QUANTILES = (80.0, 90.0, 100.0, 110.0, 120.0)


CASES = [(70.0, 0, 0), (85.0, 0, 1), (100.0, 1, 1), (115.0, 0, 1), (130.0, 0, 0)]  # below to above


@pytest.mark.parametrize(("outcome", "inside_50", "inside_90"), CASES)
def test_hand_quantile_scores_and_coverage(outcome, inside_50, inside_90):
    qs, relative, i50, i90 = method_scores(QUANTILES, outcome, 50.0)
    hand = 2 / 5 * sum(max(t * (outcome - q), (t - 1) * (outcome - q)) for t, q in zip(LEVELS, QUANTILES, strict=True))
    assert qs == pytest.approx(hand) and relative == pytest.approx(hand / 50.0) and (i50, i90) == (inside_50, inside_90)


def test_a_point_scores_its_absolute_error_and_the_floor_keeps_cheap_premiums_in_check():
    qs, relative, _, _ = method_scores((10.0,) * 5, 13.0, 0.5)
    assert qs == pytest.approx(3.0) and relative == pytest.approx(3.0 / 2.0)


def test_buckets():
    assert [delta_bucket(x) for x in (0.0, 0.1499, 0.15, 0.35, 0.65, 1.0)] == [0, 0, 1, 2, 3, 3]
    assert [days_bucket(x) for x in (2, 7, 8, 21, 22, 90)] == [0, 0, 1, 1, 2, 2]


def issued(rows) -> dict:
    return {"day": "2026-10-16", "next_session": "2026-10-19", "source": "nse", "rows": rows}


def row(strike=23000.0, side="CE", mid=100.0) -> dict:
    return {"expiry": E1.isoformat(), "strike": strike, "side": side, "mid": mid, "delta": 0.5, "days": 38,
            RULE: list(QUANTILES), DECAY_ONLY: [98.0] * 5, NO_CHANGE: [mid] * 5}  # fmt: skip


def test_unscored_rows_are_counted_by_reason():
    quotes = [contract(23000.0, "CE", 104.0), contract(22500.0, "PE", 30.0, two_sided=False)]
    nxt = g13_record(date(2026, 10, 19), [expiry(E1, 35, quotes)])
    scored, missing = score_record(issued([row(), row(22500.0, "PE"), row(22000.0, "PE")]), nxt)
    assert len(scored) == 1 and missing == {NO_NEXT_QUOTE: 2}
    assert scored[0].by_method[NO_CHANGE][0] == pytest.approx(4.0)
    assert score_record(issued([row()]), None)[1] == {NO_NEXT_CHAIN: 1}
    assert score_record(issued([row()]), {**nxt, "source": "groww"})[1] == {OTHER_SOURCE: 1}


def scored(qs, inside_50, inside_90, decay_qs) -> Scored:
    return Scored(2, 2, {RULE: (qs, qs, inside_50, inside_90), DECAY_ONLY: (decay_qs, decay_qs, 0, 0),
                         NO_CHANGE: (decay_qs, decay_qs, 0, 0)})  # fmt: skip


def test_a_day_of_100_contracts_weighs_the_same_as_a_day_of_10():
    big = session_of("a", [scored(1.0, 1, 1, 2.0)] * 100)
    small = session_of("b", [scored(3.0, 0, 0, 2.0)] * 10)
    assert summary([big, small])["methods"][RULE]["mean_qs_rs"] == 2.0  # a row-weighted mean would give 1.18


def sessions(n, inside_90, inside_50, difference) -> list[Session]:
    """`n` sessions alternating around the given means (so intervals are narrow but not zero)."""
    out = []
    for i in range(n):
        wobble = 0.01 if i % 2 else -0.01
        means = {RULE: (2.0 + difference + wobble, 0.0, inside_50 + wobble, inside_90 + wobble),
                 DECAY_ONLY: (2.0, 0.0, 0.0, 0.0), NO_CHANGE: (1.0, 0.0, 0.0, 0.0)}  # fmt: skip
        out.append(Session(f"d{i:03d}", means, 10))
    return out


def test_the_verdicts_four_answers():
    assert (verdict(sessions(60, 0.90, 0.50, -0.5))["coverage"], verdict(sessions(60, 0.90, 0.50, -0.5))["carry"]) == (
        COVERS_WELL, BEATS_CARRY)  # fmt: skip
    bad = verdict(sessions(60, 0.70, 0.50, 0.5))
    assert (bad["coverage"], bad["carry"]) == (FAILS, FAILS)
    noise = np.random.default_rng(7).normal(size=(60, 3))
    noise -= noise.mean(axis=0)  # centred, so every interval straddles its edge
    wide = [Session(f"d{i:03d}", {RULE: (2.0 + n[0], 0, 0.5 + 0.3 * n[1], 0.9 + 0.1 * n[2]),
                                  DECAY_ONLY: (2.0, 0, 0, 0), NO_CHANGE: (2.0, 0, 0, 0)}, 10)
            for i, n in enumerate(noise)]  # fmt: skip
    assert (verdict(wide)["coverage"], verdict(wide)["carry"]) == (NOT_YET, NOT_YET)


def test_the_verdict_is_read_only_at_60_120_and_250_on_each_looks_first_sessions():
    assert looks(sessions(59, 0.9, 0.5, -0.5)) == {"verdicts": {}, "status": "next look at 60 scored sessions"}
    at_100 = looks(sessions(60, 0.9, 0.5, -0.5) + sessions(40, 0.2, 0.2, 1.0))
    assert list(at_100["verdicts"]) == ["60"] and at_100["verdicts"]["60"]["coverage"] == COVERS_WELL
    assert at_100["status"] == "next look at 120 scored sessions"
    assert list(looks(sessions(250, 0.9, 0.5, -0.5))["verdicts"]) == ["60", "120", "250"]


def test_an_issue_whose_next_session_is_ahead_is_pending_not_unscored():
    entry = Issued({"day": "2026-10-16", "next_session": "2026-10-19", "source": "nse", "rows": [row()]}, None, True)
    report = underlying_report([entry], date(2026, 10, 18))
    assert report["pending_days"] == ["2026-10-16"] and report["unscored"] == {} and report["late_issues"] == 0
    later = underlying_report([entry], date(2026, 10, 20))
    assert later["unscored"] == {NO_NEXT_CHAIN: 1} and later["late_issues"] == 1 and later["sessions"] == 0
