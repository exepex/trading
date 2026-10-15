"""Story M1, criterion 7: the drivers, and the private overnight US flag read only through A17b's `reading_for`.
All cue values are made up."""

import math
from datetime import date

from fno.global_cues.cue_calendars import NyseCalendar
from fno.global_cues.reading import CueReader
from fno.global_cues.us_index_sources import CboeSp500Source, NasdaqNdxSource
from fno.global_cues.wiring import us_market_closures
from fno.weather.checklist_v0 import Event, V0Inputs
from fno.weather.drivers import LARGE, NORMAL, NOT_AVAILABLE, public_drivers, us_move_flag

NYSE = NyseCalendar(us_market_closures())
DAY = date(2026, 10, 15)  # Thursday: the expected US close at 15:00 IST is Wednesday 14 Oct
SEEN = "2026-10-15T06:00:00+05:30"


class Table:
    def __init__(self, held):
        self.held = held

    def rows(self):
        return self.held


def _rows(*pairs, seen=SEEN):
    return [{"value_date": d, "value": repr(v), "first_seen_at": seen} for d, v in pairs]


def _reader(sp500=(), nasdaq100=None):
    tables, sources = {"sp500": Table(list(sp500))}, {"sp500": CboeSp500Source()}
    if nasdaq100 is not None:
        tables["nasdaq100"], sources["nasdaq100"] = Table(list(nasdaq100)), NasdaqNdxSource()
    return CueReader(tables, sources, {cue: NYSE for cue in tables})


def _move(log_return):
    return _rows(("2026-10-13", 5000.0), ("2026-10-14", 5000.0 * math.exp(log_return)))


def _closes(latest):
    return _rows(("2026-10-13", 5000.0), ("2026-10-14", latest))


def test_a_2pct_log_move_is_large_and_just_under_is_normal():
    # closes have 2 decimals: 5101.01 is the first at or over 2% (ln = 0.020002), 5101.00 the last under (0.0199999)
    assert math.log(5101.01 / 5000) >= 0.02 > math.log(5101.00 / 5000)
    assert us_move_flag(_reader(_closes(5101.01)), DAY, live_only=True) == LARGE
    assert us_move_flag(_reader(_closes(5101.00)), DAY, live_only=True) == NORMAL
    assert us_move_flag(_reader(_closes(5000 * 5000 / 5101.01)), DAY, live_only=True) == LARGE  # a 2% fall


def test_either_us_index_moving_2pct_is_large():
    assert us_move_flag(_reader(_move(0.001), _move(-0.025)), DAY, live_only=True) == LARGE


def test_stale_and_none_readings_are_not_available():
    old = _rows(("2026-09-01", 5000.0), ("2026-09-02", 5200.0))
    assert us_move_flag(_reader(old), DAY, live_only=True) == NOT_AVAILABLE  # six weeks old: stale
    assert us_move_flag(_reader(()), DAY, live_only=True) == NOT_AVAILABLE  # none
    late = _move(0.03)
    late[-1]["first_seen_at"] = "2026-10-15T16:00:00+05:30"  # first seen after the cutoff: never used live
    assert us_move_flag(_reader(late), DAY, live_only=True) == NOT_AVAILABLE  # 13 Oct has no close before it
    assert us_move_flag(_reader(late), DAY, live_only=False) == LARGE  # the as-of view (back-fill) sees it
    assert us_move_flag(None, DAY, live_only=True) == NOT_AVAILABLE  # no Drive settings: no private cue tables


def test_the_public_drivers_show_v0_levels_and_events_and_never_the_us_move():
    inputs = V0Inputs(1.15, 0.21, 0.004, 0.10)
    drivers = public_drivers(inputs, [Event(date(2026, 10, 16), "rbi_policy", date(2026, 9, 1))])
    assert {k: v["reaches"] for k, v in drivers["v0_inputs"].items()} == {
        "vix_ratio": "AMBER", "vix_change5": "RED", "move5": "GREEN", "rv10": "GREEN",
    }  # fmt: skip
    assert drivers["events_next_5_sessions"] == [{"type": "rbi_policy", "date": "2026-10-16"}]
    assert drivers["us_move"] == "private"
    assert public_drivers(None, None) == {"v0_inputs": "not available", "events_next_5_sessions": None,
                                         "us_move": "private"}  # fmt: skip
