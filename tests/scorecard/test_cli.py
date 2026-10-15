"""`python -m fno desk scorecard` on the repository (report only: nothing is approved, nothing is paused)."""

import subprocess
import sys

from fno.config import ROOT


def test_the_command_reports_on_the_repository_without_firing_a_pause():
    run = subprocess.run(
        [sys.executable, "-m", "fno", "desk", "scorecard", "--report-only", "--on", "2026-10-14"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )  # fmt: skip
    assert run.stdout.splitlines()[:2] == ["automatic pauses: none", "== Book scorecards =="]


def test_the_desk_has_one_parser_holding_pack_and_scorecard():
    """Judge 73: one `desk` parser; each story adds its command to it (E2's pack, E6's scorecard)."""
    for command in (["pack", "--help"], ["scorecard", "--help"]):
        done = subprocess.run([sys.executable, "-m", "fno", "desk", *command], capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
    done = subprocess.run([sys.executable, "-m", "fno", "desk", "--help"], capture_output=True, text=True)
    assert "{pack,scorecard,book1}" in done.stdout  # the daily run is `fno daily run` (story O1)
