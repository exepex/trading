"""Which news source is fastest: for every source, how often it had a story first and how late it was otherwise."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

REPORT_HEADER = f"{'source':<28} {'first':>6} {'later':>6} {'median late':>12}"
REPORT_ROW = "{name:<28} {first:>6} {later:>6} {late:>12}"
NO_DATA = "No news recorded yet. Run the desk (`python -m fno live run`) during market hours."


@dataclass(frozen=True)
class SourceSpeed:
    source: str
    first: int  # stories this source delivered before any other
    later: int  # stories it delivered after another source
    median_late_seconds: float | None


def source_speeds(stories: list[dict], sightings: list[dict]) -> list[SourceSpeed]:
    first: dict[str, int] = {}
    late: dict[str, list[float]] = {}
    for story in stories:
        first[story["source"]] = first.get(story["source"], 0) + 1
    for sighting in sightings:
        late.setdefault(sighting["source"], []).append(float(sighting["lag_seconds"]))
    names = sorted(set(first) | set(late), key=lambda n: (-first.get(n, 0), n))
    return [
        SourceSpeed(n, first.get(n, 0), len(late.get(n, [])), median(late[n]) if late.get(n) else None) for n in names
    ]


def format_speed_report(speeds: list[SourceSpeed]) -> str:
    if not speeds:
        return NO_DATA
    lines = [REPORT_HEADER]
    for s in speeds:
        late = "-" if s.median_late_seconds is None else f"{s.median_late_seconds / 60:.1f} min"
        lines.append(REPORT_ROW.format(name=s.source[:28], first=s.first, later=s.later, late=late))
    return "\n".join(lines)
