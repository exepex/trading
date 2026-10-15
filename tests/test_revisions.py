"""Story A11: a later NSE version of an archived file is kept beside it in a revisions area, never over it; a
point-in-time reader returns the version available at a moment and a latest reader the newest one, tested on the real
12 Oct 2026 index-close rewrite (both versions committed as fixtures)."""

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from fno.models import IST
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.coverage import CoverageCheck, CoverageDataset, report_lines
from fno.storage.manifest_folder import Fingerprint, ManifestFolder
from fno.storage.raw_source import NseIndexCloseSource, PublishedFile, RawFileSource, RawSourceUnavailable
from fno.storage.raw_store import LocalFolderStore, ReadOnlyStoreError, StoredCopyDamaged
from fno.storage.revision_source import RevisionCapturingSource, sweep_revisions
from fno.storage.revisions import RevisionArchive, RevisionIndex
from fno.storage.versioned_store import VersionedRawStore
from fno.storage.wiring import DATED_SOURCES, build_manifest_folder, build_revision_index

FIXTURES = Path(__file__).parent / "fixtures" / "nse" / "revisions"
FIRST = (FIXTURES / "ind_close_all_12102026.first.csv").read_bytes()  # archived 12 Oct 2026, SHA fc847998...
REWRITTEN = (FIXTURES / "ind_close_all_12102026.rewritten.csv").read_bytes()  # NSE's file since 23:20 IST
OCT_12 = date(2026, 10, 12)
PATH = NseIndexCloseSource.path_for(OCT_12)
NSE_LAST_MODIFIED = datetime(2026, 10, 12, 17, 50, 10, tzinfo=UTC)  # its Last-Modified header, 13 Oct
FOUND = datetime(2026, 10, 13, 18, 8, tzinfo=IST)
SOURCE_URL = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-02,holiday,Gandhi Jayanti,{SOURCE_URL}\n")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Setup:
    """The raw archive holding the first version with its manifest row, and an empty revisions area."""

    def __init__(self, tmp_path):
        self.raw, self.revisions = LocalFolderStore(tmp_path / "raw"), LocalFolderStore(tmp_path / "revisions")
        self.manifests = ManifestFolder(tmp_path / "manifests")
        self.index = RevisionIndex(tmp_path / "manifests" / "revisions", DATED_SOURCES)
        self.raw.put(PATH, FIRST)
        self.manifests.record(NseIndexCloseSource, Fingerprint.of(NseIndexCloseSource, PATH, FIRST))
        self.archive = RevisionArchive(self.raw, self.revisions, self.index, self.manifests, lambda: FOUND)

    def reader(self, as_of):
        return VersionedRawStore(self.raw, self.revisions, self.index, as_of)


def test_a_later_version_is_kept_under_the_same_path_with_its_time_and_sha256_and_the_raw_file_never_changes(tmp_path):
    s = Setup(tmp_path)
    assert s.archive.capture(PATH, PublishedFile(FIRST, NSE_LAST_MODIFIED)) is None  # the archived version: nothing
    revision = s.archive.capture(PATH, PublishedFile(REWRITTEN, NSE_LAST_MODIFIED))
    assert revision.revision_path == f"{PATH}/20261012T232010+0530_{sha(REWRITTEN)}.csv"
    assert revision.available_from == datetime(2026, 10, 12, 23, 20, 10, tzinfo=IST) and revision.found_at == FOUND
    assert s.revisions.get(revision.revision_path) == REWRITTEN and s.raw.get(PATH) == FIRST  # raw untouched
    assert s.archive.capture(PATH, PublishedFile(REWRITTEN, NSE_LAST_MODIFIED)) is None  # found again: no new row
    assert s.index.for_path(PATH) == [revision] and s.archive.stored == [revision]
    lines = s.index.path_for(NseIndexCloseSource).read_text().splitlines()
    assert lines[0] == "date,path,sha256,size_bytes,available_from,last_modified,found_at" and len(lines) == 2


def test_without_last_modified_the_version_counts_from_when_it_was_found_and_a_third_version_is_appended(tmp_path):
    s = Setup(tmp_path)
    second = s.archive.capture(PATH, PublishedFile(REWRITTEN, NSE_LAST_MODIFIED))
    third = s.archive.capture(PATH, PublishedFile(REWRITTEN + b"x", None))
    assert third.available_from == FOUND and third.last_modified is None
    assert s.index.for_path(PATH) == [second, third]


def test_a_file_the_raw_archive_does_not_hold_is_not_a_revision(tmp_path):
    s = Setup(tmp_path)
    other = NseIndexCloseSource.path_for(date(2026, 10, 9))
    assert s.archive.capture(other, PublishedFile(b"new", None)) is None
    assert s.archive.not_archived == [other] and s.index.read(NseIndexCloseSource) == []


def test_an_unfingerprinted_raw_file_is_compared_by_its_own_bytes(tmp_path):
    s = Setup(tmp_path)
    other = NseIndexCloseSource.path_for(date(2026, 10, 9))
    s.raw.put(other, b"first")  # no manifest row
    assert s.archive.capture(other, PublishedFile(b"first", None)) is None
    assert s.archive.capture(other, PublishedFile(b"second", None)) is not None


def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=IST)


def test_point_in_time_and_latest_readers_on_the_real_12_october_rewrite(tmp_path):
    s = Setup(tmp_path)
    s.archive.capture(PATH, PublishedFile(REWRITTEN, NSE_LAST_MODIFIED))
    assert sha(s.reader(at(12, 15, 30)).get(PATH)) == sha(FIRST)  # the 15:30 decision saw the first version
    assert sha(s.reader(at(12, 23, 20)).get(PATH)) == sha(FIRST)  # one second before NSE's rewrite
    assert sha(s.reader(datetime(2026, 10, 12, 23, 20, 10, tzinfo=IST)).get(PATH)) == sha(REWRITTEN)
    assert sha(s.reader(at(13, 9)).get(PATH)) == sha(REWRITTEN)
    assert sha(s.reader(None).get(PATH)) == sha(REWRITTEN)  # latest: for publishing
    other = NseIndexCloseSource.path_for(date(2026, 10, 9))
    s.raw.put(other, b"never revised")
    assert (
        s.reader(None).get(other) == b"never revised"
        and s.reader(None).get(NseIndexCloseSource.path_for(date(2026, 10, 8))) is None
    )


def test_the_real_rewrite_added_indices_and_changed_no_existing_row():
    first = {line.split(",")[0]: line for line in FIRST.decode().splitlines()}
    rewritten = {line.split(",")[0]: line for line in REWRITTEN.decode().splitlines()}
    assert sha(FIRST).startswith("fc847998") and sha(REWRITTEN).startswith("e8e8f6ec")
    assert all(rewritten[name] == row for name, row in first.items())  # NIFTY 50 and India VIX included
    added = set(rewritten) - set(first)
    assert {"Nifty Capital Goods", "Nifty Telecommunications"} <= added and len(added) == 21


def test_the_committed_records_hold_both_real_versions():
    manifest = build_manifest_folder().fingerprints(NseIndexCloseSource)
    assert manifest["ind_close_all_12102026.csv"] == sha(FIRST)  # the raw file's row never changes
    [revision] = build_revision_index().for_path(PATH)
    assert revision.sha256 == sha(REWRITTEN) and revision.size_bytes == len(REWRITTEN)
    assert revision.available_from == datetime(2026, 10, 12, 23, 20, 10, tzinfo=IST)


def test_readers_never_write_and_a_damaged_revision_is_refused(tmp_path):
    s = Setup(tmp_path)
    revision = s.archive.capture(PATH, PublishedFile(REWRITTEN, NSE_LAST_MODIFIED))
    with pytest.raises(ReadOnlyStoreError):
        s.reader(None).put(PATH, b"x")
    (tmp_path / "revisions" / revision.revision_path).write_bytes(b"flipped")
    with pytest.raises(StoredCopyDamaged):
        s.reader(None).get(PATH)


class LiveNse(RawFileSource):
    def __init__(self, files):
        self.files, self.asked = files, []

    def fetch(self, path):
        raise AssertionError("the sweep reads files with their Last-Modified")

    def fetch_published(self, path):
        self.asked.append(path)
        answer = self.files.get(path)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_a_sweep_reads_every_file_in_full_and_keeps_what_differs(tmp_path):
    s = Setup(tmp_path)
    gone, down = (NseIndexCloseSource.path_for(date(2026, 10, d)) for d in (8, 9))
    live = LiveNse({PATH: PublishedFile(REWRITTEN, NSE_LAST_MODIFIED), down: RawSourceUnavailable("down")})
    source = RevisionCapturingSource(live, s.archive)
    result = sweep_revisions(source, [PATH, gone, down])
    assert (result.checked, result.unanswered) == (3, {gone: "not served (HTTP 404)", down: "down"})
    assert len(s.archive.stored) == 1
    assert source.last_written(PATH) == NSE_LAST_MODIFIED and len(s.archive.stored) == 1  # full read, kept once


def test_coverage_reports_revisions_per_dataset(tmp_path):
    s = Setup(tmp_path)
    s.archive.capture(PATH, PublishedFile(REWRITTEN, NSE_LAST_MODIFIED))
    fingerprints, counts = s.manifests.fingerprints(NseIndexCloseSource), s.index.counts(NseIndexCloseSource)
    dataset = CoverageDataset(NseIndexCloseSource, lambda filename, data: None, fingerprints, counts)
    result = CoverageCheck(s.raw, CALENDAR, {}).run(dataset, OCT_12, OCT_12)
    assert result.ok and result.revised == [(OCT_12, 1)]
    lines = report_lines([result])
    assert lines[0].endswith("revised") and lines[1].endswith(" 1")
    assert f"revised (later NSE versions in revisions/) {NseIndexCloseSource.dataset} {OCT_12}: 1" in lines
