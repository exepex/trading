"""Protocol v4 section 10 (freeze checklist, response 157): no v4 output uses implied volatility. One real day of G7's
capture, M1's weather and G8's report is made twice, the second time with every implied-volatility path (Black-76,
the ATM 30-day estimator and its feature) patched to raise; the outputs are identical."""

from dataclasses import asdict
from datetime import date

import pytest

from fno.constants import V6_BIG_MOVE_1S, V6_BIG_MOVE_5S
from fno.forecast.iv30 import AtmIv30Feature, PanelAtmIv30
from fno.forecast_scoring.v4.render import report_json
from fno.forecast_scoring.v4.scoring import QUESTIONS, STATUS_SCORED
from fno.forecast_scoring.v4.wiring import build_day_counts, build_scoring
from fno.forecast_v4_rules.records import LIVE
from fno.forecast_v4_rules.wiring import build_v4_forecasts
from fno.research_engine.implied_vol import Black76, ImpliedVolModel
from fno.weather.records import red_share
from fno.weather.wiring import build_records, build_weather_days
from tests.forecast_scoring_v4.conftest import no_v4_drive_records  # noqa: F401 (the one fixture, shared)

DAY = date(2026, 10, 15)  # a real session with its committed close
MADE_AT = "2026-10-15T09:00:00+00:00"
pytestmark = pytest.mark.usefixtures("no_v4_drive_records")  # the point is no implied vol, not the records


class ImpliedVolUsed(AssertionError):
    pass


def _raise(*_args, **_kwargs):
    raise ImpliedVolUsed


def _make_implied_vol_raise(monkeypatch):
    for owner, name in ((ImpliedVolModel, "__init__"), (ImpliedVolModel, "implied_vol"), (Black76, "price"),
                        (Black76, "underlying"), (PanelAtmIv30, "__init__"), (PanelAtmIv30, "estimate"),
                        (AtmIv30Feature, "value")):  # fmt: skip
        monkeypatch.setattr(owner, name, _raise)


@pytest.fixture
def iv_raises(monkeypatch):
    _make_implied_vol_raise(monkeypatch)


def _outputs() -> dict:
    g7 = build_v4_forecasts(DAY).records(DAY, LIVE, MADE_AT)
    weather = build_weather_days()
    red = red_share(build_records().live_colours_before(DAY), weather.colours(DAY)[0])
    day = weather.day(DAY, LIVE, MADE_AT, red)
    scoring = build_scoring()
    report = report_json(
        [scoring.question_report(q) for q in QUESTIONS], frozen=False, as_of=DAY.isoformat(), days=build_day_counts(DAY)
    )
    return {
        "g7": {key: asdict(row) for key, row in g7.items()},
        "weather": (day.public, {key: asdict(row) for key, row in day.rows.items()}),
        "g8": report,
    }


def test_the_patch_reaches_every_implied_vol_path(iv_raises):
    with pytest.raises(ImpliedVolUsed):
        Black76()
    with pytest.raises(ImpliedVolUsed):
        PanelAtmIv30(object(), 0.065)


def test_g7_m1_and_g8_give_identical_outputs_when_implied_vol_raises(monkeypatch):
    plain = _outputs()
    scored = {q["question"] for q in plain["g8"]["questions"] if q["status"] == STATUS_SCORED}
    assert plain["g7"] and plain["weather"][1] and {V6_BIG_MOVE_1S, V6_BIG_MOVE_5S} <= scored  # a real, scored day
    with monkeypatch.context() as patched:
        _make_implied_vol_raise(patched)
        assert _outputs() == plain
