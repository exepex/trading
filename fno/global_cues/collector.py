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
from datetime import date, datetime

import requests

from ..storage.raw_store import RawFileConflict, RawFileStore, StoredCopyDamaged
from .archived_copies import ArchivedCopies
from .collection import UNREADABLE, Collection, SourcedValue, final_values
from .snapshot_log import SnapshotLog, SnapshotRow
from .source import GlobalCueSource

SAVE_FAILURES = (RawFileConflict, StoredCopyDamaged, requests.RequestException)  # Drive refused or failed the copy


class CueCollector:
    def __init__(
        self,
        session: requests.Session,
        store: RawFileStore,
        log: SnapshotLog,
        clock: Callable[[], datetime],
    ):
        self.session, self.store, self.log, self.clock = session, store, log, clock
        self.copies = ArchivedCopies(store, log)

    def collect(self, source: GlobalCueSource, start: date, end: date) -> Collection:
        result = Collection(source.cue, self.clock())
        if source.once_a_day and self.log.fetched_on(source.cue, result.fetched_at.date()):
            return self.copies.reuse_today(source, result.fetched_at.date(), start, end)
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
            final = final_values(source, file_values, result.fetched_at)
            values += [SourcedValue(v, sha256) for v in final if start <= v.value_date <= end]
        result.values = values
        return result

    def _archive(self, source: GlobalCueSource, request, data: bytes, fetched_at: datetime) -> str:
        path = f"{source.dataset}/{fetched_at:%Y/%m/%d}/{fetched_at:%H%M%S}_{request.name}"
        sha256 = hashlib.sha256(data).hexdigest()
        self.store.put(path, data)
        self.log.append(source.cue, SnapshotRow(fetched_at, path, request.url, request.form, sha256, len(data)))
        return sha256
