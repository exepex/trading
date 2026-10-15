"""Story A14 criterion 1 as a switch (judge 77, option a): the job writes rows C2 trusts only after an independent
broker check of its figures passed. Until `config.yaml` `risk.margins.nse_span_check` holds that check's source and
date, a run computes and prints its rows and writes none, refused by name.

A check covers the structures it compared (`structures`; story STR1). The 14 Oct 2026 check compared SF, SC and BF
rows only, so that is the default when the block names none; a row of any other structure is printed, never written,
until a check that lists it passes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from ..constants import STRUCTURES, STRUCTURES_ONE_SIDE

CHECK_KEY = "nse_span_check"
NOT_PASSED = (
    "{rows} rows computed, none written: no independent broker check has passed (config.yaml risk.margins."
    f"{CHECK_KEY}: source and passed_on; story A14 criterion 1, judge 77)"
)


@dataclass(frozen=True)
class IndependentCheck:
    source: str | None  # where the passing check is recorded, e.g. the owner's Groww check in a claims file
    passed_on: date | None
    structures: frozenset[str] = frozenset(STRUCTURES)  # the codes whose rows the check compared with the broker's

    def covers(self, structure: str) -> bool:
        return structure in self.structures

    def passed_by(self, day: date) -> bool:
        return bool(self.source) and self.passed_on is not None and self.passed_on <= day

    @classmethod
    def from_margins_block(cls, margins: Mapping[str, Any]) -> IndependentCheck:
        """The switch from `risk.margins`; missing or empty means not passed. No `structures` list: SF, SC and BF."""
        block = margins.get(CHECK_KEY) or {}
        passed_on = block.get("passed_on")
        if isinstance(passed_on, str):
            passed_on = date.fromisoformat(passed_on)
        return cls(block.get("source"), passed_on, _covered(block.get("structures", list(STRUCTURES))))


def _covered(structures: Any) -> frozenset[str]:
    """The listed codes; anything but a non-empty list of known codes is refused, never read as covering nothing."""
    known = (*STRUCTURES, *STRUCTURES_ONE_SIDE)
    if not isinstance(structures, list) or not structures or any(code not in known for code in structures):
        raise ValueError(f"{CHECK_KEY}.structures must be a non-empty list of codes from {known}, not {structures!r}")
    return frozenset(structures)
