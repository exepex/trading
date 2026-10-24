"""Story G7b completion, part f, criterion 17 (the rule): V2's and V3's intraday outcome, the sum of A16's live
intraday `RV_s` over the horizon; a void session voids, a missing one leaves the day unresolved."""

from datetime import date

import pytest

from fno.constants import V2_RV_5S, V3_RV_20S
from fno.forecast_v4_rules.intraday_series import INTRADAY_SERIES, intraday_horizon_sum

AHEAD = [date(2026, 10, 19), date(2026, 10, 21), date(2026, 10, 22)]


def test_the_series_keys_name_their_questions():
    assert INTRADAY_SERIES == {"v2_rv_next_5_sessions/intraday": V2_RV_5S, "v3_rv_next_20_sessions/intraday": V3_RV_20S}


def test_good_the_sum_over_the_horizon():
    rows = {AHEAD[0]: 1e-5, AHEAD[1]: 2e-5, AHEAD[2]: 0.0, date(2026, 10, 23): 9.0}  # zero kept, later rows unused
    total, void = intraday_horizon_sum(rows, AHEAD)
    assert total == pytest.approx(3e-5) and void is False


def test_bad_a_void_session_voids_the_day():
    assert intraday_horizon_sum({AHEAD[0]: 1e-5, AHEAD[1]: None, AHEAD[2]: 2e-5}, AHEAD) == (None, True)


def test_boundary_a_session_without_its_row_leaves_the_day_unresolved():
    assert intraday_horizon_sum({AHEAD[0]: 1e-5, AHEAD[1]: 2e-5}, AHEAD) is None


def test_empty_rows_are_unresolved():
    assert intraday_horizon_sum({}, AHEAD) is None
