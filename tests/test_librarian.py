"""Story A9: the librarian fills a dataset's gaps from its source, verified against the manifest, and resumes after a
stop; a refused Drive sign-in gives a clear error and an alert naming the fix, with no credential in the output."""

import hashlib
from datetime import date

import pytest

from fno.alerts.sender import AlertSender
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage import wiring
from fno.storage.coverage import CoverageDataset
from fno.storage.librarian import RawDataLibrarian, fill_report_lines
from fno.storage.librarian_cli import run_librarian
from fno.storage.manifest_commit import NOTHING, ManifestRecorder
from fno.storage.manifest_folder import FingerprintingStore
from fno.storage.owner_token import DriveSignInRefused, OwnerAccessToken
from fno.storage.raw_source import ParticipantOiSource, RawSourceUnavailable
from fno.storage.raw_store import AreaStore, LocalFolderStore

SOURCE_URL = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-02,holiday,Gandhi Jayanti,{SOURCE_URL}\n")
DAYS = [date(2026, 10, 1), date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 7)]  # sessions 1-7 Oct 2026


def file_for(day: date) -> bytes:
    return f"participant oi for {day}".encode()


def accept_any(filename, data):
    return None


MANIFEST = {ParticipantOiSource.filename_for(d): hashlib.sha256(file_for(d)).hexdigest() for d in DAYS}
VERIFY = CoverageDataset(ParticipantOiSource, accept_any, MANIFEST)


class FakeNse(ParticipantOiSource):
    """NSE's archive in memory; `fail_after` raises RawSourceUnavailable once that many files were served."""

    def __init__(self, files, fail_after=None):
        super().__init__(session=None)
        self.files, self.fail_after, self.asked = files, fail_after, []

    def fetch(self, path):
        if self.fail_after is not None and len(self.asked) >= self.fail_after:
            raise RawSourceUnavailable("NSE archive: connection refused")
        self.asked.append(path)
        return self.files.get(path)


class RecordingStore(LocalFolderStore):
    def __init__(self, folder):
        super().__init__(folder)
        self.saved = []

    def put(self, path, data):
        self.saved.append(path)
        super().put(path, data)


def nse_with(days):
    return {ParticipantOiSource.path_for(d): file_for(d) for d in days}


def librarian(store, source, exceptions=None):
    return RawDataLibrarian(store, source, VERIFY, CALENDAR, exceptions or {}, log=lambda line: None)


def test_missing_files_are_fetched_verified_and_saved_and_present_ones_kept(tmp_path):
    store = RecordingStore(tmp_path)
    store.put(ParticipantOiSource.path_for(DAYS[0]), file_for(DAYS[0]))
    source = FakeNse(nse_with(DAYS))
    report = librarian(store, source).fill(date(2026, 10, 1), date(2026, 10, 7))
    assert report.sessions == 4 and report.present == 1 and report.uploaded == DAYS[1:] and report.complete
    assert source.asked == [ParticipantOiSource.path_for(d) for d in DAYS[1:]]  # the stored day is not fetched
    assert all(store.get(ParticipantOiSource.path_for(d)) == file_for(d) for d in DAYS)
    assert fill_report_lines(report)[-1] == "result: complete"


def test_a_file_that_differs_from_the_manifest_is_never_saved_and_a_damaged_copy_never_replaced(tmp_path):
    store = RecordingStore(tmp_path)
    store.put(ParticipantOiSource.path_for(DAYS[0]), b"damaged copy")
    files = nse_with(DAYS) | {ParticipantOiSource.path_for(DAYS[1]): b"not NSE's original"}
    report = librarian(store, FakeNse(files)).fill(date(2026, 10, 1), date(2026, 10, 7))
    assert [d for d, _ in report.damaged] == [DAYS[0]] and [d for d, _ in report.rejected] == [DAYS[1]]
    assert store.get(ParticipantOiSource.path_for(DAYS[0])) == b"damaged copy"
    assert store.get(ParticipantOiSource.path_for(DAYS[1])) is None and not report.complete
    assert "SHA-256 differs from the manifest" in report.rejected[0][1]


def test_sessions_without_a_file_are_reported_unless_a_sourced_exception_explains_them(tmp_path):
    exceptions = {(ParticipantOiSource.dataset, DAYS[2]): "NSE published no file (circular)"}
    report = librarian(LocalFolderStore(tmp_path), FakeNse(nse_with(DAYS[:2])), exceptions).fill(DAYS[0], DAYS[-1])
    assert report.excepted == 1 and report.not_published == [DAYS[3]] and not report.complete


def test_a_stopped_run_restarted_uploads_only_what_is_missing(tmp_path):
    store = RecordingStore(tmp_path)
    with pytest.raises(RawSourceUnavailable):
        librarian(store, FakeNse(nse_with(DAYS), fail_after=2)).fill(DAYS[0], DAYS[-1])
    assert len(store.saved) == 2
    resumed = FakeNse(nse_with(DAYS))
    report = librarian(store, resumed).fill(DAYS[0], DAYS[-1])
    assert resumed.asked == [ParticipantOiSource.path_for(d) for d in DAYS[2:]]
    assert report.present == 2 and report.uploaded == DAYS[2:] and len(store.saved) == 4


class NoNewRows(ManifestRecorder):
    def pending(self):
        return []

    def commit(self, what):
        return NOTHING


class SentAlerts(AlertSender):
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


class Refusal:
    status_code = 400

    def json(self):
        return {"error": "invalid_grant", "error_description": "Token has been expired or revoked."}


class RefusingGoogle:
    def post(self, url, data=None, timeout=None):
        return Refusal()


SECRETS = {"client_id": "cid-7f3a", "client_secret": "csecret-9b1c", "refresh_token": "rtoken-4d2e"}


def test_a_refused_sign_in_stops_with_a_clear_error_and_an_alert_naming_the_fix(tmp_path):
    def build():
        token = OwnerAccessToken(**SECRETS, session=RefusingGoogle())
        return librarian(wiring.GoogleDriveUploadStore("folder", token), FakeNse({}))

    alerts, out = SentAlerts(), []
    assert run_librarian(build, alerts, NoNewRows(), "test", DAYS[0], DAYS[-1], out=out.append) == 1
    assert len(alerts.sent) == 1 and "invalid_grant" in alerts.sent[0]
    assert "tools/gdrive_oauth_setup.py" in alerts.sent[0] and "FNO_GDRIVE_OAUTH_REFRESH_TOKEN" in alerts.sent[0]
    assert out == [alerts.sent[0], "alert sent to #fno-desk", NOTHING]
    printed = "\n".join(out + alerts.sent)
    assert not any(value in printed for value in SECRETS.values())


def test_a_refusal_midway_is_raised_too_never_skipped(tmp_path):
    class Refuses(LocalFolderStore):
        def put(self, path, data):
            raise DriveSignInRefused("invalid_grant")

    alerts, out = SentAlerts(), []
    build = lambda: librarian(Refuses(tmp_path), FakeNse(nse_with(DAYS)))  # noqa: E731
    assert (
        run_librarian(build, alerts, NoNewRows(), "test", DAYS[0], DAYS[-1], out=out.append) == 1
        and len(alerts.sent) == 1
    )


def test_a_source_outage_stops_the_run_and_says_how_to_resume(tmp_path):
    out = []
    build = lambda: librarian(LocalFolderStore(tmp_path), FakeNse(nse_with(DAYS), fail_after=0))  # noqa: E731
    assert run_librarian(build, SentAlerts(), NoNewRows(), "test", DAYS[0], DAYS[-1], out=out.append) == 1
    assert out[0].startswith("stopped: NSE archive: connection refused") and "resume" in out[0]


OWNER_ENV = {
    "FNO_GDRIVE_FOLDER_ID": "folder123",
    "FNO_GDRIVE_OAUTH_CLIENT_ID": "cid",
    "FNO_GDRIVE_OAUTH_CLIENT_SECRET": "secret",
    "FNO_GDRIVE_OAUTH_REFRESH_TOKEN": "refresh",
}


def test_drive_uploads_are_wired_only_when_all_four_settings_exist(monkeypatch):
    monkeypatch.setattr(OwnerAccessToken, "__call__", lambda self: "access")
    for missing in OWNER_ENV:
        assert wiring.build_owner_drive_store({k: v for k, v in OWNER_ENV.items() if k != missing}) is None
    store = wiring.build_owner_drive_store(OWNER_ENV)
    assert isinstance(store, FingerprintingStore) and store.manifests.folder == wiring.MANIFEST_FOLDER
    drive = store.store
    assert isinstance(drive, AreaStore) and drive.area == wiring.RAW_AREA and drive.store.folder_id == "folder123"


def test_the_library_archives_fetched_files_straight_to_drive_when_uploads_are_set_up(monkeypatch, tmp_path):
    monkeypatch.setattr(OwnerAccessToken, "__call__", lambda self: "access")
    for name, value in OWNER_ENV.items():
        monkeypatch.setenv(name, value)
    library = wiring.build_participant_oi_library(tmp_path)
    drive = library.archive.store  # FingerprintingStore -> AreaStore -> the upload store
    assert isinstance(drive.store, wiring.GoogleDriveUploadStore) and drive.area == wiring.RAW_AREA
    assert set(wiring.LIBRARIAN_DATASETS) == {  # each added by its own story (A9, A10, P6, A14, A23)
        "participant-oi",
        "participant-volume",
        "fii-stats",
        "index-close",
        "cm-bhavcopy",
        "security-delivery",
        "fo-bhavcopy",
        "span-bod",
    }
    with pytest.raises(RuntimeError, match="FNO_GDRIVE_OAUTH_REFRESH_TOKEN"):
        monkeypatch.delenv("FNO_GDRIVE_OAUTH_REFRESH_TOKEN")
        wiring.build_librarian("participant-oi")
