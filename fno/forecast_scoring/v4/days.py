"""Each v4 day's quality label (story G10, protocol section 1.6), as G8 reads it. The go-live capture writes one file
per day, `<folder>/<YYYY-MM-DD>.json`: the label (`A` the 14:30 live capture, `system_late` no
complete pack by 14:40), the released pack's SHA-256 and the pack's latest `observed_at`. A `system_late` day is out
for every family (`LateDaysOut`) and counted; the "moved after cutoff" flag is counted, never a reason to drop a day.
A day with no file (every back-fill day) has no label: the close-proxy cohort."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ...constants import V4_DAY_A, V4_DAY_SYSTEM_LATE
from ...forecast_v4.terms import V4_PACK_WINDOW_END
from ...models import IST
from .inputs import ForecastValue, Outcome, V4ForecastSource, V4OutcomeSource

LABELS = (V4_DAY_A, V4_DAY_SYSTEM_LATE)  # A2 (A16's mark as fallback) dropped: it cannot hold a full pack
SHA256 = re.compile(r"[0-9a-f]{64}")
COUNTS_LINE = ("days (live pack): A {a}, system_late {late} (out for every family); moved after cutoff "
               "{flagged}, flag not computable {unknown}")  # fmt: skip


class DayFileError(ValueError):
    """A day file that breaks the format: scoring stops rather than guess a day's label."""


@dataclass(frozen=True)
class DayLabel:
    day: date
    label: str
    pack_sha256: str  # "" only on a system_late day with no pack
    observed_by: datetime | None  # the pack's latest observed_at; None only on a system_late day with no pack


@dataclass(frozen=True)
class DayCounts:
    a: int
    late: int
    flagged: int
    unknown: int  # labelled days whose 14:30 or 15:15 level is missing: the flag is not computable

    def line(self) -> str:
        return COUNTS_LINE.format(a=self.a, late=self.late, flagged=self.flagged, unknown=self.unknown)


class V4DaySource(ABC):
    @abstractmethod
    def labels(self) -> dict[date, DayLabel]:
        """One entry per labelled day."""


class DayFiles(V4DaySource):
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def labels(self) -> dict[date, DayLabel]:
        found = (parse_day(path.stem, json.loads(path.read_text(encoding="utf-8")))
                 for path in sorted(self.folder.glob("*.json")))  # fmt: skip
        return {label.day: label for label in found}


def parse_day(stem: str, body: dict) -> DayLabel:
    day = date.fromisoformat(stem)
    if body.get("day") != stem or body.get("label") not in LABELS:
        raise DayFileError(f"{stem}: the day or the label is not valid")
    sha, observed = body.get("pack_sha256") or "", body.get("observed_by") or ""
    observed_by = datetime.fromisoformat(observed) if observed else None
    if sha and not SHA256.fullmatch(sha):
        raise DayFileError(f"{stem}: the pack's SHA-256 is not valid")
    if body["label"] == V4_DAY_SYSTEM_LATE:
        return DayLabel(day, body["label"], sha, observed_by)
    if not sha or observed_by is None:
        raise DayFileError(f"{stem}: an {body['label']} day names its pack's SHA-256 and its latest observed_at")
    if observed_by > datetime.combine(day, V4_PACK_WINDOW_END, IST):
        raise DayFileError(f"{stem}: a field observed after {V4_PACK_WINDOW_END:%H:%M} makes the day system_late")
    return DayLabel(day, body["label"], sha, observed_by)


def day_counts(labels: dict[date, DayLabel], moved: Callable[[date], bool | None], as_of: date) -> DayCounts:
    """`moved(d)`: whether day d moved after the cutoff (None: not computable)."""
    shown = [label for day, label in labels.items() if day <= as_of]
    flags = [moved(label.day) for label in shown]
    count = [label.label for label in shown].count
    return DayCounts(count(V4_DAY_A), count(V4_DAY_SYSTEM_LATE), flags.count(True), flags.count(None))


class LateDaysOut(V4ForecastSource, V4OutcomeSource):
    """The forecasts and outcomes without the `system_late` days: with no pack, no family had the same inputs, so
    the day is neither scored nor a miss for anyone (protocol section 4)."""

    def __init__(self, forecasts: V4ForecastSource, outcomes: V4OutcomeSource, days: V4DaySource):
        self.forecast_source, self.outcome_source, self.days = forecasts, outcomes, days

    def forecasters(self, question: str) -> list[str]:
        return self.forecast_source.forecasters(question)

    def values(self, question: str, forecaster: str) -> dict[date, ForecastValue]:
        return self._without_late(self.forecast_source.values(question, forecaster))

    def outcomes(self, question: str) -> dict[date, Outcome]:
        return self._without_late(self.outcome_source.outcomes(question))

    def _without_late(self, by_day: dict) -> dict:
        late = {d for d, label in self.days.labels().items() if label.label == V4_DAY_SYSTEM_LATE}
        return {d: v for d, v in by_day.items() if d not in late}
