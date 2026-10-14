"""Story A14 criterion 1 as a switch (judge 77, option a): the job writes rows C2 trusts only after an independent
broker check of its figures passed. Until `config.yaml` `risk.margins.nse_span_check` holds that check's source and
date, a run computes and prints its rows and writes none, refused by name."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

CHECK_KEY = "nse_span_check"
NOT_PASSED = (
    "{rows} rows computed, none written: no independent broker check has passed (config.yaml risk.margins."
    f"{CHECK_KEY}: source and passed_on; story A14 criterion 1, judge 77)"
)


@dataclass(frozen=True)
class IndependentCheck:
    source: str | None  # where the passing check is recorded, e.g. the owner's Groww check in a claims file
    passed_on: date | None

    def passed_by(self, day: date) -> bool:
        return bool(self.source) and self.passed_on is not None and self.passed_on <= day

    @classmethod
    def from_margins_block(cls, margins: Mapping[str, Any]) -> IndependentCheck:
        """The switch from `risk.margins`; missing or empty means not passed."""
        block = margins.get(CHECK_KEY) or {}
        passed_on = block.get("passed_on")
        if isinstance(passed_on, str):
            passed_on = date.fromisoformat(passed_on)
        return cls(block.get("source"), passed_on)
