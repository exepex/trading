"""v4 forecast records (story G7, layout agreed with G8): `research/forecasts/v4/<forecaster>/<question>.csv`, one row
per day; `day,value,status,label` first, G7's audit columns after. Rows are written once: the same row again changes
nothing, a different row for a day already written is refused."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import asdict, dataclass, fields
from datetime import date
from pathlib import Path

from ..constants import V1_RV_1S
from .baselines import OK

LIVE, BACKFILL = "live", "backfill_exploratory"
BASELINE, RULE = "baseline", "rule"
SLOT_RULES, SLOT_REPORTED = "rules", "reported"
VERSION = "1"
POINT_QUESTIONS = frozenset({V1_RV_1S})  # phase 1: the variance question; the others are probabilities


class InvalidRecord(ValueError):
    """A value outside its question's range: refused, never written."""


class RecordConflict(RuntimeError):
    """A day already has a different row; rows are never changed."""


@dataclass(frozen=True)
class Record:
    day: str
    value: str  # empty unless status is ok
    status: str
    label: str
    forecaster_version: str
    kind: str
    slot: str
    method_sha256: str
    inputs_sha256: str
    made_at: str  # empty for back-filled rows, so a re-run writes identical files

    def same_as(self, other: Record) -> bool:
        return {**asdict(self), "made_at": ""} == {**asdict(other), "made_at": ""}


COLUMNS = tuple(f.name for f in fields(Record))


def record(day: date, question: str, status: str, value: float | None, **audit: str) -> Record:
    """A validated row: a variance finite and > 0, a probability in [0, 1]; a value only when status is ok."""
    if status == OK:
        bad = not math.isfinite(value) or (value <= 0 if question in POINT_QUESTIONS else not 0 <= value <= 1)
        if bad:
            raise InvalidRecord(f"{question} {day}: {value} is not a valid forecast")
        text = repr(float(value))
    else:
        text = ""
    return Record(day.isoformat(), text, status, forecaster_version=VERSION, **audit)


def path(folder: Path, forecaster: str, question: str) -> Path:
    return folder / forecaster / f"{question}.csv"


def read(file: Path) -> dict[str, Record]:
    if not file.exists():
        return {}
    return {r["day"]: Record(**r) for r in csv.DictReader(io.StringIO(file.read_text()))}


def write(folder: Path, forecaster: str, question: str, rows: list[Record]) -> int:
    """Adds rows for new days; returns how many were added. Refuses (writing nothing) on any changed day."""
    file = path(folder, forecaster, question)
    kept = read(file)
    added = 0
    for row in rows:
        old = kept.get(row.day)
        if old is not None:
            if not old.same_as(row):
                raise RecordConflict(f"{forecaster}/{question} {row.day}: a different row is already written")
            continue
        kept[row.day] = row
        added += 1
    if added:
        file.parent.mkdir(parents=True, exist_ok=True)
        out = io.StringIO()
        writer = csv.DictWriter(out, COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(kept[day]) for day in sorted(kept))
        file.write_text(out.getvalue())
    return added


def first_live_day(folder: Path) -> date | None:
    """The earliest day with a live row in any v4 record file (the back-fill stops before it)."""
    days = [r.day for file in folder.glob("*/*.csv") for r in read(file).values() if r.label == LIVE]
    return date.fromisoformat(min(days)) if days else None
