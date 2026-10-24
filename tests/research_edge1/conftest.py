"""Lets the EDGE1 tests import the study's package (research/edge1/edge1study)."""

import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2] / "research" / "edge1"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))
