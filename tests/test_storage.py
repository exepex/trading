"""Raw files: stores (local folder, read-only Google Drive), sources (NSE archive) and the library over both."""

from datetime import date

import pytest
import requests

from fno.constants import ENV_GDRIVE_FOLDER_ID, ENV_GDRIVE_SERVICE_ACCOUNT_JSON
from fno.storage.google_drive import DRIVE_FILES_URL, GoogleDriveStore
from fno.storage.raw_library import RawFile, RawFileLibrary
from fno.storage.raw_source import NseDailyFoSource, RawFileSource, RawSourceUnavailable
from fno.storage.raw_store import LocalFolderStore, RawFileConflict, ReadOnlyStoreError, path_parts
from fno.storage.wiring import build_raw_stores


class Response:
    def __init__(self, body=None, content=b""):
        self.body, self.content = body, content

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class FakeDrive:
    """A Drive tree: root -> nse -> derivatives -> fo-bhavcopy -> 2024 -> 01 -> one file (and a duplicate name)."""

    TREE = {
        ("root", "nse", True): ["f1"],
        ("f1", "derivatives", True): ["f2"],
        ("f2", "fo-bhavcopy", True): ["f3"],
        ("f3", "2024", True): ["f4"],
        ("f4", "01", True): ["f5"],
        ("f5", "a.zip", False): ["file-a"],
        ("f5", "twice.zip", False): ["x", "y"],
    }

    def __init__(self):
        self.headers, self.queries = {}, []

    def get(self, url, params=None, timeout=None):
        if url != DRIVE_FILES_URL:
            return Response(content=b"bytes of " + url.rsplit("/", 1)[1].encode())
        q = params["q"]
        self.queries.append(q)
        parent, name = q.split("'")[1], q.split("'")[3]
        ids = self.TREE.get((parent, name, "mimeType = " in q), [])
        return Response({"files": [{"id": i, "name": name} for i in ids]})


def test_local_folder_keeps_the_archive_tree_and_never_overwrites(tmp_path):
    store, path = LocalFolderStore(tmp_path / "raw"), "nse/derivatives/fo-bhavcopy/2024/01/a.zip"
    assert store.get(path) is None
    store.put(path, b"data")
    store.put(path, b"data")  # the same bytes again: nothing happens
    assert store.get(path) == b"data" and (tmp_path / "raw" / "nse/derivatives/fo-bhavcopy/2024/01/a.zip").is_file()
    assert [p.name for p in (tmp_path / "raw/nse/derivatives/fo-bhavcopy/2024/01").iterdir()] == ["a.zip"]
    with pytest.raises(RawFileConflict):
        store.put(path, b"other")
    assert store.get(path) == b"data"


@pytest.mark.parametrize("bad", ["", "/abs/a.zip", "nse//a.zip", "nse/../a.zip", "./a.zip"])
def test_archive_paths_must_be_plain_relative_paths(bad):
    with pytest.raises(ValueError):
        path_parts(bad)


class CountingSource(RawFileSource):
    name = "origin"

    def __init__(self, files):
        self.files, self.asked = files, []

    def fetch(self, filename):
        self.asked.append(filename)
        return self.files.get(filename)


def test_library_uses_a_stored_copy_first_and_archives_what_it_fetches(tmp_path):
    stored, archive = LocalFolderStore(tmp_path / "drive"), LocalFolderStore(tmp_path / "keep")
    stored.put("d/2024/01/old.zip", b"stored")
    source = CountingSource({"d/2024/01/old.zip": b"origin", "d/2024/02/new.zip": b"fresh"})
    library = RawFileLibrary([stored], source, archive)
    assert library.get("d/2024/01/old.zip") == RawFile(b"stored", "local folder") and source.asked == []
    assert library.get("d/2024/02/new.zip") == RawFile(b"fresh", "origin")
    assert archive.get("d/2024/02/new.zip") == b"fresh"
    assert library.get("d/2024/03/holiday.zip") == RawFile(None, "origin")
    assert archive.get("d/2024/03/holiday.zip") is None


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
    path = NseDailyFoSource.path_for(date(2026, 10, 9))
    assert path == "nse/derivatives/fo-bhavcopy/2026/10/BhavCopy_NSE_FO_0_0_0_20261009_F_0000.csv.zip"
    assert NseDailyFoSource.url_for(path).endswith("/content/fo/BhavCopy_NSE_FO_0_0_0_20261009_F_0000.csv.zip")
    waits = []
    session = Flaky([requests.ConnectionError("reset"), Answer(200, b"zip")])
    source = NseDailyFoSource(session, sleep=waits.append)
    assert source.fetch("f.zip") == b"zip" and waits == [5] and session.urls[0].endswith("/content/fo/f.zip")
    assert NseDailyFoSource(Flaky([Answer(404)]), sleep=waits.append).fetch("f.zip") is None
    down = NseDailyFoSource(Flaky([requests.ConnectionError("down")] * 4), sleep=waits.append)
    with pytest.raises(RawSourceUnavailable):
        down.fetch("f.zip")


def test_drive_walks_the_same_tree_folder_by_folder_and_never_writes():
    session = FakeDrive()
    store = GoogleDriveStore("root", "token", session)
    assert session.headers["Authorization"] == "Bearer token"
    assert store.get("nse/derivatives/fo-bhavcopy/2024/01/a.zip") == b"bytes of file-a"
    assert len(session.queries) == 6 and "'root' in parents" in session.queries[0]
    assert store.get("nse/derivatives/fo-bhavcopy/2024/01/a.zip") == b"bytes of file-a"
    assert len(session.queries) == 6  # folder and file IDs are cached
    assert store.get("nse/derivatives/fo-bhavcopy/2024/02/a.zip") is None  # no such month folder
    with pytest.raises(RawFileConflict):
        store.get("nse/derivatives/fo-bhavcopy/2024/01/twice.zip")
    with pytest.raises(ReadOnlyStoreError):
        store.put("nse/derivatives/fo-bhavcopy/2024/01/c.zip", b"data")


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
