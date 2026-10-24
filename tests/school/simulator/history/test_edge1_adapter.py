"""EDGE1 is read by file path under its own package name and never joins sys.path (judge 500, minor a)."""

import subprocess
import sys
from datetime import date
from pathlib import Path

from fno.school.simulator.history import edge1

ROOT = Path(__file__).resolve().parents[4]
PROBE = """
import sys
before = list(sys.path)
from fno.school.simulator.history import edge1
edge1.module("lots"); edge1.module("stt_history")
print(sys.path == before, edge1.PACKAGE in sys.modules, "edge1study" in sys.modules)
"""


def test_a_fresh_process_loads_edge1_without_touching_sys_path_or_the_plain_name():
    """A subprocess, since other tests in the suite put research/edge1 on the path themselves."""
    out = subprocess.run([sys.executable, "-c", PROBE], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.split() == ["True", "True", "False"]


def test_the_schedule_is_asked_only_for_the_indices_it_covers():
    assert edge1.circular_lot_or_none("FINNIFTY", date(2022, 1, 27)) is None
    assert edge1.circular_lot_or_none("NIFTY", date(2021, 6, 24)) == 75
