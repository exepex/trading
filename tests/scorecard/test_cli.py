"""`python -m fno desk scorecard` on the repository (report only: nothing is approved, nothing is paused)."""

import subprocess
import sys

from fno import cli
from fno.desk import wiring as desk_wiring
from fno.storage import wiring as storage_wiring


def test_the_command_reports_on_the_repository_without_firing_a_pause(monkeypatch, capsys):
    monkeypatch.setattr(desk_wiring, "download_private_records", lambda day=None: None)  # Drive: not tested here
    assert cli.main(["desk", "scorecard", "--report-only", "--on", "2026-10-14"]) == 0
    assert capsys.readouterr().out.splitlines()[:2] == ["automatic pauses: none", "== Book scorecards =="]


def test_without_drive_the_command_stops_named_before_reading_any_account(monkeypatch, capsys):
    """Story E2c: the accounts live in Drive; without its settings nothing is read from a stale local copy."""
    monkeypatch.setattr(storage_wiring, "build_owner_drive", lambda: None)
    assert cli.main(["desk", "scorecard", "--report-only", "--on", "2026-10-14"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("stopped: the private paper records need Drive's owner settings") and "==" not in out


def test_the_desk_has_one_parser_holding_pack_and_scorecard():
    """Judge 73: one `desk` parser; each story adds its command to it (E2's pack, E6's scorecard)."""
    for command in (["pack", "--help"], ["scorecard", "--help"]):
        done = subprocess.run([sys.executable, "-m", "fno", "desk", *command], capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
    done = subprocess.run([sys.executable, "-m", "fno", "desk", "--help"], capture_output=True, text=True)
    assert "{pack,scorecard,book1}" in done.stdout  # the daily run is `fno daily run` (story O1)
