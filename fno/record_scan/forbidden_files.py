"""Files that must never be committed whatever they hold (story A4b): the public-record scan (story O5) refuses them by
path, as one finding naming the kind, so a raw Groww quote file is refused even when added with `git add -f`."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForbiddenFiles:
    kind: str
    folder: str  # repository path prefix, ending with "/"
    suffix: str

    def matches(self, path: str) -> bool:
        return path.startswith(self.folder) and path.lower().endswith(self.suffix)


RAW_GROWW_QUOTES = ForbiddenFiles(
    "raw Groww quote file (Google Drive only, story A4b)", "research/data/quotes/groww/", ".csv"
)
