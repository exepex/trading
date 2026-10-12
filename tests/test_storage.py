"""Raw files: stores (local folder, read-only Google Drive), sources (NSE archive) and the library over both."""

from datetime import date

import pytest
import requests

from fno.constants import ENV_GDRIVE_FOLDER_ID, ENV_GDRIVE_SERVICE_ACCOUNT_JSON
from fno.storage.google_drive import DRIVE_FILES_URL, GoogleDriveStore
from fno.storage.raw_library import RawFile, RawFileLibrary
from fno.storage.raw_source import NseDailyFoSource, RawFileSource, RawSourceUnavailable
from fno.storage.raw_store import LocalFolderStore, ReadOnlyStoreError
from fno.storage.wiring import build_raw_stores


class Response:
    def __init__(self, body=None, content=b""):
        self.body, self.content = body, content

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class FakeDrive:
    """Two pages of folder listing and one downloadable file."""

    def __init__(self):
        self.headers, self.calls = {}, []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params or {})))
        if url == DRIVE_FILES_URL and "pageToken" not in params:
            return Response({"files": [{"id": "1", "name": "a.zip"}], "nextPageToken": "p2"})
        if url == DRIVE_FILES_URL:
            return Response({"files": [{"id": "2", "name": "b.zip"}]})
        return Response(content=b"bytes of " + url.rsplit("/", 1)[1].encode())


def test_local_folder_saves_whole_files_and_reads_them_back(tmp_path):
    store = LocalFolderStore(tmp_path / "raw")
    assert store.get("x.zip") is None
    store.put("x.zip", b"data")
    assert store.get("x.zip") == b"data" and [p.name for p in (tmp_path / "raw").iterdir()] == ["x.zip"]


class CountingSource(RawFileSource):
    name = "origin"

    def __init__(self, files):
        self.files, self.asked = files, []

    def fetch(self, filename):
        self.asked.append(filename)
        return self.files.get(filename)


def test_library_uses_a_stored_copy_first_and_archives_what_it_fetches(tmp_path):
    stored, archive = LocalFolderStore(tmp_path / "drive"), LocalFolderStore(tmp_path / "keep")
    stored.put("old.zip", b"stored")
    source = CountingSource({"old.zip": b"origin", "new.zip": b"fresh"})
    library = RawFileLibrary([stored], source, archive)
    assert library.get("old.zip") == RawFile(b"stored", "local folder") and source.asked == []
    assert library.get("new.zip") == RawFile(b"fresh", "origin") and archive.get("new.zip") == b"fresh"
    assert library.get("holiday.zip") == RawFile(None, "origin") and archive.get("holiday.zip") is None


class Answer:
    def __init__(self, status, content=b""):
        self.status_code, self.content = status, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class Flaky:
    def __init__(self, answers):
        self.answers, self.urls = list(answers), []

    def get(self, url, timeout=None):
        self.urls.append(url)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_nse_source_names_files_retries_drops_and_reports_holidays():
    assert NseDailyFoSource.filename_for(date(2026, 10, 9)) == "BhavCopy_NSE_FO_0_0_0_20261009_F_0000.csv.zip"
    waits = []
    session = Flaky([requests.ConnectionError("reset"), Answer(200, b"zip")])
    source = NseDailyFoSource(session, sleep=waits.append)
    assert source.fetch("f.zip") == b"zip" and waits == [5] and session.urls[0].endswith("/content/fo/f.zip")
    assert NseDailyFoSource(Flaky([Answer(404)]), sleep=waits.append).fetch("f.zip") is None
    down = NseDailyFoSource(Flaky([requests.ConnectionError("down")] * 4), sleep=waits.append)
    with pytest.raises(RawSourceUnavailable):
        down.fetch("f.zip")


def test_drive_lists_every_page_downloads_by_id_and_never_writes():
    session = FakeDrive()
    store = GoogleDriveStore("folder123", "token", session)
    assert session.headers["Authorization"] == "Bearer token"
    assert store.get("b.zip") == b"bytes of 2" and store.get("missing.zip") is None
    listings = [p for url, p in session.calls if url == DRIVE_FILES_URL]
    assert len(listings) == 2 and "'folder123' in parents" in listings[0]["q"]  # listed once, both pages
    with pytest.raises(ReadOnlyStoreError):
        store.put("c.zip", b"data")


def test_drive_is_used_only_when_both_settings_exist(tmp_path, monkeypatch):
    monkeypatch.delenv(ENV_GDRIVE_SERVICE_ACCOUNT_JSON, raising=False)
    monkeypatch.delenv(ENV_GDRIVE_FOLDER_ID, raising=False)
    assert build_raw_stores() == []
    assert [s.name for s in build_raw_stores(tmp_path)] == ["local folder"]
    monkeypatch.setenv(ENV_GDRIVE_SERVICE_ACCOUNT_JSON, '{"type": "service_account"}')
    assert [s.name for s in build_raw_stores(tmp_path, token_for=lambda key: "t")] == ["local folder"]
    monkeypatch.setenv(ENV_GDRIVE_FOLDER_ID, "folder123")
    stores = build_raw_stores(tmp_path, token_for=lambda key: "t")
    assert [s.name for s in stores] == ["local folder", "Google Drive"] and stores[1].folder_id == "folder123"
