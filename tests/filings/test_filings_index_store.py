"""Story A12: index files are rewritten in place (Drive keeps the file's ID); raw files never are."""

import hashlib

from fno.storage.google_drive_upload import GoogleDriveUploadStore
from fno.storage.index_store import DriveIndexStore, LocalIndexStore


class Answer:
    status_code = 200

    def __init__(self, body=None, content=b""):
        self.body, self.content = body, content

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class OneFileDrive:
    """A Drive holding folder `index` and, once created, file `progress.json` in it."""

    def __init__(self):
        self.headers, self.data, self.patched = {}, None, []

    def get(self, url, params=None, timeout=None):
        q = (params or {}).get("q", "")
        if "name = 'index'" in q:
            return Answer({"files": [{"id": "F", "name": "index"}]})
        if "name = 'progress.json'" in q:
            return Answer({"files": [{"id": "P", "name": "progress.json"}] if self.data is not None else []})
        if url.endswith("/generateIds"):
            return Answer({"ids": ["P"]})
        return Answer(content=self.data)

    def post(self, url, json=None, files=None, params=None, timeout=None):
        self.data = files["file"][1]
        return Answer({"id": "P", "md5Checksum": hashlib.md5(self.data).hexdigest()})

    def patch(self, url, params=None, data=None, headers=None, timeout=None):
        self.data = data
        self.patched.append(url.rsplit("/", 1)[-1])
        return Answer({"md5Checksum": hashlib.md5(data).hexdigest()})


def test_drive_index_file_is_created_then_rewritten_in_place():
    drive = OneFileDrive()
    store = DriveIndexStore(GoogleDriveUploadStore("root", lambda: "t", drive, sleep=lambda s: None), "index")
    store.replace("progress.json", b'{"step": 1}')
    store.replace("progress.json", b'{"step": 2}')
    assert drive.patched == ["P"] and store.get("progress.json") == b'{"step": 2}'


def test_local_index_file_is_replaced(tmp_path):
    store = LocalIndexStore(tmp_path)
    assert store.get("a/p.json") is None
    store.replace("a/p.json", b"1")
    store.replace("a/p.json", b"2")
    assert store.get("a/p.json") == b"2"
