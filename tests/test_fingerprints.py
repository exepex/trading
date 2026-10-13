"""Stories A9 and A10: every manifest comes from one code path (whole from the archive, or one row per saved file),
the coverage check reads them, and a spot-check against NSE's live bytes reports a difference as a rewrite."""

import hashlib
from datetime import date

import pytest

from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.fingerprints import compare_with_source, fingerprint_store
from fno.storage.manifest_folder import Fingerprint, FingerprintingStore, ManifestFolder
from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource, ParticipantOiSource
from fno.storage.raw_store import LocalFolderStore, RawFileConflict
from fno.storage.wiring import RAW_SOURCES, build_manifest_folder, coverage_datasets

SOURCE_URL = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-02,holiday,Gandhi Jayanti,{SOURCE_URL}\n")
DAYS = [date(2026, 10, 1), date(2026, 10, 5)]


def stored(tmp_path, days):
    store = LocalFolderStore(tmp_path / "drive")
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


def test_a_written_manifest_is_read_back_sorted_and_used_by_the_coverage_check(tmp_path):
    manifests = ManifestFolder(tmp_path / "manifests")
    found = fingerprint_store(stored(tmp_path, DAYS), NseIndexCloseSource, CALENDAR, DAYS[0], DAYS[-1])
    manifests.write(NseIndexCloseSource, reversed(found))
    text = manifests.path_for(NseIndexCloseSource).read_text()
    assert text.splitlines()[0] == "date,url,status,sha256,size_bytes" and text.index("2026-10-01") < text.index(
        "10-05"
    )
    assert manifests.read(NseIndexCloseSource) == found
    dataset = next(d for d in coverage_datasets(manifests) if d.source is NseIndexCloseSource)
    assert dataset.fingerprints == {f.filename: f.sha256 for f in found}


def test_a_saved_file_gets_its_row_in_the_same_operation_and_a_row_is_never_changed(tmp_path):
    manifests = ManifestFolder(tmp_path / "manifests")
    store = FingerprintingStore(LocalFolderStore(tmp_path / "drive"), manifests, RAW_SOURCES)
    path = ParticipantOiSource.path_for(DAYS[0])
    store.put(path, b"oi")
    assert manifests.read(ParticipantOiSource) == [Fingerprint.of(ParticipantOiSource, path, b"oi")]
    store.put(path, b"oi")  # the same file again: the same single row
    assert len(manifests.read(ParticipantOiSource)) == 1
    with pytest.raises(RawFileConflict):
        manifests.record(ParticipantOiSource, Fingerprint.of(ParticipantOiSource, path, b"other bytes"))
    assert manifests.fingerprints(ParticipantOiSource) == {path.rsplit("/", 1)[1]: hashlib.sha256(b"oi").hexdigest()}


def test_a_refused_save_writes_no_row_and_an_unknown_dataset_is_never_saved(tmp_path):
    manifests = ManifestFolder(tmp_path / "manifests")
    store = FingerprintingStore(LocalFolderStore(tmp_path / "drive"), manifests, RAW_SOURCES)
    path = ParticipantOiSource.path_for(DAYS[0])
    store.put(path, b"oi")
    with pytest.raises(RawFileConflict):
        store.put(path, b"different")  # the store refuses: the manifest keeps the original row only
    assert len(manifests.read(ParticipantOiSource)) == 1
    with pytest.raises(ValueError, match="no dataset with a manifest"):
        store.put("nse/unknown/2026/10/x.csv", b"x")


@pytest.mark.parametrize("source", [NseDailyFoSource, NseLegacyFoSource, NseIndexCloseSource, ParticipantOiSource])
def test_every_source_reads_the_day_back_from_its_file_name(source):
    for day in (date(2017, 1, 2), date(2019, 12, 31), date(2026, 10, 12)):
        assert source.day_for(source.filename_for(day)) == day
    with pytest.raises(ValueError):
        source.day_for("not_an_nse_file.csv")


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


def test_every_raw_dataset_has_a_committed_manifest_in_one_folder():
    manifests = build_manifest_folder()
    for dataset in coverage_datasets():
        assert manifests.path_for(dataset.source).is_file() and len(dataset.fingerprints) >= 250, (
            dataset.source
        )  # a year+
    assert all(f.url.startswith("https://nsearchives.nseindia.com/") for f in manifests.read(NseDailyFoSource))
