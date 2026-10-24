"""A14c part 2's comparison of Groww's margin with an A14 row (orchestrator, 16 Oct 2026; tolerances some evidence:
one basket on one day). SPAN: Groww's `span_required` against the row's `max(0, scan - NOV)`, within Rs 1 a lot.
Exposure: Groww's `exposure_required` against A14's own rule recomputed at independent NIFTY levels (this caller's
`get_quote`, read before the first basket and after the last), within 0.1% at some level between the two: Groww
charges exposure on the live index when each basket is asked, so a move during the run must not read as a mismatch
(judge 630), and the level is never implied from Groww's own figure (which would compare Groww with itself; judges
291 and 356)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .broker_basket import Basket
from .calculator import ExposureRule

SPAN_TOLERANCE_RS = 1.0
EXPOSURE_TOLERANCE = 0.001  # a share of the recomputed exposure
OK, MISMATCH, ERROR = "ok", "mismatch", "error"
SPAN_OFF = "SPAN {broker:.2f} vs {expected:.2f}"
EXPOSURE_OFF = "exposure {broker:.2f} vs {expected:.2f} at NIFTY {levels}"
RATE_STEP = "exposure rate step inside the NIFTY range {levels}"
NO_SECOND_LEVEL = "exposure {broker:.2f} vs {expected:.2f} at NIFTY {levels}, no second reading ({why})"


@dataclass(frozen=True)
class Levels:
    """NIFTY before the first basket and after the last; `after` is None when that reading failed (`why`)."""

    before: float
    after: float | None = None
    why: str = ""

    def __str__(self) -> str:
        return f"{self.before:.2f}" if self.after is None else f"{self.before:.2f}-{self.after:.2f}"


@dataclass(frozen=True)
class Comparison:
    span_broker: float
    span_expected: float
    exposure_broker: float
    exposure_expected: float
    status: str
    detail: str


def compare(basket: Basket, broker: tuple[float, float], levels: Levels, rule: ExposureRule, lot_size: int,
            day: date) -> Comparison:  # fmt: skip
    """`broker`: Groww's (span_required, exposure_required) for one lot of the basket. An exposure that cannot be
    judged (a rate step inside the range, or no second reading) is an `error`, never a guessed `mismatch`."""
    span, exposure = broker

    def expected(level: float) -> float:
        return rule.per_unit(basket.legs, level, basket.expiry, day) * lot_size

    off, unclear = [], ""
    if _beyond(span - basket.span_expected, SPAN_TOLERANCE_RS):
        off.append(SPAN_OFF.format(broker=span, expected=basket.span_expected))
    first = expected(levels.before)
    if levels.after is None:
        nearest = first
        if _outside(exposure, first):
            unclear = NO_SECOND_LEVEL.format(broker=exposure, expected=first, levels=levels, why=levels.why)
    else:
        last = expected(levels.after)
        nearest = min(max(exposure, min(first, last)), max(first, last))  # exposure is linear in the level
        if round(first / levels.before, 6) != round(last / levels.after, 6):  # the summed rate differs: two rates
            unclear = RATE_STEP.format(levels=levels)
        elif _outside(exposure, nearest):
            off.append(EXPOSURE_OFF.format(broker=exposure, expected=nearest, levels=levels))
    status = ERROR if unclear else MISMATCH if off else OK  # an unclear exposure is never a finding
    detail = "; ".join(part for part in (*off, unclear) if part)
    return Comparison(span, basket.span_expected, exposure, nearest, status, detail)


def _outside(exposure: float, expected: float) -> bool:
    return _beyond(exposure - expected, EXPOSURE_TOLERANCE * expected)  # 0 for a bought-only basket


def _beyond(difference: float, allowed: float) -> bool:
    """Off by more than `allowed`, both rounded to the paisa, so float noise never decides a case at the boundary."""
    return round(abs(difference), 2) > round(allowed, 2)
