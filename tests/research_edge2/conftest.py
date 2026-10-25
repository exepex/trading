"""Lets the EDGE2 tests import the study's packages (research/edge2/f1study and EDGE1's edge1study it reuses)."""

import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[2] / "research"
for study in (RESEARCH / "edge1", RESEARCH / "edge2"):
    if str(study) not in sys.path:
        sys.path.insert(0, str(study))
