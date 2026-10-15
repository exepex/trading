"""Story G10: the day's clock, the "moved after cutoff" rule and its frozen X (computed by
`tools/v4_moved_after_cutoff.py` from A16b's checked 2020-26 closes; the committed result must equal `terms`)."""

import json
import math
from datetime import time
from pathlib import Path

import pytest

from fno.forecast_v4 import terms
from fno.forecast_v4.cutoff_move import cutoff_move, moved_after_cutoff, nearest_rank

RESULT = Path(__file__).resolve().parents[2] / "research" / "forecasts" / "v4_moved_after_cutoff.json"


def test_the_days_clock():
    clock = (terms.V4_CAPTURE_START, terms.V4_PACK_WINDOW_END, terms.V4_DEADLINE, terms.V4_COMMON_SNAPSHOT)
    assert clock == (time(14, 30), time(14, 40), time(15, 10), time(15, 15))


def test_the_move_and_the_strict_flag():
    assert cutoff_move(24000.0, 24000.0) == 0.0
    assert cutoff_move(24000.0, 23900.0) == pytest.approx(abs(math.log(23900 / 24000)))
    x = 0.006
    assert not moved_after_cutoff(x, x) and moved_after_cutoff(x + 1e-12, x)
    with pytest.raises(ValueError):
        cutoff_move(0.0, 1.0)


def test_nearest_rank_has_no_interpolation():
    values = [float(v) for v in range(1, 21)]  # 20 values: ceil(0.95 x 20) = 19th smallest
    assert nearest_rank(values) == 19.0 and nearest_rank([5.0]) == 5.0
    assert nearest_rank(list(range(1, 101))) == 95  # ceil(95.0) = 95th


def test_the_frozen_x_equals_the_committed_tool_result():
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["x"] == terms.MOVED_AFTER_CUTOFF_X and result["sample_count"] == terms.MOVED_AFTER_CUTOFF_SAMPLE
    assert result["source"]["table_revision"] == terms.MOVED_AFTER_CUTOFF_SOURCE
    assert result["quantile"] == 0.95 and result["first_session"] == "2020-01-02"
    assert result["flagged_in_history"] == 83  # of 1,661 strictly above X
