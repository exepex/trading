"""Margins as inputs (story C2): the broker's or NSE SPAN's margin per structure and lot, recorded with source and date.

`research/data/margins/margins.csv`: `structure, width, margin_per_lot_rs, source, as_of`. The margin of a trade is
its initial margin (SPAN plus exposure) for its structure, width and lots, from the latest row dated on or before the
decision day; a missing row, or one older than the configured age, fails closed. It is never the broker's live total,
which includes the marked loss of a short structure: that loss is already in available cash (the lower of cash and
marked equity), and would count twice.

Stressed margin, one frozen method (`risk.stressed_margin`):
- `multiplier`: the margin times a predeclared factor, with its source and date; missing or older than its age fails
  closed;
- `scenario_lookup`: a margin per stress scenario from SPAN parameter files (`structure, width, scenario,
  margin_per_lot_rs, source, as_of`); every configured scenario needs a fresh row, and the largest counts.
"""

from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from ..constants import STRESSED_MARGIN_MULTIPLIER, STRESSED_MARGIN_SCENARIO_LOOKUP
from .inputs import RiskInputError, TradeTerms
from .settings import StressedMarginSettings

MARGIN_COLUMNS = ("structure", "width", "margin_per_lot_rs", "source", "as_of")
SCENARIO_MARGIN_COLUMNS = ("structure", "width", "scenario", "margin_per_lot_rs", "source", "as_of")


def _rows(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.exists():
        raise RiskInputError(f"margin file {path.name} is missing")
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != columns:
            raise RiskInputError(f"{path.name}: columns must be {', '.join(columns)}")
        return list(reader)


def _fresh_margin(rows: list[dict[str, str]], what: str, day: date, max_age_days: int) -> float:
    """Per-lot margin of the latest row dated on or before `day`; refused when there is none or it is too old."""
    dated = [(date.fromisoformat(r["as_of"]), r) for r in rows if r["source"].strip()]
    usable = [(d, r) for d, r in dated if d <= day]
    if not usable:
        raise RiskInputError(f"no margin recorded for {what} on or before {day}")
    as_of, row = max(usable, key=lambda pair: pair[0])
    if (day - as_of).days > max_age_days:
        raise RiskInputError(f"margin for {what} is from {as_of}, older than {max_age_days} days on {day}")
    margin = float(row["margin_per_lot_rs"])
    if not margin > 0:
        raise RiskInputError(f"margin for {what} must be positive, not {margin}")
    return margin


def _matches(row: dict[str, str], terms: TradeTerms) -> bool:
    return row["structure"] == terms.structure and float(row["width"]) == terms.width


class MarginTable:
    def __init__(self, path: Path, max_age_days: int):
        self.path, self.max_age_days = path, max_age_days

    def margin(self, terms: TradeTerms, day: date) -> float:
        """Initial margin of a trade in rupees: per-lot margin x lots."""
        rows = [r for r in _rows(self.path, MARGIN_COLUMNS) if _matches(r, terms)]
        what = f"{terms.structure} width {terms.width:g}"
        return _fresh_margin(rows, what, day, self.max_age_days) * terms.lots


class StressedMargin(ABC):
    method: str

    @abstractmethod
    def margin(self, terms: TradeTerms, day: date) -> float:
        """The trade's margin under stress, in rupees."""

    @abstractmethod
    def record(self) -> dict[str, str]:
        """The method in force, for every decision record, so the judge can reproduce it."""


class MultiplierMargin(StressedMargin):
    method = STRESSED_MARGIN_MULTIPLIER

    def __init__(self, table: MarginTable, settings: StressedMarginSettings):
        self.table, self.settings = table, settings

    def margin(self, terms: TradeTerms, day: date) -> float:
        s = self.settings
        if s.multiplier is None or not s.source or s.as_of is None:
            raise RiskInputError("stressed margin multiplier is not set (factor, source and as_of are all required)")
        if s.as_of > day or (day - s.as_of).days > s.max_age_days:
            raise RiskInputError(f"stressed margin multiplier of {s.as_of} is not valid on {day}")
        return self.table.margin(terms, day) * s.multiplier

    def record(self) -> dict[str, str]:
        values = {"multiplier": self.settings.multiplier, "source": self.settings.source, "as_of": self.settings.as_of}
        return {"method": self.method} | {k: "" if v is None else str(v) for k, v in values.items()}


class ScenarioLookupMargin(StressedMargin):
    method = STRESSED_MARGIN_SCENARIO_LOOKUP

    def __init__(self, settings: StressedMarginSettings, scenarios: Sequence[str], max_age_days: int):
        self.settings, self.scenarios, self.max_age_days = settings, tuple(scenarios), max_age_days

    def margin(self, terms: TradeTerms, day: date) -> float:
        if self.settings.scenario_file is None:
            raise RiskInputError("stressed margin scenario_lookup has no scenario_file")
        rows = [r for r in _rows(self.settings.scenario_file, SCENARIO_MARGIN_COLUMNS) if _matches(r, terms)]
        per_lot = [
            _fresh_margin(
                [r for r in rows if r["scenario"] == name], f"{terms.structure} {name}", day, self.max_age_days
            )
            for name in self.scenarios
        ]
        return max(per_lot) * terms.lots

    def record(self) -> dict[str, str]:
        file = self.settings.scenario_file
        return {"method": self.method, "scenario_file": file.name if file else ""}
