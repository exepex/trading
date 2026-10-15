"""Copies already in the raw archive, read back instead of downloaded (story A17).

- `adopt`: a copy saved before it was logged (the four US-index files fetched before their terms were read, kept by
  the owner): logged with the fetch time in its own path and the request its name matches, then read.
- `reuse_today`: the once-a-day rule's other half. A second run on the same IST date downloads nothing and reads the
  day's logged copy again, so a run whose table write failed can finish later that day with the copy's true
  `first_seen_at` (never a later one).
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime

from ..models import IST
from ..storage.raw_store import RawFileStore
from .collection import UNREADABLE, Collection, SourcedValue, final_values
from .snapshot_log import SnapshotLog, SnapshotRow
from .source import GlobalCueSource

COPY_TIME = "%Y/%m/%d/%H%M%S"  # a copy's fetch time, from its path `<YYYY>/<MM>/<DD>/<HHMMSS>_<name>` (IST)
COPY_PATH = "<dataset>/<YYYY>/<MM>/<DD>/<HHMMSS>_<name>"


class ArchivedCopies:
    def __init__(self, store: RawFileStore, log: SnapshotLog):
        self.store, self.log = store, log

    def adopt(self, source: GlobalCueSource, path: str, start: date, end: date) -> Collection:
        result = Collection(source.cue, datetime.now(IST))
        try:
            result.fetched_at = datetime.strptime("/".join(path.split("/")[-4:])[:17], COPY_TIME).replace(tzinfo=IST)
            name = path.rsplit("/", 1)[-1].split("_", 1)[1]
        except (ValueError, IndexError):
            result.failure = f"cannot adopt {path}: not a copy path {COPY_PATH}"
            return result
        request = next((r for r in source.requests(start, end) if r.name == name), None)
        if not path.startswith(f"{source.dataset}/") or request is None:
            result.failure = (
                f"cannot adopt {path}: not {source.cue}'s dataset, or no request named {name} for {start}-{end}"
            )
            return result
        data = self._read(source, path, start, end, result)
        if data is not None and path not in self.log.paths(source.cue):  # every copy logged once
            sha256 = hashlib.sha256(data).hexdigest()
            self.log.append(
                source.cue, SnapshotRow(result.fetched_at, path, request.url, request.form, sha256, len(data))
            )
        return result

    def reuse_today(self, source: GlobalCueSource, day: date, start: date, end: date) -> Collection:
        fetched_at, paths = self.log.latest_fetch_on(source.cue, day)
        result = Collection(source.cue, fetched_at)
        for path in paths:
            if self._read(source, path, start, end, result) is None:
                return result
        result.skipped = f"no download: today's copy of {fetched_at:%H:%M:%S} IST read again (at most once a day)"
        return result

    def _read(self, source: GlobalCueSource, path: str, start: date, end: date, result: Collection) -> bytes | None:
        """Adds the copy's final values in range to `result`; names the failure and returns None when unreadable."""
        data = self.store.get(path)
        if data is None:
            result.failure = f"{path} is not in the archive"
            return None
        try:
            values = final_values(source, source.parse(data), result.fetched_at)
        except UNREADABLE as exc:
            result.failure = f"{path} is not the publisher's file: {exc}"
            return None
        sha256 = hashlib.sha256(data).hexdigest()
        result.values += [SourcedValue(v, sha256) for v in values if start <= v.value_date <= end]
        return data
