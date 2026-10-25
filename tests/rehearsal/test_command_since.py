"""REH1r: a routine command not yet in its routine on the replayed day runs as on the day but is exercised, never the
routine's failure (R1); on and after its `since` the real rule holds (R2); each `since` is its table row, the later
of the CLAUDE.md commit and the routine's own first run (R3); a command with no `since` is never exercised by it
(R4)."""

import os
from datetime import date

import pytest

from fno.forecast_lab.constants import EVENING, MORNING
from fno.rehearsal.exercised_line import exercised_line
from fno.rehearsal.rehearse import run_routine
from fno.rehearsal.routines import ROUTINES, Command

D21, D22, D23, D24 = (date(2026, 10, d) for d in (21, 22, 23, 24))
# docs/stories/REH1-rehearsal-mode.md, REH1r, Design 2 (judges 673.1 and 674.1)
TABLE = {
    ("daily", "daily run --day {day}"): None,
    ("preopen", "global-cues preopen"): D23,
    ("preopen", "preopen record"): D23,
    ("morning", "data-librarian index-close --from {week_ago}"): D23,
    ("morning", "lab open"): None,  # its live key (REH1k)
    ("morning", "records certify closes --since 7 --level certified --commit"): D24,
    ("evening", "closes read --commit"): D22,
    ("evening", "records certify closes --level provisional --commit"): D24,
    ("evening", "data-librarian fo-bhavcopy --from {day} --to {day}"): D22,
    ("evening", "data-librarian participant-oi --from {day} --to {day}"): D22,
    ("evening", "data-snapshot fii-dii-cash-by-session"): D22,
    ("evening", "lab close"): None,  # its live key (REH1k)
    ("evening", "lab release-check"): D22,
}


def failing_fno(tmp_path):
    """A stand-in `python -m fno` in the checkout: every command prints a line and exits 1."""
    (tmp_path / "fno").mkdir()
    (tmp_path / "fno" / "__main__.py").write_text(
        "import sys\nprint('said no:', ' '.join(sys.argv[1:]))\nsys.exit(1)\n"
    )


def evening(tmp_path, day, not_live=frozenset({EVENING})):
    failing_fno(tmp_path)
    exercised = {}
    code, line = run_routine(tmp_path, ROUTINES["evening"], day, dict(os.environ), [].append, not_live, exercised)
    return code, line, exercised


# R1: before `since`, exercised


def test_on_21_oct_every_evening_command_is_exercised_and_the_routine_is_done(tmp_path):
    code, line, exercised = evening(tmp_path, D21)
    assert (code, line) == (0, "7 commands done")
    assert len(exercised) == 7
    closes = exercised["closes read --commit"]["result"]
    assert closes == {"status": "not_live", "since": "2026-10-22",
                      "exercised": {"status": "failed", "reason": "said no: closes read --commit"}}  # fmt: skip
    assert "since" not in exercised["lab close"]["result"]  # its edition's own not-live, as REH1k gives it


def test_the_exercised_line_says_the_command_was_not_yet_in_its_routine(tmp_path):
    """Self-review should-fix: the owner sees why, once, in the posted line; a lab edition's item is as before."""
    _, _, exercised = evening(tmp_path, D21)
    line = exercised_line(exercised)
    assert "closes read --commit (in its routine from 2026-10-22) failed: said no: closes read --commit" in line
    assert "; lab close failed: said no: lab close;" in line


# R2: on and after `since`, the real rule


def test_on_22_oct_the_evening_s_own_commands_fail_as_on_the_day_and_the_later_ones_are_exercised(tmp_path):
    code, line, exercised = evening(tmp_path, D22)
    assert code == 1 and line == (
        "failed: closes read --commit, data-librarian fo-bhavcopy --from {day} --to {day}, data-librarian "
        "participant-oi --from {day} --to {day}, data-snapshot fii-dii-cash-by-session, lab release-check"
    )
    assert set(exercised) == {"records certify closes --level provisional --commit", "lab close"}


def test_on_24_oct_with_the_edition_live_nothing_is_exercised(tmp_path):
    code, line, exercised = evening(tmp_path, D24, not_live=frozenset())
    assert code == 1 and exercised == {} and line.count(", ") == 6  # all seven failed, as a real day would


@pytest.mark.parametrize(("day", "apart"), [(D22, True), (D23, False)], ids=["the-day-before", "the-day-itself"])
def test_the_boundary_index_close_is_exercised_before_its_first_morning_only(day, apart):
    command = ROUTINES["morning"].commands[0]
    assert command.args[:2] == ("data-librarian", "index-close") and command.exercised_on(day, frozenset()) is apart


# R3: each constant is its table row, and each command is still in its routine


def test_each_command_s_since_is_its_table_row():
    found = {(r.name, " ".join(c.args)): c.since for r in ROUTINES.values() for c in r.commands}
    assert found == TABLE


def test_the_lab_editions_keep_their_live_key_and_take_no_since():
    keyed = {c.live_key: c.since for r in ROUTINES.values() for c in r.commands if c.live_key}
    assert keyed == {MORNING: None, EVENING: None}


# R4: no since, never exercised by it


def test_a_command_with_no_since_is_never_exercised_by_it():
    daily = ROUTINES["daily"].commands[0]
    assert daily.since is None and not daily.exercised_on(date(2020, 1, 1), frozenset())
    assert Command(("x",), since=D22).exercised_on(D21, frozenset()) and not Command(("x",)).exercised_on(
        D21, frozenset()
    )


def test_set_apart_commands_without_an_exercised_record_are_refused(tmp_path):
    failing_fno(tmp_path)
    with pytest.raises(ValueError, match="need an `exercised` record"):
        run_routine(tmp_path, ROUTINES["evening"], D21, dict(os.environ), [].append, frozenset())


@pytest.mark.parametrize(
    ("day", "line"), [(D22, "2 commands done"), (D23, "failed: preopen record, global-cues preopen")]
)
def test_the_preopen_routine_before_and_on_its_first_day_through_run_routine(tmp_path, day, line):
    """Self-review minor: the boundary through `run_routine`, on a routine whose every command is set apart (one in
    the background)."""
    failing_fno(tmp_path)
    exercised = {}
    code, said = run_routine(tmp_path, ROUTINES["preopen"], day, dict(os.environ), [].append, frozenset(), exercised)
    assert said == line and code == (0 if day == D22 else 1)
    assert len(exercised) == (2 if day == D22 else 0)
