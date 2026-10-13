"""Judge 47: the forecast protocol protects behaviour, not library bytes. Every panel day's IV30 (value, flag,
expiries) and trailing RV20 must equal the committed golden file, whatever refactor the shared code goes through. The
hand-worked values (IV30 14.4937 and 13.0 flagged; RV 15.8745 and 34.0470; the holiday and muhurat window) are the
fixture goldens in test_iv30.py and test_targets.py."""

import pytest

from fno.config import ROOT, load_app_config
from fno.forecast.golden import GOLDEN_FILE, differences, read_golden
from fno.forecast.wiring import forecast_golden_rows

YEARS = list(range(2019, 2027))


@pytest.fixture(scope="module")
def golden():
    return read_golden((ROOT / GOLDEN_FILE).read_text(encoding="utf-8"))


def test_every_panel_day_equals_the_golden_values(golden):
    assert len(golden) >= 1900
    assert differences(golden, forecast_golden_rows(load_app_config(), YEARS)) == []


def test_the_golden_file_has_values_on_almost_every_day(golden):
    assert sum(r["iv30_points"] == "" for r in golden) <= 2
    assert all(r["trailing_rv20_points"] for r in golden)
    flagged = sum(r["iv30_flagged"] == "true" for r in golden)
    assert 200 < flagged < 300  # 13% of days, as the protocol states


def test_a_changed_number_flag_or_day_is_caught(golden):
    first = dict(golden[0])
    moved = [first | {"iv30_points": repr(float(first["iv30_points"]) + 1e-9)}] + golden[1:]
    assert differences(golden, moved) and "iv30_points" in differences(golden, moved)[0]
    flipped = [first | {"iv30_flagged": "true" if first["iv30_flagged"] == "false" else "false"}] + golden[1:]
    assert differences(golden, flipped)
    assert differences(golden, golden[1:]) == [f"{first['date']}: missing from the recomputation"]
    assert differences(golden, golden) == []
