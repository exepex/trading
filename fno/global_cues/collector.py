"""Downloads one cue's files, checks them, archives them raw and logs them (story A17).

All of a cue's files are downloaded and read before anything is saved: one failed download or one file that is not
the publisher's writes nothing for that cue, and the failure is named. A saved copy is filed under the time it was
fetched (`<dataset>/<YYYY>/<MM>/<DD>/<HHMMSS>_<name>`, IST), because these publishers replace their files in place: a
copy is never overwritten, and a later copy that changes a past value is kept beside the earlier one (A11's rule; the
table records the change, `table.py`). Every saved copy gets a row in the cue's snapshot log in the same operation.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime

import requests

from ..storage.raw_store import RawFileStore
from .snapshot_log import SnapshotLog, SnapshotRow
from .source import CueValue, GlobalCueSource

UNREADABLE = (ValueError, KeyError, TypeError)  # a file that is not the publisher's layout


@dataclass(frozen=True)
class SourcedValue:
    value: CueValue
    source_sha256: str


@dataclass
class Collection:
    cue: str
    fetched_at: datetime
    values: list[SourcedValue] = field(default_factory=list)
    failure: str = ""  # why nothing was saved; empty when every file was archived


class CueCollector:
    def __init__(
        self,
        session: requests.Session,
        store: RawFileStore,
        log: SnapshotLog,
        clock: Callable[[], datetime],
    ):
        self.session, self.store, self.log, self.clock = session, store, log, clock

    def collect(self, source: GlobalCueSource, start: date, end: date) -> Collection:
        result = Collection(source.cue, self.clock())
        downloaded = []
        for request in source.requests(start, end):
            try:
                data = source.download(self.session, request)
                values = source.parse(data)
            except requests.RequestException as exc:
                result.failure = f"download failed, nothing saved: {request.url}: {exc}"
                return result
            except UNREADABLE as exc:
                result.failure = f"not the publisher's file, nothing saved: {request.name}: {exc}"
                return result
            downloaded.append((request, data, values))
        for request, data, values in downloaded:
            sha256 = self._archive(source, request, data, result.fetched_at)
            result.values += [SourcedValue(v, sha256) for v in values if start <= v.value_date <= end]
        return result

    def _archive(self, source: GlobalCueSource, request, data: bytes, fetched_at: datetime) -> str:
        path = f"{source.dataset}/{fetched_at:%Y/%m/%d}/{fetched_at:%H%M%S}_{request.name}"
        sha256 = hashlib.sha256(data).hexdigest()
        self.store.put(path, data)
        self.log.append(source.cue, SnapshotRow(fetched_at, path, request.url, request.form, sha256, len(data)))
        return sha256
