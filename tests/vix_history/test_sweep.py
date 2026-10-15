"""Story A15 with A11's rule: a later NSE version of a month is kept beside the original and named day by day; an
error page is never kept as a version; the table is not changed by a revision."""

import hashlib
from datetime import date, datetime

from fno.models import IST
from fno.storage.manifest_folder import ManifestFolder
from fno.storage.raw_source import PublishedFile, RawSourceUnavailable
from fno.storage.raw_store import LocalFolderStore
from fno.storage.revisions import RevisionArchive, RevisionIndex
from fno.vix_history.month_file import NseVixJsonReader
from fno.vix_history.source import NseVixHistorySource as Source
from fno.vix_history.sweep import VixRevisionSweep
from tests.vix_history.nse_vix import FakeNseVix, july_2010

JULY = date(2010, 7, 1)
PATH = Source.path_for(JULY)
FOUND = datetime(2026, 10, 15, 6, 0, tzinfo=IST)


class Unreachable(FakeNseVix):
    def fetch(self, path):
        raise RawSourceUnavailable("NSE: connection reset")


def sweep(tmp_path, source):
    raw, revisions = LocalFolderStore(tmp_path / "raw"), LocalFolderStore(tmp_path / "revisions")
    if raw.get(PATH) is None:
        raw.put(PATH, july_2010())
    index = RevisionIndex(tmp_path / "index", (Source,))
    archive = RevisionArchive(raw, revisions, index, ManifestFolder(tmp_path / "manifests"), clock=lambda: FOUND)
    fingerprints = {JULY: hashlib.sha256(july_2010()).hexdigest()}
    return VixRevisionSweep(source, archive, raw, Source.path_for, NseVixJsonReader(), fingerprints), raw, index


def test_a_revised_month_is_kept_beside_the_original_and_named_day_by_day(tmp_path):
    job, raw, index = sweep(tmp_path, FakeNseVix({PATH: july_2010(close_on_20th=20.4)}))
    report = job.sweep([JULY])
    assert report.revised == [(JULY, ["2010-07-20: O 20.71 H 20.71 L 19.61 C 20.38 -> O 20.71 H 20.71 L 19.61 C 20.4"])]
    assert raw.get(PATH) == july_2010()  # the original is never overwritten
    (revision,) = index.for_path(PATH)
    assert LocalFolderStore(tmp_path / "revisions").get(revision.revision_path) == july_2010(close_on_20th=20.4)


def test_the_same_bytes_again_are_no_revision(tmp_path):
    job, _, index = sweep(tmp_path, FakeNseVix({PATH: july_2010()}))
    assert job.sweep([JULY]).revised == [] and index.for_path(PATH) == []


def test_an_error_page_is_listed_and_never_kept_as_a_version(tmp_path):
    job, _, index = sweep(tmp_path, FakeNseVix({PATH: b"<html>Service Temporarily Unavailable</html>"}))
    report = job.sweep([JULY])
    assert [m for m, _ in report.invalid] == [JULY] and index.for_path(PATH) == []


def test_no_answer_is_listed(tmp_path):
    for source in (FakeNseVix({}), Unreachable({})):
        job, _, _ = sweep(tmp_path, source)
        assert job.sweep([JULY]).unanswered == [JULY]


def test_a_last_modified_time_is_the_versions_time(tmp_path):
    class Stamped(FakeNseVix):
        def fetch_published(self, path):
            return PublishedFile(july_2010(close_on_20th=20.4), datetime(2026, 10, 14, 23, 0, tzinfo=IST))

    job, _, index = sweep(tmp_path, Stamped({}))
    job.sweep([JULY])
    assert index.for_path(PATH)[0].available_from == datetime(2026, 10, 14, 23, 0, tzinfo=IST)


def test_a_missing_original_is_named_not_passed_over(tmp_path):
    job, raw, index = sweep(tmp_path, FakeNseVix({PATH: july_2010(close_on_20th=20.4)}))
    (tmp_path / "raw" / PATH).unlink()
    report = job.sweep([JULY])
    assert report.not_archived == [JULY] and report.revised == [] and index.for_path(PATH) == []
    assert "original MISSING from the archive, nothing compared 2010-07" in report.lines()
