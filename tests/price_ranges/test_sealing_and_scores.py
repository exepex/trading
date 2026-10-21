"""G13b criteria 6-7: sealing by GitHub's push time (at the deadline sealed, one second later late, no evidence late),
and the scores: QS, coverage and Brier by hand, a point mass's coverage "n/a", late rows counted never scored,
comparisons equal to G4's bootstrap, groups never pooled, and the notes."""

import math
from datetime import date, datetime, timedelta

import pytest

from fno.forecast_scoring.block_bootstrap import compare
from fno.models import IST
from fno.price_distribution.scoring import pinball
from fno.price_ranges.constants import BRIER_NOTE, LEVELS, TAU_NOTE
from fno.price_ranges.scores import comparison_seed, group_scores, resolved, score_report
from fno.price_ranges.sealing import SealCheck
from tests.price_ranges.builders import CALENDAR

DAY = date(2026, 10, 16)
DEADLINE = datetime(2026, 10, 19, 9, 15, tzinfo=IST)  # Monday after Friday the 16th
LQ = (-0.02, -0.01, 0.0, 0.01, 0.02)


@pytest.mark.parametrize(("pushed", "late"), [(DEADLINE, False), (DEADLINE + timedelta(seconds=1), True),
                                              (DEADLINE - timedelta(hours=17), False)])  # fmt: skip
def test_a_live_record_is_sealed_only_when_pushed_by_its_deadline(pushed, late):
    seal = SealCheck(lambda path: pushed, CALENDAR).seal("receipts/x.sha256", DAY)
    assert (seal.late, seal.deadline, seal.sealed_at) == (late, DEADLINE, pushed)


def test_no_push_evidence_is_late_never_sealed():
    def unknown(path):
        raise RuntimeError("no GitHub token")

    seal = SealCheck(unknown, CALENDAR).seal("receipts/x.sha256", DAY)
    assert seal.late and seal.sealed_at is None and "push time unknown" in seal.reason


def row(forecaster="implied", shift=0.0, p_up=0.6, horizon="N1"):
    values = (0.0,) * 5 if forecaster == "no_change" else tuple(v + shift for v in LQ)
    return {"forecaster": forecaster, "horizon": horizon, "status": "ok", "target_day": "2026-10-19", "s_ref": 100.0,
            "p_up": p_up} | {f"lq{round(t * 100):02d}": v for t, v in zip(LEVELS, values, strict=True)}  # fmt: skip


def record(day="2026-10-16", label="backfill_eod", underlying="NIFTY", rows=None):
    return {"day": day, "label": label, "underlying": underlying, "issue": "1545", "rows": rows or [row()]}


def test_qs_coverage_and_brier_by_hand():
    found, late = resolved([(record(), True)], lambda u, d: 101.5)
    (group,) = group_scores(found)
    y = found[0][2]
    assert group["mean_qs"] == pytest.approx(2 / 5 * sum(pinball(t, y, q) for t, q in zip(LEVELS, LQ, strict=True)))
    assert (group["inside_50"], group["inside_90"]) == (0.0, 1.0)  # +1.49%: outside the +-1% band, inside +-2%
    assert group["brier_up"] == pytest.approx((0.6 - 1) ** 2) and late == 0


def test_an_equal_close_is_not_up_and_the_point_mass_has_no_band():
    found, _ = resolved([(record(rows=[row("no_change", p_up=0.5)]), True)], lambda u, d: 100.0)
    (group,) = group_scores(found)
    assert group["brier_up"] == 0.25 and group["inside_50"] is None and group["inside_90"] is None
    assert group["mean_qs"] == 0.0  # its absolute log error: the close did not move


def test_a_late_live_record_is_counted_never_scored_and_an_unresolved_row_is_skipped():
    found, late = resolved([(record(label="live"), False), (record(), True)], lambda u, d: None)
    assert (found, late) == ([], 1)


def test_comparisons_are_g4s_bootstrap_with_the_comparisons_own_seed():
    days = [(date(2025, 1, 1) + timedelta(days=i)).isoformat() for i in range(50)]
    records = [(record(d, rows=[row(), row("rv20", shift=0.004)]), True) for d in days]
    out = score_report(records, lambda u, d: 100.5)
    first = next(c for c in out["comparisons"] if c["second"] == "rv20")
    y = math.log(1.005)
    diffs = [2 / 5 * sum(pinball(t, y, q) - pinball(t, y, q + 0.004) for t, q in zip(LEVELS, LQ, strict=True))] * 50
    direct = compare(diffs, comparison_seed("backfill_eod", "NIFTY", "1545", "N1", "rv20"))
    assert (first["n"], first["tested"]) == (50, True) and first["p_value"] == direct.p_value
    assert TAU_NOTE in out["notes"] and BRIER_NOTE in out["notes"]


def test_labels_underlyings_and_horizons_are_never_pooled():
    records = [(record(), True), (record(label="live"), True), (record(underlying="BANKNIFTY"), True),
               (record(rows=[row(horizon="N3")]), True)]  # fmt: skip
    groups = group_scores(resolved(records, lambda u, d: 100.5)[0])
    assert len(groups) == 4 and all(g["n"] == 1 for g in groups)
