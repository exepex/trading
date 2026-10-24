"""Lets the GR1 tests import the study's package (research/gr1/gr1study)."""

import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2] / "research" / "gr1"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))
