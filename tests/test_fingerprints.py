"""Story A9 (judge 18, minor 1): SHA-256 manifests of every NSE dataset in Drive, checked by the coverage check, and a
spot-check against NSE's live bytes that reports a difference as a rewrite."""

import hashlib
from datetime import date

from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.coverage import FingerprintCheck, read_fingerprints
from fno.storage.fingerprints import Fingerprint, compare_with_source, fingerprint_store, manifest_text
from fno.storage.raw_source import NseIndexCloseSource
from fno.storage.raw_store import LocalFolderStore
from fno.storage.wiring import COVERAGE_DATASETS, FINGERPRINT_MANIFESTS

SOURCE_URL = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-02,holiday,Gandhi Jayanti,{SOURCE_URL}\n")
DAYS = [date(2026, 10, 1), date(2026, 10, 5)]


def stored(tmp_path, days):
    store = LocalFolderStore(tmp_path)
    for day in days:
        store.put(NseIndexCloseSource.path_for(day), f"closes {day}".encode())
    return store


def test_every_file_in_the_store_is_fingerprinted_in_day_order_and_gaps_left_out(tmp_path):
    store = stored(tmp_path, DAYS)
    store.put(NseIndexCloseSource.path_for(date(2026, 10, 4)), b"a Sunday file")  # not a session: not in the manifest
    found = fingerprint_store(store, NseIndexCloseSource, CALENDAR, date(2026, 10, 1), date(2026, 10, 6))
    assert [f.day for f in found] == DAYS  # 6 Oct has no file: no row
    assert found[0].sha256 == hashlib.sha256(b"closes 2026-10-01").hexdigest() and found[0].size_bytes == 17
    assert found[0].url == "https://nsearchives.nseindia.com/content/indices/ind_close_all_01102026.csv"


def test_the_manifest_is_read_back_by_the_coverage_check(tmp_path):
    found = fingerprint_store(stored(tmp_path, DAYS), NseIndexCloseSource, CALENDAR, DAYS[0], DAYS[-1])
    path = tmp_path / "manifest.csv"
    path.write_text(manifest_text(found))
    assert path.read_text().splitlines()[0] == "date,url,status,sha256,size_bytes"
    assert read_fingerprints(path) == {f.url.rsplit("/", 1)[1]: f.sha256 for f in found}


class LiveNse(NseIndexCloseSource):
    def __init__(self, files):
        super().__init__(session=None)
        self.files = files

    def fetch(self, path):
        return self.files.get(path)


def test_a_live_file_that_differs_is_reported_as_an_nse_rewrite_and_the_archive_kept():
    same, rewritten = (Fingerprint(d, f"u{d.day}", hashlib.sha256(b"x").hexdigest(), 1) for d in DAYS)
    gone = Fingerprint(date(2026, 10, 6), "u6", "0" * 64, 1)
    live = LiveNse({NseIndexCloseSource.path_for(DAYS[0]): b"x", NseIndexCloseSource.path_for(DAYS[1]): b"new"})
    lines = compare_with_source(live, [same, rewritten, gone])
    assert lines[0].endswith("identical") and "NSE REWRITE" in lines[1] and "no longer serves it" in lines[2]


def test_every_nse_dataset_is_checked_against_a_committed_manifest():
    for dataset in COVERAGE_DATASETS:
        assert isinstance(dataset.validate, FingerprintCheck), dataset.source.dataset
        assert len(dataset.validate.fingerprints) > 600, dataset.source.dataset
    assert all(path.is_file() for path in FINGERPRINT_MANIFESTS.values())
