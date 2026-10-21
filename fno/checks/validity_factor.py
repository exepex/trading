"""C4's own reader of the stress factor (story C2d): the latest row of A14c's factor file dated strictly before the
decision day, by the same rule as C2 but written apart (story C4: no C2 code). Fails closed by name. One k per
structure family (story A14c families): only rows of the proposal's family or of `all` (rows before the family column)
count."""

from __future__ import annotations

import csv
import math
from datetime import date, datetime
from pathlib import Path

from ..constants import (
    FAMILY_ALL,
    STRESS_FACTOR_COLUMNS,
    STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES,
    STRESS_FACTOR_DATE,
    STRESS_FACTOR_STATUSES,
    STRESS_FAMILIES,
    STRUCTURE_FAMILIES,
)


class FactorProblem(ValueError):
    """No usable stress factor for the day, for the named reason."""


def factor_on(path: Path | None, day: date, max_age_days: int, structure: str) -> tuple[date, float]:
    """(as_of, factor) of the row in force on `day` for the structure's family; of two same-day rows the later one in
    the file (append-only)."""
    family = STRUCTURE_FAMILIES.get(structure)
    if family is None:
        raise FactorProblem(f"stressed margin: {structure} has no structure family (fno/constants.py)")
    before = [row[:2] for row in _rows(path) if row[0] < day and row[2] in (family, FAMILY_ALL)]
    if not before:
        raise FactorProblem(f"stressed margin: {path.name} has no factor row before {day} for the {family} family")
    as_of, factor = sorted(before, key=lambda row: row[0])[-1]  # a stable sort keeps the file's order within a day
    if (day - as_of).days > max_age_days:
        raise FactorProblem(f"stressed margin multiplier of {as_of} is not valid on {day}")
    return as_of, factor


def _rows(path: Path | None) -> list[tuple[date, float, str]]:
    """Every row, checked: one unreadable row anywhere refuses the file by name."""
    if path is None:
        raise FactorProblem("stressed margin multiplier is not set (risk.stressed_margin.factor_file is required)")
    if not path.is_file():
        raise FactorProblem(f"stressed margin: the factor file {path.name} is missing")
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) not in (STRESS_FACTOR_COLUMNS, STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES):
            raise FactorProblem(f"stressed margin: {path.name} columns must be {', '.join(STRESS_FACTOR_COLUMNS)}")
        return [_row(row, f"{path.name} row {number}") for number, row in enumerate(reader, 2)]


def _row(row: dict[str, str | None], where: str) -> tuple[date, float, str]:
    if None in row:  # more fields than the header: a family row under the old header would read as `all`
        raise FactorProblem(f"stressed margin: {where} has more fields than the header")
    try:
        as_of = datetime.strptime(row["as_of"] or "", STRESS_FACTOR_DATE).date()
        factor = float(row["factor"] or "")
    except (TypeError, ValueError) as exc:
        raise FactorProblem(f"stressed margin: {where} is unreadable ({exc})") from exc
    status = row["status"]
    if not math.isfinite(factor) or factor < 1 or status not in STRESS_FACTOR_STATUSES:
        raise FactorProblem(f"stressed margin: {where} of {as_of} has factor {factor:g}, status {status!r}")
    family = row.get("family") or FAMILY_ALL
    if family not in (*STRESS_FAMILIES, FAMILY_ALL):
        raise FactorProblem(f"stressed margin: {where} has family {family!r}")
    return as_of, factor, family
