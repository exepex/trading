"""Lets the R2 tests import the study's package (research/2026-10-15-r2-stock-options-results/r2study)."""

import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2] / "research" / "2026-10-15-r2-stock-options-results"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))
