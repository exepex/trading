"""Story G7b completion, criterion 18: O1's `forecasts_v4_pack` step as built. It runs `forecast-v4 capture-pack` right
after G10's `v4_release`, is live only from its own `daily.live_from.forecasts_v4_pack` (null until the owner's go)
and commits only G7b's receipt folders."""

from datetime import date

from fno.constants import DAILY_RUN_STEPS, V4_PACK_FORECASTS_STEP
from fno.daily.steps import Alerted, CommandStep, LiveFrom
from fno.daily.wiring import FORECASTS_V4_PACK

from .test_candle_step import _built_steps


def test_the_step_runs_right_after_the_release_and_before_the_desk():
    order = list(DAILY_RUN_STEPS)
    assert order.index(V4_PACK_FORECASTS_STEP) == order.index("v4_release") + 1 < order.index("versions")


def test_the_built_step_is_not_live_and_commits_only_g7bs_receipts(monkeypatch):
    step = _built_steps(monkeypatch)[V4_PACK_FORECASTS_STEP]
    assert isinstance(step, Alerted) and isinstance(step.step, LiveFrom) and step.step.live_from is None
    command = step.step.step
    assert isinstance(command, CommandStep) and command.arguments(date(2026, 10, 26)) == FORECASTS_V4_PACK
    assert FORECASTS_V4_PACK == ("forecast-v4", "capture-pack")
    assert command.pathspecs == ("receipts/data/v4/records/live/", "receipts/data/v4/terms/",
                                 "receipts/data/v4/ratios/", "receipts/data/v4/outcomes/",
                                 "receipts/data/v4/diagnostics/")  # fmt: skip
