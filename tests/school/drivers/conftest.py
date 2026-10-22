"""Lets the driver tests read EDGE1's frozen study (research/edge1/edge1study), as the EDGE1 tests do."""

import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[3] / "research" / "edge1"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))
