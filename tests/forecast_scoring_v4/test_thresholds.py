"""Story G8 criterion 5: the frozen tools are called with the member's n and the look's rate (the claim tool divides
by 15 itself), and the Brier tool's look names are mapped; one real call below 12 batches answers 0.0 at once."""

import sys
import types
from pathlib import Path

from fno.constants import V1_RV_1S, V6_BIG_MOVE_1S
from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds, Thresholds
from fno.forecast_v4.terms import LOOK_SETTLE_DATE, LOOK_STOP_REVIEW

TOOLS = Path(__file__).resolve().parents[2] / "tools"


def fake_tools(monkeypatch, calls):
    claim = types.SimpleNamespace(claim_threshold=lambda q, n, rate: calls.append(("claim", q, n, rate)) or 1e-9)
    futility = types.SimpleNamespace(futility_threshold=lambda q, n: calls.append(("futility", q, n)) or 1e-5)
    bands = types.SimpleNamespace(operative_thresholds=lambda q, n, band: calls.append(("bands", q, n, band)) or {
        "claim": {"look 1": 1e-4, "look 2": 2e-4}, "futility": 3e-3})  # fmt: skip
    for name, module in (("v4_claim_thresholds", claim), ("v4_futility_study", futility), ("v4_brier_bands", bands)):
        monkeypatch.setitem(sys.modules, name, module)


def test_point_members_use_the_claim_and_futility_tools_with_the_look_rate(monkeypatch):
    calls = []
    fake_tools(monkeypatch, calls)
    found = FrozenToolThresholds(TOOLS).thresholds(V1_RV_1S, LOOK_STOP_REVIEW, 130, 128, None)
    assert found == Thresholds(1e-9, 1e-5)
    assert calls == [("claim", V1_RV_1S, 130, 0.02), ("futility", V1_RV_1S, 128)]


def test_brier_members_use_the_band_tool_and_its_look_names(monkeypatch):
    calls = []
    fake_tools(monkeypatch, calls)
    found = FrozenToolThresholds(TOOLS).thresholds(V6_BIG_MOVE_1S, LOOK_SETTLE_DATE, 140, 140, (8, 12))
    assert found == Thresholds(2e-4, 3e-3) and calls == [("bands", V6_BIG_MOVE_1S, 140, (8, 12))]


def test_the_real_claim_tool_answers_zero_below_12_batches():
    found = FrozenToolThresholds(TOOLS).thresholds(V1_RV_1S, LOOK_STOP_REVIEW, 59, 59, None)
    assert found == Thresholds(0.0, 0.0)
