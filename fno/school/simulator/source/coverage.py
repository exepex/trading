"""What a practice snapshot could not price, so a report never hides it (story MS-SIM-c)."""

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Coverage:
    """Legs of one road-session by what happened to them. `insufficient` counts legs by the spread bucket that had fewer
    than 30 quoted sessions; those legs have no quote and a trade needing them is unavailable, never a zero spread."""

    legs: int = 0
    priced: int = 0
    untraded: int = 0  # no volume that day: not a quote
    impossible: int = 0  # EDGE1's rule on the closes
    insufficient: Counter = field(default_factory=Counter)

    @property
    def unpriced(self) -> int:
        return self.untraded + self.impossible + sum(self.insufficient.values())
