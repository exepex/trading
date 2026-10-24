"""REH1k: the lab's editions in a rehearsal of a day before their live date run, every post of the edition's process
says it is not live in real runs (K1, K2), and a rehearsed routine's not-live command is exercised, never a failure
(K3, K4); a real run is unchanged (K5)."""

import os
from datetime import date

import pytest

from fno.constants import ENV_FNO_REHEARSAL, ENV_FNO_REHEARSAL_NOT_LIVE
from fno.forecast_lab import wiring
from fno.forecast_lab.constants import EVENING, MORNING
from fno.rehearsal.mode import Rehearsal, labelled
from fno.rehearsal.rehearse import run_routine
from fno.rehearsal.routines import ROUTINES, Command, Routine

D22, D23 = date(2026, 10, 22), date(2026, 10, 23)
CFG = {"forecast_lab": {"live_from": {"morning": "2026-10-23", "evening": "2026-10-23"}}}
NOTE_22 = "not live in real runs on 2026-10-22 (live from 2026-10-23)"


def mode(day, tmp_path):
    return {ENV_FNO_REHEARSAL: Rehearsal.new(day, tmp_path, tmp_path).to_env()}


# K1: the lab's live dates in a rehearsal


def test_before_their_live_date_both_editions_run_with_their_note(tmp_path):
    live, notes = wiring.lab_live(CFG, mode(D22, tmp_path))
    assert live == {MORNING: D22, EVENING: D22}
    assert notes == {MORNING: NOTE_22, EVENING: NOTE_22}


def test_on_the_live_day_itself_and_with_no_mode_nothing_changes(tmp_path):
    real = {MORNING: D23, EVENING: D23}
    assert wiring.lab_live(CFG, mode(D23, tmp_path)) == (real, {})
    assert wiring.lab_live(CFG, {}) == (real, {})  # K5's no-mode case (judge 611 m2)


def test_an_edition_with_no_live_date_gets_the_unset_note(tmp_path):
    live, notes = wiring.lab_live({"forecast_lab": {"live_from": {"morning": "2026-10-23"}}}, mode(D22, tmp_path))
    assert live[EVENING] == D22 and notes[EVENING] == "not live in real runs yet (live_from unset)"


class Sessions:
    def is_regular(self, day):
        return True


@pytest.fixture
def edition_root(monkeypatch):
    """`build_edition` with the composer and the records stubbed (they read Drive); its live dates are the real
    root's own."""
    seen = {}

    def composer(edition, env, live=None):
        seen["live"] = live
        return object(), Sessions(), live

    monkeypatch.setattr(wiring, "build_composer", composer)
    monkeypatch.setattr(wiring, "records", lambda edition, env=None: object())
    monkeypatch.setattr(wiring, "load_app_config", lambda: CFG)
    monkeypatch.setenv(ENV_FNO_REHEARSAL_NOT_LIVE, "before")  # recorded, so the line the edition sets is undone
    monkeypatch.delenv(ENV_FNO_REHEARSAL_NOT_LIVE)
    return seen


@pytest.mark.parametrize("edition", [MORNING, EVENING])
def test_the_edition_s_run_takes_the_rehearsal_s_date_and_notes_its_process(edition_root, monkeypatch, tmp_path,
                                                                           edition):  # fmt: skip
    monkeypatch.setenv(ENV_FNO_REHEARSAL, mode(D22, tmp_path)[ENV_FNO_REHEARSAL])
    run = wiring.build_edition(edition)
    assert run.edition.live_from == D22 and edition_root["live"][edition] == D22
    assert os.environ[ENV_FNO_REHEARSAL_NOT_LIVE] == NOTE_22


# K2: the note in every post of the edition's process


def test_every_labelled_post_carries_the_note_and_a_live_edition_s_none(edition_root, monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_FNO_REHEARSAL, mode(D22, tmp_path)[ENV_FNO_REHEARSAL])
    wiring.build_edition(MORNING)
    assert labelled("*DRY RUN*", "the morning edition") == f"*DRY RUN*\n{NOTE_22}\nthe morning edition"
    monkeypatch.delenv(ENV_FNO_REHEARSAL_NOT_LIVE)
    monkeypatch.setenv(ENV_FNO_REHEARSAL, mode(D23, tmp_path)[ENV_FNO_REHEARSAL])
    wiring.build_edition(MORNING)
    assert ENV_FNO_REHEARSAL_NOT_LIVE not in os.environ
    assert labelled("*DRY RUN*", "the morning edition") == "*DRY RUN*\nthe morning edition"


# K3: a not-live command is exercised, never a routine failure


def routine(tmp_path):
    """A routine like the morning's: a script that exits 1 in place of `lab open`."""
    script = tmp_path / "fno"
    script.mkdir()
    (script / "__main__.py").write_text(
        "import sys\nprint('lab open said no')\nsys.exit(1 if 'lab' in sys.argv else 0)\n"
    )
    return Routine("morning", "-", None, (Command(("ok",)), Command(("lab", "open"), live_key=MORNING)))


def test_a_not_live_command_s_failure_is_exercised_and_the_routine_is_done(tmp_path):
    exercised, lines = {}, []
    code, line = run_routine(tmp_path, routine(tmp_path), D22, dict(os.environ), lines.append,
                             frozenset({MORNING}), exercised)  # fmt: skip
    assert (code, line) == (0, "2 commands done")
    failed = {"status": "failed", "reason": "lab open said no"}
    assert exercised == {"lab open": {"result": {"status": "not_live", "exercised": failed}}}


def test_on_its_live_day_the_same_failure_is_the_routine_s(tmp_path):
    exercised = {}
    code, line = run_routine(tmp_path, routine(tmp_path), D23, dict(os.environ), [].append, frozenset(), exercised)
    assert (code, line, exercised) == (1, "failed: lab open", {})


def test_the_lab_editions_name_their_live_key_and_nothing_else_does():
    keyed = {" ".join(c.args): c.live_key for r in ROUTINES.values() for c in r.commands if c.live_key}
    assert keyed == {"lab open": MORNING, "lab close": EVENING}  # the pre-open's and the daily's: none
