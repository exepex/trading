"""Story G6 revision 6 (ChatGPT review 101): V7's own VIX null. No measured rule holds V7's size across VIX regimes,
so V7 is descriptive-only in v4; V6b's busy-regime stress is disclosed."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from fno.constants import V4_OPEN, V4_SLOT_RULES, V6_BIG_MOVE_5S, V7_VIX_UP_5S
from fno.forecast_v4.family import MemberResult, judge_family
from fno.forecast_v4.stop_rule import forecasting_test
from fno.forecast_v4.terms import DESCRIPTIVE_ONLY, FAMILY, LOOK_STOP_REVIEW
from fno.models import IST

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import v4_vix_null as vix  # noqa: E402

DATA = json.loads((ROOT / "research/forecasts/v4_vix_null.json").read_text(encoding="utf-8"))
AT = datetime(2027, 5, 31, 18, 0, tzinfo=IST)


def test_no_measured_rule_holds_v7_size_across_regimes():
    rules = {r["rule"].split(",")[0] for r in DATA["rows"]}
    assert rules == {"R0 borrowed V6b", "R1 own", "R2 own"} and DATA["series"] == 200_000
    assert not any(vix.within(r) for r in DATA["rows"])


def test_v7_own_rule_holds_on_the_full_period_and_fails_only_inside_one_regime():
    own = [r for r in DATA["rows"] if r["rule"] == "R1 own, no gate"]
    for r in own:
        full = [rate for name, (rate, _) in r["look 1"]["by_null"].items() if name.startswith("full")]
        assert max(full) <= 0.0016 and r["look 1"]["size"] > 0.05  # fine overall, 5-17% inside a calm year


def test_committed_markdown_matches_the_data():
    assert (ROOT / "research/forecasts/v4_vix_null.md").read_text(encoding="utf-8") == vix.markdown(DATA["rows"])


def test_v7_is_descriptive_only_never_claims_and_never_counts_in_test_a():
    assert {V7_VIX_UP_5S} == DESCRIPTIVE_ONLY
    v7 = (V7_VIX_UP_5S, V4_SLOT_RULES)
    decision = judge_family(LOOK_STOP_REVIEW, AT, {v7: MemberResult(1e-9, True, True)})
    member = next(m for m in decision.members if (m.question, m.slot) == v7)
    assert (member.judged, member.p_used, member.verdict, member.futile) == (False, 1.0, V4_OPEN, False)
    v6b = (V6_BIG_MOVE_5S, V4_SLOT_RULES)
    futile = judge_family(LOOK_STOP_REVIEW, AT, {v6b: MemberResult(0.9, False, True)})
    assert forecasting_test(futile.members, {v6b, v7}) == "no"  # V7 neither claims nor blocks the "no"
    assert len(FAMILY) == 15


def test_v6b_busy_regime_stress_is_recorded_and_fails():
    data = json.loads((ROOT / "research/forecasts/v4_brier_busy_stress.json").read_text(encoding="utf-8"))
    assert max(r["rate"] for r in data["rows"] if r["kind"] == "claim") > 0.4
    assert max(r["rate"] for r in data["rows"] if r["kind"] == "futility") > 0.9
