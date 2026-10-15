"""Story M1, criterion 5: the owner's thresholds (floors and base-rate multiples), `not scored`, the operative model."""

import pytest

from fno.constants import WeatherColour
from fno.weather import day as weather_day
from fno.weather.colour import weather_colour

from .fakes import ok, rows_from, weather_days

GREEN, AMBER, RED, NOT_SCORED = (WeatherColour.GREEN, WeatherColour.AMBER, WeatherColour.RED,
                                 WeatherColour.NOT_SCORED)  # fmt: skip
LOW = (0.02, 0.10)  # base rates b1, b5 with the floors binding (2.5 x 0.02 = 0.05 < 0.10)
EPS = 1e-9  # well above the colour's 1e-12 tolerance, far below a share's 1/750 step


@pytest.mark.parametrize("p1, p5, colour", [
    (0.10, 0.0, RED), (0.10 - EPS, 0.0, AMBER), (0.10 + EPS, 0.0, RED),  # p1 RED floor
    (0.0, 0.35, RED), (0.0, 0.35 - EPS, AMBER), (0.0, 0.35 + EPS, RED),  # p5 RED floor
    (0.06, 0.0, AMBER), (0.06 - EPS, 0.0, GREEN), (0.06 + EPS, 0.0, AMBER),  # p1 AMBER floor
    (0.0, 0.20, AMBER), (0.0, 0.20 - EPS, GREEN), (0.0, 0.20 + EPS, AMBER),  # p5 AMBER floor
])  # fmt: skip
def test_each_condition_at_just_under_and_just_over_its_floor(p1, p5, colour):
    assert weather_colour(p1, p5, *LOW) == colour


def test_the_multiple_binds_when_the_base_rate_is_high():
    b1, b5 = 0.06, 0.20  # 2.5 x b = 0.15 and 0.50; 1.5 x b = 0.09 and 0.30
    assert [weather_colour(p, 0.0, b1, b5) for p in (0.15, 0.15 - EPS, 0.09, 0.09 - EPS)] == [RED, AMBER, AMBER, GREEN]
    assert [weather_colour(0.0, p, b1, b5) for p in (0.50, 0.50 - EPS, 0.30, 0.30 - EPS)] == [RED, AMBER, AMBER, GREEN]
    assert weather_colour(0.12, 0.0, b1, b5) == AMBER  # above the 10% floor, under 2.5 x b1


@pytest.mark.parametrize("missing", range(4))
def test_any_missing_figure_is_not_scored_never_a_colour(missing):
    figures = [0.5, 0.9, 0.02, 0.10]
    figures[missing] = None
    assert weather_colour(*figures) == NOT_SCORED


def _days():
    return weather_days(rows_from([0.001] * 600))


def test_the_operative_colour_is_the_model_and_v0_when_the_constant_says_so(monkeypatch):
    days = _days()
    d = days.days[-10]  # inside the calendar: v0 has its event window
    values = days.values(d)
    values["weather_vix_v1"] = {q: ok(0.5) for q in values["weather_vix_v1"]}  # the model: RED
    assert days.colours(d, values) == (RED, RED, GREEN)
    monkeypatch.setattr(weather_day, "WEATHER_OPERATIVE_MODEL", "weather_checklist_v0")
    assert days.colours(d, values) == (GREEN, RED, GREEN)


def test_the_record_names_the_operative_model_and_says_not_yet_proven():
    public = _days().day(_days().days[-1], "live", "", {}).public
    assert (public["operative"], public["proof"]) == ("weather_vix_v1", weather_day.NOT_YET_PROVEN)
    assert public["proof"].startswith("not yet proven")


def test_a_share_exactly_at_a_multiple_reaches_it():
    b5 = 100 / 750  # 1.5 x b5 = 150/750 = 0.2 exactly on paper, not in floating point
    assert weather_colour(0.0, 150 / 750, 0.02, b5) == AMBER and weather_colour(0.0, 149 / 750, 0.02, b5) == GREEN


def test_a_not_scored_record_names_each_missing_figure():
    days = weather_days(rows_from([0.001] * 400))  # under 500 resolved: nothing eligible yet
    public = days.day(days.days[-10], "live", "", {}).public
    assert public["colour"] == "not scored"
    assert public["status"].startswith("not scored: v6_abs_move_2pct_next_session p not_eligible, ")
    assert public["status"].count("not_eligible") == 4
