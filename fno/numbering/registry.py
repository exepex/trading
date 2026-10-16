"""A category's registry rows (story O12): `number,name,session,claimed_at_utc`, one row per claimed number.

Rows with session `existing` were seeded from the files already on `main` (no time); every later row is a claim.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fno.numbering.categories import AddendumCategory, Category

HEADER = ("number", "name", "session", "claimed_at_utc")
SEEDED = "existing"
UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True)
class Row:
    number: str
    name: str
    session: str
    claimed_at_utc: str = ""

    @property
    def seeded(self) -> bool:
        return self.session == SEEDED

    def as_line(self) -> str:
        out = io.StringIO()
        csv.writer(out, lineterminator="\n").writerow((self.number, self.name, self.session, self.claimed_at_utc))
        return out.getvalue()


def utc_stamp(moment: datetime) -> str:
    return moment.strftime(UTC_FORMAT)


def valid_stamp(text: str) -> bool:
    try:
        datetime.strptime(text, UTC_FORMAT)
    except ValueError:
        return False
    return True


def read_rows(path: Path) -> list[Row]:
    """The registry's rows; a missing file is an empty registry. A row with the wrong column count raises ValueError."""
    if not path.exists():
        return []
    lines = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8"))))
    if not lines or tuple(lines[0]) != HEADER:
        raise ValueError(f"the first line must be {','.join(HEADER)}")
    rows = []
    for at, cells in enumerate(lines[1:], start=2):
        if len(cells) != len(HEADER):
            raise ValueError(f"line {at}: {len(cells)} columns, expected {len(HEADER)}")
        rows.append(Row(*cells))
    return rows


def append_row(path: Path, row: Row) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(",".join(HEADER) + "\n", encoding="utf-8")
    ended = path.read_text(encoding="utf-8").endswith("\n")  # a hand edit may drop the last line break
    with path.open("a", encoding="utf-8") as registry:
        registry.write(row.as_line() if ended else "\n" + row.as_line())


def next_number(category: Category, rows: list[Row], report: str | None = None) -> str:
    """The number after the highest taken one: per category, or per report for an addendum category."""
    if isinstance(category, AddendumCategory):
        taken = [int(r.number.split(".")[1]) for r in rows if r.number.split(".")[0] == report]
        return f"{report}.{max(taken, default=0) + 1}"
    return str(max((int(r.number) for r in rows), default=0) + 1)
