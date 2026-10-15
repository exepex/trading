"""Story A15: month files are archived with their manifest rows, a missing or failed download writes nothing and is
named, a stored file is never replaced, and a stopped run resumes with only what is missing."""

import hashlib
from datetime import date

from fno.storage.manifest_folder import Fingerprint, FingerprintingStore, ManifestFolder
from fno.storage.raw_store import LocalFolderStore
from fno.vix_history.librarian import VixHistoryLibrarian
from fno.vix_history.month_file import NseVixJsonReader
from fno.vix_history.source import NseVixHistorySource as Source
from tests.vix_history.nse_vix import FakeNseVix, august_2010, july_2010

JULY, AUGUST, SEPTEMBER = date(2010, 7, 1), date(2010, 8, 1), date(2010, 9, 1)
NSE = {Source.path_for(JULY): july_2010(), Source.path_for(AUGUST): august_2010()}


def librarian(tmp_path, source, fingerprints=None):
    raw = LocalFolderStore(tmp_path / "raw")
    manifests = ManifestFolder(tmp_path / "manifests")
    store = FingerprintingStore(raw, manifests, (Source,))
    fingerprints = {} if fingerprints is None else fingerprints
    return VixHistoryLibrarian(store, source, Source.path_for, NseVixJsonReader(), fingerprints, log=lambda _: None), (
        raw,
        manifests,
    )


def test_each_month_is_archived_with_its_manifest_row(tmp_path):
    lib, (raw, manifests) = librarian(tmp_path, FakeNseVix(NSE))
    report = lib.fill([JULY, AUGUST])
    assert report.uploaded == [JULY, AUGUST] and report.complete
    assert raw.get(Source.path_for(JULY)) == july_2010()
    rows = {f.day: f for f in manifests.read(Source)}
    assert rows[JULY].sha256 == hashlib.sha256(july_2010()).hexdigest()
    assert rows[JULY].url.endswith("vixhistory?from=01-07-2010&to=31-07-2010")


def test_a_missing_month_writes_nothing_and_is_named(tmp_path):
    lib, (raw, manifests) = librarian(tmp_path, FakeNseVix(NSE))
    report = lib.fill([JULY, SEPTEMBER])
    assert report.not_published == [SEPTEMBER] and not report.complete
    assert raw.get(Source.path_for(SEPTEMBER)) is None
    assert [f.day for f in manifests.read(Source)] == [JULY]
    assert "not published by the source 2010-09" in report.lines()


def test_an_answer_that_fails_the_check_is_not_saved(tmp_path):
    html = b"<html>Service Temporarily Unavailable</html>"
    lib, (raw, manifests) = librarian(tmp_path, FakeNseVix({Source.path_for(JULY): html}))
    report = lib.fill([JULY])
    assert [m for m, _ in report.rejected] == [JULY] and not report.complete
    assert raw.get(Source.path_for(JULY)) is None and manifests.read(Source) == []


def test_a_rerun_fetches_only_what_is_missing(tmp_path):
    first = FakeNseVix(NSE)
    librarian(tmp_path, first)[0].fill([JULY])
    again = FakeNseVix(NSE)
    lib, _ = librarian(tmp_path, again, {JULY: hashlib.sha256(july_2010()).hexdigest()})
    report = lib.fill([JULY, AUGUST])
    assert again.fetched == [Source.path_for(AUGUST)]
    assert report.present == [JULY] and report.uploaded == [AUGUST]


def test_a_stored_file_without_a_manifest_row_gets_its_row_without_a_fetch(tmp_path):
    LocalFolderStore(tmp_path / "raw").put(Source.path_for(JULY), july_2010())  # a run stopped before its row
    source = FakeNseVix(NSE)
    lib, (_, manifests) = librarian(tmp_path, source)
    assert lib.fill([JULY]).present == [JULY]
    assert source.fetched == [] and [f.day for f in manifests.read(Source)] == [JULY]


def test_a_stored_file_differing_from_its_manifest_is_reported_and_left_alone(tmp_path):
    LocalFolderStore(tmp_path / "raw").put(Source.path_for(JULY), july_2010(close_on_20th=99.0))
    source = FakeNseVix(NSE)
    lib, (raw, _) = librarian(tmp_path, source, {JULY: hashlib.sha256(july_2010()).hexdigest()})
    report = lib.fill([JULY])
    assert report.damaged == [(JULY, "SHA-256 differs from the manifest")] and not report.complete
    assert report.present == [] and report.uploaded == []
    assert raw.get(Source.path_for(JULY)) == july_2010(close_on_20th=99.0) and source.fetched == []


def test_a_manifest_conflict_after_the_save_is_named_not_a_crash(tmp_path):
    lib, (raw, manifests) = librarian(tmp_path, FakeNseVix(NSE))
    old = Fingerprint(JULY, Source.url_for(Source.path_for(JULY)), "0" * 64, 1)
    manifests.record(Source, old)  # a row from an earlier copy whose file is gone
    report = lib.fill([JULY])
    assert [m for m, _ in report.damaged] == [JULY] and report.uploaded == [] and not report.complete
