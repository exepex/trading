"""ChatGPT review 119 point 1 (the freeze plan, response 287): IV30 and Black-76 are not in v4's live path under this
freeze. One real day of G7's forecasts, M1's weather and G8's V6a report run with `Black76` and `PanelAtmIv30`
replaced by objects that raise if called, and give the same results as the unpatched run. V2-V5's implied baselines,
which would need them, come under a later freeze record."""

from datetime import date

import pytest

from fno.constants import V6_BIG_MOVE_1S
from fno.forecast.iv30 import PanelAtmIv30
from fno.forecast_scoring.v4.wiring import build_scoring
from fno.forecast_v4_rules.wiring import build_v4_forecasts
from fno.research_engine.implied_vol import Black76
from fno.weather.wiring import build_weather_days

DAY = date(2026, 10, 15)


def run_v4_day():
    g7 = build_v4_forecasts().values(DAY)
    weather = build_weather_days().values(DAY)
    report = build_scoring().question_report(V6_BIG_MOVE_1S)
    return g7, weather, report


def refuse(*args, **kwargs):
    raise AssertionError("an implied-volatility method was called on v4's live path")


def test_g7_m1_and_g8_run_without_any_implied_volatility(monkeypatch):
    plain = run_v4_day()
    for owner, name in ((Black76, "price"), (Black76, "implied_vol"), (Black76, "underlying"),
                        (PanelAtmIv30, "estimate")):  # fmt: skip
        monkeypatch.setattr(owner, name, refuse)
    assert run_v4_day() == plain


def test_the_refusing_patch_does_fire_when_called(monkeypatch):
    monkeypatch.setattr(PanelAtmIv30, "estimate", refuse)
    with pytest.raises(AssertionError, match="implied-volatility"):
        PanelAtmIv30(Black76(), 0.065).estimate(None, DAY)
