"""The one place the simulator reads EDGE1's frozen study (orchestrator, 22 Oct 2026: read-only, one adapter, never
copied or edited): NSE's circular lot schedule and the dated STT rates. `research/edge1` is not a package, so its folder
goes on the path as EDGE1's own tests do."""

import sys
from collections.abc import Callable, Mapping
from datetime import date
from pathlib import Path

STUDY = Path(__file__).resolve().parents[4] / "research" / "edge1"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))

from edge1study.lots import SCHEDULE, circular_lot  # noqa: E402
from edge1study.stt_history import charges_on  # noqa: E402


def circular_lot_or_none(underlying: str, expiry: date) -> int | None:
    """NSE's circular lot for an index EDGE1 has a schedule for (NIFTY, BANKNIFTY); None for any other."""
    return circular_lot(underlying, expiry) if underlying in SCHEDULE else None


def dated_charges(charges: Mapping[str, float]) -> Callable[[date], dict]:
    """C1's charges with the two STT rates of a trade date (EDGE1's `stt_history`); every other charge as decided."""
    return charges_on(charges)
