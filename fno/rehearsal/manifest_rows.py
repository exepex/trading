"""When each manifest row entered the real record (REH1g, DRY2's gap G2): the A9 datasets and the global cues keep
their SHA-256 rows in `research/data/manifests/**/*.csv`, not in O9 receipts. A row counts from the committer time of
the commit that added it (`git blame` on the record checkout), so a rehearsal sees a librarian or cue file only once
the replay clock reaches that commit: never before (no look-ahead). A row not committed yet never counts.

Two row shapes: a `path` column (the global cues, Groww's candles: the Drive path under the area), or A9's
`date,url,...` (the file is the URL's last part, inside the folder named after the manifest)."""

from __future__ import annotations

import csv
import io
import subprocess
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

MANIFESTS = Path("research/data/manifests")
NOT_COMMITTED = "0" * 40  # git blame's ID for a line not committed yet


class ManifestRows:
    def __init__(self, record: Path):
        self.record = Path(record)
        self._paths: dict[str, datetime] | None = None
        self._files: dict[tuple[str, str], datetime] = {}

    def seen_at(self, path: str) -> datetime | None:
        """When the row naming this Drive path was committed, or None when no committed row names it."""
        self._load()
        parts = PurePosixPath(path).parts
        for start in range(len(parts)):
            found = self._paths.get("/".join(parts[start:]))
            if found is not None:
                return found
        times = [self._files[(folder, parts[-1])] for folder in parts[:-1] if (folder, parts[-1]) in self._files]
        return min(times, default=None)

    def _load(self) -> None:
        if self._paths is not None:
            return
        self._paths = {}
        for manifest in sorted((self.record / MANIFESTS).rglob("*.csv")):
            for row, committed in self._rows(manifest):
                if row.get("path"):
                    _keep(self._paths, row["path"].strip("/"), committed)
                elif row.get("url"):
                    _keep(self._files, (manifest.stem, row["url"].rsplit("/", 1)[-1]), committed)

    def _rows(self, manifest: Path):
        """Each data row with its commit's committer time; uncommitted rows are left out."""
        relative = manifest.relative_to(self.record).as_posix()
        blame = subprocess.run(["git", "blame", "--line-porcelain", "--", relative], cwd=self.record,
                               capture_output=True, text=True, check=False)  # fmt: skip
        if blame.returncode != 0:
            return
        lines, header = _blamed(blame.stdout), None
        for commit, committed, text in lines:
            if header is None:
                header = next(csv.reader([text]))
                continue
            if commit != NOT_COMMITTED and text.strip():
                yield dict(zip(header, next(csv.reader(io.StringIO(text))), strict=False)), committed


def _blamed(porcelain: str) -> list[tuple[str, datetime, str]]:
    found, commit, committed = [], "", datetime.min.replace(tzinfo=UTC)
    for line in porcelain.splitlines():
        if line.startswith("\t"):
            found.append((commit, committed, line[1:]))
        elif line.startswith("committer-time "):
            committed = datetime.fromtimestamp(int(line.split()[1]), UTC)
        elif len(line) > 40 and line[40] == " " and all(c in "0123456789abcdef" for c in line[:40]):
            commit = line[:40]
    return found


def _keep(index: dict, key, committed: datetime) -> None:
    if key not in index or committed < index[key]:
        index[key] = committed
