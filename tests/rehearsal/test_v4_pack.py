"""Story G10 completion, criterion 12 (judge 580 SF1 and 580.1 minor 2): protocol v4's pieces in a rehearsal. `v4_pack`
goes through `rehearsed_live` like every key; its one note reaches the `v4` part's child (by its command) and both
steps; the release's D3 failure is excused only on a replayed day whose record holds no `v4` attempt; the deadline
checks the replayed day only. Only the composition roots and `fno/rehearsal/` read the mode."""

import os
from datetime import date

from fno.config import load_app_config
from fno.constants import ENV_FNO_REHEARSAL, ENV_FNO_REHEARSAL_NOT_LIVE
from fno.daily.v4_wiring import day_parts, part_notes, step_notes
from fno.rehearsal.live_wiring import NOT_LIVE_UNSET, rehearsed_live
from fno.rehearsal.mode import Rehearsal
from fno.rehearsal.v4_pack import NO_CAPTURE, NotedPartProcesses, rehearsed_catch_up, rehearsed_release_excuse

DAY = date(2026, 10, 23)
V4 = ("quotes", "record", "--window", "v4")


def env(tmp_path):
    return {ENV_FNO_REHEARSAL: Rehearsal.new(DAY, tmp_path, tmp_path / "record").to_env()}


def test_v4_pack_runs_in_a_rehearsal_and_its_one_note_reaches_the_part_and_both_steps(tmp_path):
    live, notes = rehearsed_live({"v4_pack": None, "card": None}, env(tmp_path))
    assert live["v4_pack"] == DAY and notes["v4_pack"] == NOT_LIVE_UNSET
    assert part_notes(day_parts(load_app_config()), notes) == {V4: NOT_LIVE_UNSET}  # A4's parts have no key
    shared = step_notes(notes)
    assert shared["v4_release"] == shared["v4_deadline"] == NOT_LIVE_UNSET and shared["card"] == NOT_LIVE_UNSET
    assert step_notes({"card": NOT_LIVE_UNSET}) == {"card": NOT_LIVE_UNSET}  # v4 live: nothing added


class Seen:
    def __init__(self):
        self.started = []

    def start(self, arguments, hold=None):
        self.started.append((tuple(arguments), os.environ.get(ENV_FNO_REHEARSAL_NOT_LIVE)))


def test_the_part_s_child_starts_with_its_note_and_the_environment_is_restored(monkeypatch):
    monkeypatch.delenv(ENV_FNO_REHEARSAL_NOT_LIVE, raising=False)
    seen = Seen()
    processes = NotedPartProcesses(seen, {V4: "note"})
    processes.start(V4)
    processes.start(("quotes", "record"))
    assert seen.started == [(V4, "note"), (("quotes", "record"), None)]
    assert ENV_FNO_REHEARSAL_NOT_LIVE not in os.environ
    monkeypatch.setenv(ENV_FNO_REHEARSAL_NOT_LIVE, "v4_release's note")  # NIFTY starting inside that step's wait
    processes.start(("quotes", "record"))
    assert seen.started[-1] == (("quotes", "record"), None)  # never another step's note (self-review, daily side 2)
    assert os.environ[ENV_FNO_REHEARSAL_NOT_LIVE] == "v4_release's note"  # the running step's note is put back


def test_the_release_is_excused_only_on_a_replayed_day_without_a_recorded_attempt(tmp_path):
    recorded = {(tmp_path / "record", date(2026, 10, 27))}
    excuse = rehearsed_release_excuse(lambda record, day: (record, day) in recorded, env(tmp_path))
    assert excuse(DAY) == NO_CAPTURE and excuse(date(2026, 10, 27)) is None
    assert rehearsed_release_excuse(lambda record, day: False, {})(DAY) is None  # a real run: never excused


def test_the_deadline_catches_up_only_in_a_real_run(tmp_path):
    assert rehearsed_catch_up({}) and not rehearsed_catch_up(env(tmp_path))
