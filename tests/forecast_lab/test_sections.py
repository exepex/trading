"""FL1-1d-2: each Section in exactly one state, inside its expected as-of rule (judge 438): A17's US cues and the
RBI rate only when current at the 09:15 cutoff, Brent as its last print up to 10 days old, India VIX as the previous
session's official close in the morning and never in the evening, the day's flags.
Made-up levels only: the S&P 500 and the Nasdaq-100 are private cues (owner bcbbc454)."""

from datetime import date, time, timedelta

import pytest

from fno.forecast_lab.page.cues import AVAILABLE, NOT_AVAILABLE, NOT_OUT_YET
from fno.forecast_lab.page.reasons import Facts
from fno.forecast_lab.sections.global_cues import CueSpec, GlobalCueSection
from fno.forecast_lab.sections.india import FlagsSection, VixSection
from fno.forecast_lab.sections.spread import changes, size
from fno.global_cues.reading import CueReading
from fno.research_data.nifty_panel import DailyFiles

MON, FRI = date(2026, 10, 26), date(2026, 10, 23)
OPEN = time(9, 15)


class Table:
    def __init__(self, values, last):
        self.values, self.last = values, last

    def rows(self):
        days = [self.last - timedelta(days=len(self.values) - 1 - i) for i in range(len(self.values))]
        return [{"value_date": d.isoformat(), "value": str(v)} for d, v in zip(days, self.values, strict=True)]


class Reader:
    def __init__(self, status, values=(100.0, 101.0), last=FRI, age=3):
        self.tables, self.status, self.age, self.last = {"x": Table(values, last)}, status, age, last
        self.calls = []

    def read(self, cue, day, cutoff, live_only):
        self.calls.append((cue, day, cutoff, live_only))
        row = self.tables[cue].rows()[-1] if self.status != "none" else None
        return CueReading(row, self.status, self.age, None)


def section(reader, calendar=True, unit="%"):
    return GlobalCueSection(lambda: reader, CueSpec("x", "S&P 500", unit, calendar), OPEN)


@pytest.mark.parametrize("status", ["current", "ahead"])
def test_a_current_us_cue_is_shown_with_its_date_and_change_read_live_at_the_open(status):
    reader = Reader(status)
    view = section(reader).read(MON, "morning")
    (cue,) = view.items
    assert (view.status, cue.value, cue.change, cue.as_of, cue.role) == (AVAILABLE, 101.0, 1.0, FRI, "context")
    assert reader.calls == [("x", MON, OPEN, True)]


@pytest.mark.parametrize(("status", "edition", "state"), [("behind", "morning", NOT_AVAILABLE), ("stale", "evening",
                         NOT_OUT_YET), ("none", "evening", NOT_OUT_YET)])  # fmt: skip
def test_a_us_cue_outside_its_rule_is_never_shown_as_current(status, edition, state):
    view = section(Reader(status)).read(MON, edition)
    assert (view.status, view.items) == (state, ()) and status in view.why


@pytest.mark.parametrize(("age", "state"), [(8, AVAILABLE), (10, AVAILABLE), (11, NOT_AVAILABLE)])
def test_brent_is_its_last_print_up_to_10_days_old(age, state):
    view = section(Reader("behind", age=age), calendar=False).read(MON, "morning")
    assert view.status == state


def test_a_yield_moves_in_points_and_the_size_needs_20_earlier_moves():
    assert section(Reader("current", (4.0, 4.25)), unit="pts").read(MON, "morning").items[0].change == 0.25
    assert changes([100.0, 101.0, 99.99], percent=True) == pytest.approx([1.0, -1.0], abs=0.001)
    assert size(1.0, [0.5, -0.5] * 9) is None and size(1.0, [0.5, -0.5] * 10) == 2.0


def vix_files(archived):
    def get(day):
        data = b"Index Name,Closing Index Value\nIndia VIX,15.68\nNifty 50,22811.35\n" if day in archived else None
        return f"ind_close_all_{day:%d%m%Y}.csv", data

    return DailyFiles("index-close", "nse/indices/index-close", FRI, MON, get)


def vix(archived):
    history = {FRI - timedelta(days=1): 14.0}
    return VixSection(vix_files(archived), lambda day: FRI, lambda day: history)


def test_vix_is_the_previous_session_s_official_close_in_the_morning_only():
    view = vix({FRI}).read(MON, "morning")
    (cue,) = view.items
    assert (view.status, cue.value, cue.as_of, round(cue.change, 2)) == (AVAILABLE, 15.68, FRI, 12.0)
    assert vix({FRI}).read(MON, "evening").status == NOT_OUT_YET  # the list's value is not the close
    missing = vix(set()).read(MON, "morning")
    assert missing.status == NOT_AVAILABLE and "not archived yet" in missing.why


def test_the_day_s_flags_are_the_day_s_own_events_and_expiry():
    later = MON + timedelta(days=1)  # a later day's event is not today's flag
    facts = Facts(events={MON: "RBI policy decision", FRI: "Union Budget", later: "Union Budget"},
                  expiries=frozenset({MON}))  # fmt: skip
    view = FlagsSection(lambda day: facts).read(MON, "morning")
    assert [c.text for c in view.items] == ["RBI policy decision", "NIFTY F&O expiry today"]
    assert FlagsSection(lambda day: Facts()).read(MON, "morning").items == ()
