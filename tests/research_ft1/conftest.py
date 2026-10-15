"""Lets the FT1 tests import the study's package (research/2026-10-16-fill-timing/ft1study)."""

import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2] / "research" / "2026-10-16-fill-timing"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))
