"""A14c's side of the stress factor file (`stress_factor.csv`, story C2d's columns): each family's last row as
written, the guardrails that decide the next rows, and the append-only write.
C2 and C4 read the file with their own readers.

Guardrails (owner, 15 Oct 2026, DESK_DECISIONS da0f769d; orchestrator: hold every fall): a result below 1.0 writes no
row; a result at or above the factor in force is applied at once; any lower result is held (the row keeps the old
factor and the alert asks the owner), unless the run cites the owner's DESK_DECISIONS commit approving that fall.

One k per structure family (owner, 16 Oct 2026): each run appends one row per family. A family's factor in force is its
own latest row or an `all` row (the rows written before the family column), whichever is later; only its own rows carry
a measured value forward, so its first run is full. The first append adds `family` to the header line once; no data
row's bytes change."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..constants import FAMILY_ALL, STRESS_FACTOR_COLUMNS, STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES

ROUND_STEP = 0.05  # the rule rounds the largest needed factor up to the next 0.05 (response 77)
APPLIED, HELD = "applied", "held"
HEADERS = (STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES, STRESS_FACTOR_COLUMNS)  # before and after the family column


class StressRowRefused(RuntimeError):
    """No row may be written, for the named reason."""


@dataclass(frozen=True)
class LastRow:
    factor: float
    unrounded: float | None  # None: the owner's seed (a hand value), so the next run is full
    coverage_through: date | None


@dataclass(frozen=True)
class NextRow:
    as_of: date
    factor: float
    computed: float
    unrounded: float
    status: str
    peak: str
    coverage_through: date
    evidence_sha256: str
    family: str

    def as_csv_line(self) -> str:
        values = (self.as_of.isoformat(), f"{self.factor:g}", f"{self.computed:g}", f"{self.unrounded:.6f}",
                  self.status, self.peak, self.coverage_through.isoformat(), self.evidence_sha256,
                  self.family)  # fmt: skip
        out = io.StringIO()
        csv.writer(out, lineterminator="\n").writerow(values)
        return out.getvalue()


def rounded_up(value: float) -> float:
    """Up to the next 0.05 (1.407 -> 1.45; 1.40 stays 1.40), free of float and bisection noise: the needed factor is
    kept to 6 decimals (`unrounded`), so a bisection end 1e-9 above 1.40 still gives 1.40."""
    return round(math.ceil(round(value / ROUND_STEP, 6)) * ROUND_STEP, 2)


def decide(last: LastRow, unrounded: float, approved_fall: str | None = None) -> tuple[float, float, str]:
    """(factor in force, computed, status) for a run whose largest needed factor is `unrounded`."""
    computed = rounded_up(unrounded)
    if computed < 1:
        raise StressRowRefused(f"the computed factor {computed:g} is below 1")
    if computed >= last.factor:
        return computed, computed, APPLIED
    if approved_fall:
        return computed, computed, APPLIED  # the owner approved this lower value (`peak` names the decision)
    return last.factor, computed, HELD


class StressFactorFile:
    def __init__(self, path: Path):
        self.path = path

    def last(self, family: str) -> LastRow:
        """The family's factor in force (its own latest row or an `all` row, whichever is later in the file) and the
        measured value only its own latest row carries (none before its first run, so that run is full)."""
        rows = self._rows()
        in_force = [row for row in rows if (row.get("family") or FAMILY_ALL) in (family, FAMILY_ALL)]
        if not in_force:
            raise StressRowRefused(f"{self.path.name} has no row for {family}: the owner's seed must be first (C2d)")
        own = [row for row in rows if row.get("family") == family]
        try:
            unrounded = float(own[-1]["unrounded"]) if own and own[-1]["unrounded"] else None
            through = date.fromisoformat(own[-1]["coverage_through"]) if own and own[-1]["coverage_through"] else None
            return LastRow(float(in_force[-1]["factor"]), unrounded, through)
        except (TypeError, ValueError) as exc:
            raise StressRowRefused(f"{self.path.name}: the last {family} row is unreadable ({exc})") from exc

    def append(self, rows: list[NextRow]) -> None:
        """Appends one line per row; the data rows already there keep their bytes (never edited). Before the first
        family row the header line alone gains `family`, written to a new file and moved over the old one."""
        data = self.path.read_bytes()
        old_header, new_header = (",".join(columns).encode("utf-8") for columns in HEADERS)
        first = data.split(b"\n", 1)[0].rstrip(b"\r")
        if first not in (old_header, new_header):  # e.g. a quoted header: no migration
            raise StressRowRefused(f"{self.path.name}: line 1 must be exactly {new_header.decode('utf-8')}")
        if first == old_header:
            data = new_header + data[len(old_header) :]
        if data and not data.endswith(b"\n"):
            data += b"\n"
        fresh = self.path.with_suffix(".tmp")
        fresh.write_bytes(data + b"".join(row.as_csv_line().encode("utf-8") for row in rows))
        fresh.replace(self.path)

    def _rows(self) -> list[dict[str, str]]:
        if not self.path.is_file():
            raise StressRowRefused(f"{self.path.name} is missing")
        with open(self.path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if tuple(reader.fieldnames or ()) not in HEADERS:
                raise StressRowRefused(f"{self.path.name}: columns must be {', '.join(STRESS_FACTOR_COLUMNS)}")
            rows = list(reader)
        extra = next((number for number, row in enumerate(rows, 2) if None in row), None)
        if extra is not None:
            raise StressRowRefused(f"{self.path.name} row {extra} has more fields than the header")
        return rows
