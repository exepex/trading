"""A22d's composition root: the open check reads NSE's index-close files from the stores only (never NSE, never a
Drive write) and A22's own files through the verified Drive cache."""

from __future__ import annotations

from datetime import date

from fno.preopen import wiring
from fno.preopen.check_files import DriveCacheFiles


class StoredCloses:
    def __init__(self):
        self.asked = []

    def get(self, day):
        self.asked.append(day)
        return "ind_close_all_21102026.csv", None


def test_the_open_check_reads_the_stored_index_close_files_and_the_verified_cache(monkeypatch):
    closes, cache = StoredCloses(), object()
    monkeypatch.setattr(wiring, "build_stored_index_close_files", lambda: closes)
    monkeypatch.setattr(wiring, "build_drive_cache", lambda: cache)
    check = wiring._open_check(lambda day: day, store=None)
    assert check.official(date(2026, 10, 21)) is None and closes.asked == [date(2026, 10, 21)]
    assert isinstance(check.files, DriveCacheFiles) and check.files.cache is cache and check.files.area == "data"
    assert not hasattr(wiring, "build_index_close_files")  # the writer's library (it fetches from NSE) is not wired
