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
