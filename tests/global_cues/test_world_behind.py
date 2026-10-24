"""Judge 351 addendum 2 (story A17e): a name whose reading is `behind` at 09:15 is alerted once per episode (the run
fails once, then a quiet reminder), its recovery is one line, and the committed state holds names only."""

from datetime import date

from fno.circulars.episodes import OpenProblems
from fno.global_cues import wiring
from fno.global_cues.behind import BehindCheck
from fno.global_cues.reading import BEHIND, CURRENT, STALE, CueReading

DAY = date(2026, 10, 21)


def check(tmp_path, statuses: dict[str, str]):
    read = lambda name, day: CueReading({"value_date": "2026-10-16"}, statuses[name], 5, DAY)  # noqa: E731
    return BehindCheck(read, ("nasdaq100", "sp500"), OpenProblems(tmp_path / "behind_alerted.txt"))


def test_a_name_turning_behind_fails_the_run_once_then_reminds_quietly_then_clears(tmp_path):
    lines, on_time = check(tmp_path, {"nasdaq100": BEHIND, "sp500": CURRENT}).run(DAY)
    assert not on_time and lines == [
        "nasdaq100: BEHIND, its newest value is older than the session expected by 09:15 IST"
    ]
    lines, on_time = check(tmp_path, {"nasdaq100": BEHIND, "sp500": CURRENT}).run(DAY)
    assert on_time and lines == ["still behind (alerted before): nasdaq100"]
    lines, on_time = check(tmp_path, {"nasdaq100": CURRENT, "sp500": CURRENT}).run(DAY)
    assert on_time and lines == ["nasdaq100: caught up"]
    assert (tmp_path / "behind_alerted.txt").read_text() == ""


def test_the_state_holds_names_only_and_stale_is_left_to_the_runs_own_stale_rule(tmp_path):
    lines, on_time = check(tmp_path, {"nasdaq100": STALE, "sp500": BEHIND}).run(DAY)
    assert lines == ["sp500: BEHIND, its newest value is older than the session expected by 09:15 IST"] and not on_time
    assert (tmp_path / "behind_alerted.txt").read_text() == "sp500\n"  # no date, no value


def test_nothing_behind_prints_nothing_and_an_old_name_outside_the_list_is_dropped(tmp_path):
    (tmp_path / "behind_alerted.txt").write_text("usdinr_fbil\n")
    assert check(tmp_path, {"nasdaq100": CURRENT, "sp500": CURRENT}).run(DAY) == ([], True)
    assert (tmp_path / "behind_alerted.txt").read_text() == ""


def test_only_names_with_a_real_session_calendar_are_judged():
    from fno.global_cues.cue_calendars import NseSessionCalendar, NyseCalendar
    from fno.storage.wiring import build_session_calendar

    calendars = wiring.build_calendars(build_session_calendar())
    for name in wiring.BEHIND_NAMES:
        pair = wiring.INDEX_PAIRS.get(name)
        cues = [c for c in (pair.official, pair.yahoo) if c] if pair else [name]
        assert all(isinstance(calendars[c], NyseCalendar | NseSessionCalendar) for c in cues), name
    assert set(wiring.BEHIND_NAMES) == {"sp500", "usdinr_rbi", "nasdaq100", "vix_us"}
