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

from ..models import IST
from ..storage.raw_store import RawFileConflict, RawFileStore, StoredCopyDamaged
from .snapshot_log import SnapshotLog, SnapshotRow
from .source import CueValue, GlobalCueSource

ADOPTED_TIME = "%Y/%m/%d/%H%M%S"  # a copy's fetch time, from its path `<YYYY>/<MM>/<DD>/<HHMMSS>_<name>` (IST)
UNREADABLE = (ValueError, KeyError, TypeError)  # a file that is not the publisher's layout
SAVE_FAILURES = (RawFileConflict, StoredCopyDamaged, requests.RequestException)  # Drive refused or failed the copy


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
    skipped: str = ""  # why nothing was downloaded although nothing failed (the once-a-day rule)


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
        if source.once_a_day and self.log.fetched_on(source.cue, result.fetched_at.date()):
            result.skipped = f"already downloaded on {result.fetched_at.date()} (at most once a day)"
            return result
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
        result.fetched_at = self.clock()  # after the last download: a slow fetch is never labelled earlier than it was
        if not any(values for _, _, values in downloaded):
            result.failure = "no values in any file, nothing saved"
            return result
        values = []
        for done, (request, data, file_values) in enumerate(downloaded):
            try:
                sha256 = self._archive(source, request, data, result.fetched_at)
            except SAVE_FAILURES as exc:  # copies saved before it stay saved and logged; the table is not touched
                result.failure = f"saving failed after {done} of {len(downloaded)} copies: {request.name}: {exc}"
                return result
            values += [SourcedValue(v, sha256) for v in file_values if start <= v.value_date <= end]
        result.values = values
        return result

    def adopt(self, source: GlobalCueSource, path: str, start: date, end: date) -> Collection:
        """A copy already in the raw archive but not logged (fetched before its terms were read, kept by the owner):
        logged with the fetch time in its own path and the request its name matches, then read like a new copy."""
        fetched_at = datetime.strptime("/".join(path.split("/")[-4:])[:17], ADOPTED_TIME).replace(tzinfo=IST)
        name = path.rsplit("/", 1)[-1].split("_", 1)[1]
        request = next((r for r in source.requests(start, end) if r.name == name), None)
        result = Collection(source.cue, fetched_at)
        data = self.store.get(path)
        if request is None or data is None:
            result.failure = f"cannot adopt {path}: {'no request named ' + name if request is None else 'not archived'}"
            return result
        try:
            values = source.parse(data)
        except UNREADABLE as exc:
            result.failure = f"cannot adopt {path}: not the publisher's file: {exc}"
            return result
        sha256 = hashlib.sha256(data).hexdigest()
        if path not in self.log.paths(source.cue):  # every copy logged once, a second copy of the same bytes too
            self.log.append(source.cue, SnapshotRow(fetched_at, path, request.url, request.form, sha256, len(data)))
        result.values = [SourcedValue(v, sha256) for v in values if start <= v.value_date <= end]
        return result

    def _archive(self, source: GlobalCueSource, request, data: bytes, fetched_at: datetime) -> str:
        path = f"{source.dataset}/{fetched_at:%Y/%m/%d}/{fetched_at:%H%M%S}_{request.name}"
        sha256 = hashlib.sha256(data).hexdigest()
        self.store.put(path, data)
        self.log.append(source.cue, SnapshotRow(fetched_at, path, request.url, request.form, sha256, len(data)))
        return sha256
