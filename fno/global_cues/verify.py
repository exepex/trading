"""Recomputes every cue table row from the archived copy it names (story A17): the copy is found by its SHA-256 in
the snapshot log, read from the raw archive, its SHA-256 checked, and its value for the row's date compared. Read-only.
"""

from __future__ import annotations

import hashlib
from collections import Counter

from ..storage.raw_store import RawFileStore
from .collector import UNREADABLE
from .snapshot_log import SnapshotLog
from .source import GlobalCueSource


class CueTableVerifier:
    def __init__(self, store: RawFileStore, log: SnapshotLog):
        self.store, self.log = store, log

    def problems(self, source: GlobalCueSource, rows: list[dict[str, str]]) -> list[str]:
        days = [row["value_date"] for row in rows]
        twice = sorted(d for d, n in Counter(days).items() if n > 1)
        problems = [f"{source.cue} {d}: the table holds this date twice" for d in twice]
        problems += [] if days == sorted(days) else [f"{source.cue}: the table's dates are not in order"]
        paths, parsed = self.log.paths_by_sha256(source.cue), {}
        for row in rows:
            sha256 = row["source_sha256"]
            if sha256 not in parsed:
                parsed[sha256] = self._values(source, paths.get(sha256), sha256)
            values = parsed[sha256]
            if isinstance(values, str):
                problems.append(f"{source.cue} {row['value_date']}: {values}")
            elif values.get(row["value_date"]) != float(row["value"]):
                copy = values.get(row["value_date"])
                problems.append(f"{source.cue} {row['value_date']}: table {row['value']}, archived copy {copy}")
        return problems

    def _values(self, source: GlobalCueSource, path: str | None, sha256: str) -> dict[str, float] | str:
        if path is None:
            return f"no logged copy with SHA-256 {sha256[:12]}"
        data = self.store.get(path)
        if data is None or hashlib.sha256(data).hexdigest() != sha256:
            return f"{path} missing from the archive or not the logged bytes"
        try:
            return {v.value_date.isoformat(): v.value for v in source.parse(data)}
        except UNREADABLE as exc:
            return f"{path} fails the publisher's check: {exc}"
