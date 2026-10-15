"""C4's own reader of the stress factor (story C2d): the latest row of A14c's factor file dated strictly before the
decision day, by the same rule as C2 but written apart (story C4: no C2 code). Fails closed by name."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from ..constants import STRESS_FACTOR_COLUMNS, STRESS_FACTOR_STATUSES


class FactorProblem(ValueError):
    """No usable stress factor for the day, for the named reason."""


def factor_on(path: Path | None, day: date, max_age_days: int) -> tuple[date, float]:
    """(as_of, factor) of the row in force on `day`."""
    if path is None:
        raise FactorProblem("stressed margin multiplier is not set (risk.stressed_margin.factor_file is required)")
    if not path.is_file():
        raise FactorProblem(f"stressed margin: the factor file {path.name} is missing")
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != STRESS_FACTOR_COLUMNS:
            raise FactorProblem(f"stressed margin: {path.name} columns must be {', '.join(STRESS_FACTOR_COLUMNS)}")
        before = [r for r in reader if date.fromisoformat(r["as_of"]) < day]
    if not before:
        raise FactorProblem(f"stressed margin: {path.name} has no factor row before {day}")
    row = max(before, key=lambda r: r["as_of"])
    as_of, factor = date.fromisoformat(row["as_of"]), float(row["factor"])
    if factor < 1 or row["status"] not in STRESS_FACTOR_STATUSES:
        status = row["status"]
        raise FactorProblem(f"stressed margin: {path.name} row of {as_of} has factor {factor:g}, status {status!r}")
    if (day - as_of).days > max_age_days:
        raise FactorProblem(f"stressed margin multiplier of {as_of} is not valid on {day}")
    return as_of, factor
