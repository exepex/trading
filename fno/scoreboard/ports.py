"""What scoreboard B reads besides the books' own records (story S2), each behind an interface so its source can change
in one class: a book's operating costs (C1's columns), its allocated AI cost (F8) and the protocol's status (S1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


class OperatingCosts(Protocol):
    def rows(self, book: str) -> list[dict]:
        """C1's operating-cost rows of the book (`month,item,category,amount_rs,source`); empty when none recorded."""


class AiCostAllocation(Protocol):
    def allocated(self, book: str, first: date, last: date) -> float | None:
        """The book's allocated AI plan cost over the days, in rupees; None when it cannot be known yet."""


@dataclass(frozen=True)
class ProtocolStatus:
    version: int | None  # None when there is no protocol file
    frozen: bool

    @property
    def label(self) -> str:
        if self.version is None:
            return "no evaluation protocol: figures provisional"
        state = "frozen" if self.frozen else "not frozen: figures provisional"
        return f"protocol v{self.version}, {state}"
