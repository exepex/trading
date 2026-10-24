"""When each manifest row entered the real record (REH1g, DRY2's gap G2): the A9 datasets and the global cues keep
their SHA-256 rows in `research/data/manifests/**/*.csv`, not in O9 receipts. A row counts from the committer time of
the first commit on the record's `main` (first-parent history, `git blame --first-parent` of `origin/main`) that holds
it, so a rehearsal sees a librarian or cue file only once the replay clock reaches that commit: never before (no
look-ahead). A row only in the working tree, or only on a branch not merged into `main`, never counts.

Two row shapes, each matched by its own writer's rule:
- a `path` column (the global cues, Groww's candles): the Drive path inside the raw area, matched whole;
- A9's `date,url,...` (`ManifestFolder`): a Drive path is its dataset's (day, URL) as the dataset's source names it
  (`day_for_path`, `url_for`: `Fingerprint.of`'s rule), so the same URL fetched on two days is two files.

The rows are read once per record checkout and process (`git blame` on 65 files takes about 5 s)."""

from __future__ import annotations

import csv
import io
import subprocess
from datetime import UTC, date, datetime
from functools import lru_cache
from pathlib import Path

from ..storage.source_lists import RAW_SOURCES, dataset_name

MANIFESTS = Path("research/data/manifests")
RAW_AREA = "raw/"  # the area the manifests describe (`storage.wiring.RAW_AREA`)
RECORD_MAIN = "origin/main"  # the record checkout's view of main (`checkout.RECORD_MAIN`)


class ManifestRows:
    def __init__(self, record: Path):
        self.record = Path(record)

    def seen_at(self, path: str) -> datetime | None:
        """When the row naming this Drive path reached the record's main, or None when no row there names it."""
        if not path.startswith(RAW_AREA):
            return None
        inside = path.removeprefix(RAW_AREA)
        paths, files = _index(self.record)
        found = paths.get(inside)
        return found if found is not None else files.get(_a9_key(inside))


def _a9_key(path: str) -> tuple[str, date, str] | None:
    """The (manifest, day, URL) row an A9 dataset's archive path is recorded under, or None for any other path."""
    for source in RAW_SOURCES:
        if path.startswith(f"{source.dataset}/"):
            try:
                return dataset_name(source), source.day_for_path(path), source.url_for(path)
            except ValueError:
                return None
    return None


@lru_cache(maxsize=4)
def _index(record: Path) -> tuple[dict[str, datetime], dict[tuple[str, date, str], datetime]]:
    paths: dict[str, datetime] = {}
    files: dict[tuple[str, date, str], datetime] = {}
    for manifest in sorted((record / MANIFESTS).rglob("*.csv")):
        top_level = manifest.parent == record / MANIFESTS
        for row, committed in _rows(record, manifest):
            if row.get("path"):
                _keep(paths, row["path"].strip("/"), committed)
            elif top_level and row.get("url") and row.get("date"):
                _keep(files, (manifest.stem, date.fromisoformat(row["date"]), row["url"]), committed)
    return paths, files


def _rows(record: Path, manifest: Path):
    """Each data row of the manifest as `main` holds it, with the committer time of its first-parent commit."""
    relative = manifest.relative_to(record).as_posix()
    blame = subprocess.run(["git", "blame", "--first-parent", "--line-porcelain", RECORD_MAIN, "--", relative],
                           cwd=record, capture_output=True, text=True, check=False)  # fmt: skip
    if blame.returncode != 0:  # not on main (yet): no row of it counts
        return
    header = None
    for committed, text in _blamed(blame.stdout):
        if header is None:
            header = next(csv.reader([text]))
        elif text.strip():
            yield dict(zip(header, next(csv.reader(io.StringIO(text))), strict=False)), committed


def _blamed(porcelain: str) -> list[tuple[datetime, str]]:
    found, committed = [], datetime.min.replace(tzinfo=UTC)
    for line in porcelain.splitlines():
        if line.startswith("\t"):
            found.append((committed, line[1:]))
        elif line.startswith("committer-time "):
            committed = datetime.fromtimestamp(int(line.split()[1]), UTC)
    return found


def _keep(index: dict, key, committed: datetime) -> None:
    if key not in index or committed < index[key]:
        index[key] = committed
