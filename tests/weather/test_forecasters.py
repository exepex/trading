"""Story M1, criteria 3 and 4: both `WeatherModel`s on hand-computed fixtures, their 499/500 windows, a missing VIX
close and the look-ahead test."""

import math
from dataclasses import replace

import pytest

from fno.forecast_v4_rules.baselines import MISSING, NOT_ELIGIBLE, OK
from fno.forecast_v4_rules.series import Outcome
from fno.weather.constants import WeatherColour
from fno.weather.v0_live import ColourBaseRate
from fno.weather.vix_scaled import VixScaledWeather, daily_scale

from .fakes import rows_from, sessions

RED, GREEN, AMBER = WeatherColour.RED, WeatherColour.GREEN, WeatherColour.AMBER


class Colours:
    """A v0 checklist double: a fixed colour per day."""

    def __init__(self, colours):
        self.colours = colours

    def colour(self, d):
        return self.colours.get(d)


def _v0(count: int, today=RED):
    """`count` outcomes, resolved on the day after their own; every 4th day RED (big move 1 on 1 of its 2)."""
    days = sessions(count + 2)
    colours = {d: (RED if n % 4 == 0 else GREEN) for n, d in enumerate(days[:count])} | {days[-1]: today}
    outcomes = [Outcome(d, int(n % 8 == 0), days[n + 1]) for n, d in enumerate(days[:count])]
    return ColourBaseRate(Colours(colours), {1: outcomes}), days[-1]


def test_v0_probability_is_the_share_among_sessions_of_the_same_colour():
    rate, d = _v0(500)
    assert rate.forecast(d, 1).value == pytest.approx(63 / 125)  # 125 RED days (n % 4 == 0), 63 with n % 8 == 0
    rate, d = _v0(500, today=GREEN)
    assert rate.forecast(d, 1).value == 0.0


def test_v0_needs_500_resolved_and_a_colour_absent_from_the_window_is_missing():
    rate, d = _v0(499)
    assert rate.forecast(d, 1).status == NOT_ELIGIBLE
    rate, d = _v0(500, today=AMBER)
    assert rate.forecast(d, 1).status == MISSING
    rate, d = _v0(500, today=None)  # v0 has no colour for the day
    assert rate.forecast(d, 1).status == MISSING


def _returns(count: int, big_every: int = 10, small: float = 0.012, big: float = 0.03) -> list[float]:
    return [big if n % big_every == 0 else small for n in range(count)]


def test_vix_model_equals_a_hand_computation():
    rows = rows_from(_returns(600))  # constant VIX 16: z x s_d is the return itself
    model, d = VixScaledWeather(rows), rows[-1].day
    # V6a windows k = 1..598 resolve on rows[k+1] < d=rows[600]: 598, the last 598 (fewer than 750)
    assert model.forecast(d, 1).value == pytest.approx(sum(n % 10 == 0 for n in range(1, 599)) / 598)
    # V6b windows k = 1..594 hold returns k..k+4; each 5 in a row holds one 3% day or not
    big5 = sum(any(m % 10 == 0 for m in range(k, k + 5)) for k in range(1, 595))
    assert model.forecast(d, 5).value == pytest.approx(big5 / 594)


def test_a_doubled_vix_today_doubles_every_standardized_move():
    rows = rows_from(_returns(600), [16.0] * 600 + [32.0])
    rows = [*rows[:-2], replace(rows[-2], vix=32.0), rows[-1]]  # the session before d priced twice the volatility
    assert VixScaledWeather(rows).forecast(rows[-1].day, 1).value == 1.0  # 1.2% x 2 = 2.4% >= 2%


def test_vix_model_needs_500_resolved_windows():
    rows = rows_from(_returns(600))
    model = VixScaledWeather(rows)
    assert model.forecast(rows[501].day, 1).status == NOT_ELIGIBLE  # windows k = 1..499
    assert model.forecast(rows[502].day, 1).status == OK
    assert model.forecast(rows[505].day, 5).status == NOT_ELIGIBLE  # windows k = 1..499 of 5 returns
    assert model.forecast(rows[506].day, 5).status == OK


def test_the_window_keeps_the_most_recent_750():
    rows = rows_from([0.03] * 300 + [0.001] * 800)  # the big days are older than the last 750 windows
    assert VixScaledWeather(rows).forecast(rows[-1].day, 1).value == 0.0


def test_a_missing_vix_close_for_the_previous_session_gives_missing():
    rows = rows_from(_returns(600))
    rows = [*rows[:-2], replace(rows[-2], vix=None), rows[-1]]
    assert VixScaledWeather(rows).forecast(rows[-1].day, 1).status == MISSING
    assert daily_scale(None) is None and daily_scale(16.0) == pytest.approx(0.16 / math.sqrt(252))


def test_no_input_after_the_cutoff_changes_a_forecast():
    rows = rows_from(_returns(700))
    d = rows[650].day
    later = [*rows[:650], *(replace(r, close=r.close * 1.3, vix=80.0) for r in rows[650:])]  # d's close onwards
    for h in (1, 5):
        assert VixScaledWeather(rows).forecast(d, h) == VixScaledWeather(later).forecast(d, h)
    assert VixScaledWeather(rows).forecast(rows[651].day, 1) != VixScaledWeather(later).forecast(rows[651].day, 1)


def test_each_window_is_scaled_by_the_vix_of_its_own_previous_session():
    rows = rows_from([0.012] * 600, [8.0] + [16.0] * 600)  # only window k = 1 is scaled by half: z doubles
    assert VixScaledWeather(rows).forecast(rows[-1].day, 1).value == pytest.approx(1 / 598)


def test_a_standardized_move_scaled_exactly_to_2pct_counts():
    model = VixScaledWeather(rows_from([0.0] * 600))
    scale = daily_scale(16.0)
    model.windows[1] = [replace(w, largest=0.02 / scale) for w in model.windows[1]]  # z x s_d = 0.02 exactly
    assert (0.02 / scale) * scale == 0.02
    assert model.forecast(model.days[-1], 1).value == 1.0
