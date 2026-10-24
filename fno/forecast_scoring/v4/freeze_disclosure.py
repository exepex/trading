"""The v4 freeze record's disclosure (protocol section 8; story G6 freeze, criterion 9): every exploratory back-fill and
every live row, report and Drive back-fill made on or before the freeze day, read from the repository, never typed by
hand. Each back-fill source names its days, its row count, its method hashes and the SHA-256 of its back-fill rows, so
the judge and any later reader can check that the rows disclosed are the rows still there."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ...forecast_v4_rules.records import BACKFILL, LIVE

V4_RECORDS = "research/forecasts/v4"  # G7's and M1's CSV records, M1's day files under weather/
WEATHER_DAYS = f"{V4_RECORDS}/weather"
REPORTS = "research/forecasts/v4_scores"  # G8's reports (and looks, none before the freeze)
DRIVE_BACKFILLS = "receipts/data/v4/records/backfill"  # G7b's Drive back-fills, one receipt per file
NONE = "- none"


@dataclass(frozen=True)
class Rows:
    """One source's rows of one label: where, which days, how many, made by which method, and their fingerprint."""

    source: str
    first: str
    last: str
    count: int
    methods: tuple[str, ...]
    sha256: str

    def line(self) -> str:
        methods = ", ".join(f"`{m[:12]}`" for m in self.methods) or "none"
        return (f"| `{self.source}` | {self.first} | {self.last} | {self.count} | {methods} | "
                f"`{self.sha256}` |")  # fmt: skip


def csv_rows(root: Path, label: str, through: date | None = None) -> list[Rows]:
    """Per record file, its rows of `label` (live ones only up to `through`): the header and those lines, hashed."""
    found = []
    for path in sorted((root / V4_RECORDS).glob("*/*.csv")):
        text = path.read_text(encoding="utf-8")
        header, *lines = text.splitlines()
        rows = zip(csv.DictReader(io.StringIO(text)), lines, strict=True)
        picked = [(row, line) for row, line in rows if _wanted(row, label, through)]
        if picked:
            body = "\n".join([header, *(line for _, line in picked)]) + "\n"
            found.append(_rows(path.relative_to(root).as_posix(), [r for r, _ in picked], body))
    return found


def weather_rows(root: Path, label: str, through: date | None = None) -> list[Rows]:
    """M1's day files of `label` as one source: the SHA-256 is over each file's path and bytes, in day order."""
    picked = []
    for path in sorted((root / WEATHER_DAYS).glob("*/*.json")):
        day = json.loads(path.read_text(encoding="utf-8"))
        if _wanted(day, label, through):
            picked.append((path, day))
    if not picked:
        return []
    body = "".join(
        f"{p.relative_to(root).as_posix()} {hashlib.sha256(p.read_bytes()).hexdigest()}\n" for p, _ in picked
    )
    return [_rows(f"{WEATHER_DAYS}/*/*.json", [d for _, d in picked], body)]


def _wanted(row: dict, label: str, through: date | None) -> bool:
    return row["label"] == label and (through is None or date.fromisoformat(row["day"]) <= through)


def _rows(source: str, rows: list[dict], body: str) -> Rows:
    days = sorted(r["day"] for r in rows)
    methods = tuple(sorted({r["method_sha256"] for r in rows if r.get("method_sha256")}))
    return Rows(source, days[0], days[-1], len(rows), methods, hashlib.sha256(body.encode("utf-8")).hexdigest())


def reports_through(root: Path, through: date) -> list[str]:
    """G8's report files dated on or before the freeze day (descriptive, exploratory)."""
    folder = root / REPORTS
    return sorted(p.relative_to(root).as_posix() for p in folder.glob("*.*") if _dated_on_or_before(p.stem, through))


def _dated_on_or_before(stem: str, through: date) -> bool:
    try:
        return date.fromisoformat(stem) <= through
    except ValueError:
        return False


def drive_backfills(root: Path) -> list[str]:
    """G7b's Drive back-fills by their receipts: the path and the SHA-256 the receipt holds (content stays in Drive)."""
    receipts = sorted((root / DRIVE_BACKFILLS).rglob("*.sha256"))
    return [f"| `{p.relative_to(root).as_posix()}` | `{p.read_text(encoding='utf-8').split()[0]}` |" for p in receipts]


def disclosure(root: Path, frozen_on: date) -> str:
    """The record's disclosure section, as Markdown."""
    head = "| Source | First day | Last day | Rows | Method SHA-256 (first 12) | Rows' SHA-256 |\n" + "|---" * 6 + "|"
    backfill = csv_rows(root, BACKFILL) + weather_rows(root, BACKFILL)
    live = csv_rows(root, LIVE, frozen_on) + weather_rows(root, LIVE, frozen_on)
    drive = drive_backfills(root)
    parts = [
        "### Exploratory back-fills in the repository (`backfill_exploratory`, never counted)",
        "\n".join([head, *(r.line() for r in backfill)]) if backfill else NONE,
        f"### Live rows made on or before {frozen_on} (before the freeze, never counted)",
        "\n".join([head, *(r.line() for r in live)]) if live else NONE,
        f"### G8's reports dated on or before {frozen_on} (exploratory)",
        "\n".join(f"- `{p}`" for p in reports_through(root, frozen_on)) or NONE,
        "### Exploratory back-fills in Drive (by receipt; never counted)",
        "\n".join(["| Receipt | File SHA-256 |", "|---|---|", *drive]) if drive else NONE,
    ]
    return "\n\n".join(parts)
