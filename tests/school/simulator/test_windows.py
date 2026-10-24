"""Which history may be practised (MS-SIM-a, 7.1 item 2)."""

import re
from datetime import date
from pathlib import Path

import pytest

from fno.school.constants import RoadCode
from fno.school.simulator.constants import PracticeRefusal
from fno.school.simulator.windows import PRACTICE_WINDOWS, PracticeWindows

REGISTER = Path(__file__).resolve().parents[3] / "research" / "DATA_SPEND.md"
OK = PracticeRefusal.NOT_IN_DATA_SPEND


def test_a_spent_day_may_be_practised_and_the_day_after_the_window_may_not():
    windows = PracticeWindows()
    assert windows.check(RoadCode.NIFTY_MONTHLY, date(2024, 3, 4)) is None
    assert windows.check(RoadCode.NIFTY_MONTHLY, date(2026, 10, 12)) is None  # boundary: the last day
    assert windows.check(RoadCode.NIFTY_MONTHLY, date(2026, 10, 13)) is OK  # the first forward capture: fresh


def test_each_road_has_its_own_first_and_last_day():
    windows = PracticeWindows()
    assert windows.check(RoadCode.NIFTY_WEEKLY, date(2026, 10, 9)) is None
    assert windows.check(RoadCode.NIFTY_WEEKLY, date(2026, 10, 12)) is OK  # the weekly register row ends 9 Oct
    assert windows.check(RoadCode.NIFTY_WEEKLY, date(2019, 1, 31)) is OK
    assert windows.check(RoadCode.BANKNIFTY_MONTHLY, date(2018, 12, 31)) is OK
    assert windows.check(RoadCode.BANKNIFTY_MONTHLY, date(2019, 1, 1)) is None


@pytest.mark.parametrize("road", [RoadCode.FINNIFTY_MONTHLY, RoadCode.MIDCPNIFTY_MONTHLY])
def test_a_road_that_is_not_in_the_register_is_always_refused(road):
    assert PracticeWindows().check(road, date(2024, 3, 4)) is OK
    assert PracticeWindows().last_day(road) is None


def test_the_window_ends_the_day_before_the_first_counted_session():
    windows = PracticeWindows(first_counted=date(2026, 6, 10))
    assert windows.check(RoadCode.NIFTY_MONTHLY, date(2026, 6, 9)) is None
    assert windows.check(RoadCode.NIFTY_MONTHLY, date(2026, 6, 10)) is OK
    assert PracticeWindows(first_counted=date(2027, 1, 4)).last_day(RoadCode.NIFTY_MONTHLY) == date(2026, 10, 12)


def register_status(data_set: str, period: str) -> str | None:
    for line in REGISTER.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[0].startswith(data_set) and period in cells[2]:
            return re.sub(r"[`]", "", cells[3])
    return None


def test_every_allowed_window_rests_on_a_spent_or_exposed_register_row():
    for road, window in PRACTICE_WINDOWS.items():
        for row in window.rows:
            assert register_status(row.data_set, row.period) in ("spent", "exposed"), (road, row)


def test_a_row_turned_fresh_in_the_register_would_fail_the_check(tmp_path, monkeypatch):
    planted = tmp_path / "DATA_SPEND.md"
    planted.write_text("| NIFTY weekly options | NSE daily closes | Feb 2019 - 9 Oct 2026 | `fresh` | none | x |\n")
    monkeypatch.setattr(f"{__name__}.REGISTER", planted)
    assert register_status("NIFTY weekly options", "Feb 2019 - 9 Oct 2026") == "fresh"
