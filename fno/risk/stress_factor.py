"""The stress factor k in force on a decision day (story C2d): the latest row of A14c's append-only factor file dated
strictly before the day, so a replay of day d never sees a row written on d (judge 176); of two rows with the same date,
the later one in the file wins: the file is append-only, so it is the correction (judge 188). A held row keeps the old
factor in its `factor` column, so the row is read as written. Missing, malformed, too old or below 1 fails closed."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..constants import STRESS_FACTOR_COLUMNS, STRESS_FACTOR_STATUSES
from .inputs import RiskInputError


@dataclass(frozen=True)
class FactorRow:
    as_of: date
    factor: float
    status: str
    evidence_sha256: str  # empty for the owner's seed row

    def record(self) -> dict[str, str]:
        return {"as_of": self.as_of.isoformat(), "multiplier": f"{self.factor:g}", "status": self.status,
                "evidence_sha256": self.evidence_sha256}  # fmt: skip


def factor_in_force(path: Path, day: date, max_age_days: int) -> FactorRow:
    rows = [r for r in _rows(path) if date.fromisoformat(r["as_of"]) < day]
    if not rows:
        raise RiskInputError(f"stressed margin: {path.name} has no factor row before {day}")
    row = _parsed(sorted(rows, key=lambda r: r["as_of"])[-1], path.name)  # stable: of two same-day rows, the later
    if (day - row.as_of).days > max_age_days:
        raise RiskInputError(f"stressed margin multiplier of {row.as_of} is not valid on {day}")
    return row


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RiskInputError(f"stressed margin: the factor file {path.name} is missing")
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != STRESS_FACTOR_COLUMNS:
            raise RiskInputError(f"stressed margin: {path.name} columns must be {', '.join(STRESS_FACTOR_COLUMNS)}")
        return list(reader)


def _parsed(row: dict[str, str], name: str) -> FactorRow:
    factor, status = float(row["factor"]), row["status"]
    if factor < 1 or status not in STRESS_FACTOR_STATUSES:
        raise RiskInputError(f"stressed margin: {name} row of {row['as_of']} has factor {factor:g}, status {status!r}")
    return FactorRow(date.fromisoformat(row["as_of"]), factor, status, row["evidence_sha256"])
