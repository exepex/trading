"""A playbook whose versions open by date rather than by D1's registry (story F6, Book 3): each strategy trades from
the session after the day it opened (Book 3: the day it was proposed and registered), the same "a same-day approval
trades from the next session" rule D2 applies to Book 1. It has no research candidates to shadow and no status
history; everything D2 and C4 read of a playbook (`strategies`, `approved_on`, `shadow_on`) answers from the dates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

from .loader import Playbook
from .schema import Strategy


@dataclass(frozen=True)
class OpenedPlaybook(Playbook):
    opens: Mapping[tuple[str, int], date] = field(default_factory=dict)  # version -> the day it opened

    def approved(self) -> tuple[Strategy, ...]:
        return self.strategies

    def status_on(self, day: date) -> dict[tuple[str, int], str]:
        return {}  # no D1 status: the common opportunity set is Book 1's playbook, never this one

    def approved_on(self, day: date) -> tuple[Strategy, ...]:
        return tuple(s for s in self.strategies if s.key in self.opens and self.opens[s.key] < day)

    def shadow_on(self, day: date) -> tuple[Strategy, ...]:
        return ()
