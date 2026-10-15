"""Owner's item E, option 2 (orchestrator decision 69): a window with more than 10% 2% days gives no verdict."""

from fno.forecast_v4.confirmatory import crash_dominated, event_band


def test_twelve_of_125_is_judged_and_thirteen_is_cut():
    assert not crash_dominated(12, 125) and crash_dominated(13, 125)


def test_the_cut_is_strict_at_exactly_ten_percent():
    assert not crash_dominated(25, 250) and crash_dominated(26, 250)


def test_the_13_plus_band_is_reachable_only_from_130_outcomes():
    assert event_band(13) == (13, None)
    assert crash_dominated(13, 129) and not crash_dominated(13, 130)
