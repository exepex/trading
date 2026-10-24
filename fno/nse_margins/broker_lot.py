"""NSE's dated NIFTY lot for A14c part 2's baskets (judge 630 finding 3): read from A20a's archived `fo_mktlots.csv` of
the day with the market school's reader (`ArchivedLots`, never a second reader), so a `lot_sizes` setting left behind
an NSE lot revision is an `error`, never a basket sent for the wrong quantity."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from ..constants import NIFTY_SYMBOL
from ..school.contracts.roads import DatedLot
from ..school.roads.lots import ArchivedLots


class NseDatedLot:
    def __init__(self, lots: Callable[[], ArchivedLots]):
        """Built on first use: a closed day or an early start reads no Drive."""
        self._lots, self._read = lots, {}

    def __call__(self, day: date, expiry: date) -> int | str:
        """The lot in force on `day` for `expiry`'s month, or why there is none (the school's closure reason). Read
        once per run and expiry (the library keeps no copy; a failed read raises and is not remembered)."""
        if (day, expiry) not in self._read:
            found = self._lots().lot(NIFTY_SYMBOL, day, (expiry,))
            self._read[day, expiry] = found.units if isinstance(found, DatedLot) else found.reason.value
        return self._read[day, expiry]
