"""Drive's v3 file API in memory, at the HTTP level the real adapters use (story DR1-c: a fake remote, never a fake
store): queries by parent, name and folder type, downloads, creates under reserved IDs, moves and renames. Unlike
the real path-based store it lets a test make two items with one name, the state a race leaves."""

from __future__ import annotations

import hashlib
import json
import re

import requests

from fno.storage.google_drive import DRIVE_FILES_URL, FOLDER_TYPE
from fno.storage.google_drive_upload import GENERATE_IDS_URL, GoogleDriveUploadStore

PARENT, NAME = re.compile(r"'([^']*)' in parents"), re.compile(r"name = '((?:[^'\\]|\\.)*)'")
MIME = re.compile(r"mimeType (=|!=) '")


class Answer:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code, self.body, self.content = status, body, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code), response=self)

    def json(self):
        return self.body


class FakeDrive:
    def __init__(self):
        self.headers, self.items, self.next_id, self.clock = {}, {}, 0, 0

    def add(self, parent: str, name: str, data: bytes | None = None) -> str:
        """A folder (no data) or a file, even beside one of the same name; returns its ID."""
        item_id = self._new_id()
        self.clock += 1
        created = f"2026-10-22T10:03:{self.clock:02d}.000Z"
        self.items[item_id] = {"parent": parent, "name": name, "data": data, "created": created}
        return item_id

    def named(self, parent: str, name: str) -> list[str]:
        return [i for i, item in self.items.items() if (item["parent"], item["name"]) == (parent, name)]

    def get(self, url, params=None, timeout=None):
        if url == GENERATE_IDS_URL:
            return Answer(body={"ids": [self._new_id() for _ in range(params["count"])]})
        if url == DRIVE_FILES_URL:
            return Answer(body={"files": [self._answer(i) for i in self._query(params["q"])]})
        return Answer(content=self.items[url.rsplit("/", 1)[1]]["data"])

    def post(self, url, json=None, files=None, params=None, timeout=None):
        meta = json if url == DRIVE_FILES_URL else _metadata(files)
        data = None if url == DRIVE_FILES_URL else files["file"][1]
        self.clock += 1
        created = f"2026-10-23T12:00:{self.clock:02d}.000Z"
        self.items[meta["id"]] = {"parent": meta["parents"][0], "name": meta["name"], "data": data, "created": created}
        md5 = hashlib.md5(data or b"").hexdigest()  # noqa: S324 - Drive's transfer checksum
        return Answer(body={"id": meta["id"], "md5Checksum": md5})

    def patch(self, url, params=None, json=None, timeout=None, **kwargs):
        item = self.items[url.rsplit("/", 1)[1]]
        if params.get("addParents"):
            assert item["parent"] == params["removeParents"]
            item["parent"] = params["addParents"]
        if json and "name" in json:
            item["name"] = json["name"]
        return Answer(body={"id": url.rsplit("/", 1)[1]})

    def _query(self, q: str) -> list[str]:
        parent, name, mime = PARENT.search(q).group(1), NAME.search(q), MIME.search(q)
        found = [i for i, item in self.items.items() if item["parent"] == parent]
        if name:
            found = [i for i in found if self.items[i]["name"] == name.group(1).replace("\\'", "'")]
        if mime:
            want_folder = mime.group(1) == "="
            found = [i for i in found if (self.items[i]["data"] is None) == want_folder]
        return found

    def _answer(self, item_id: str) -> dict:
        item = self.items[item_id]
        answer = {"id": item_id, "name": item["name"], "createdTime": item["created"]}
        answer["mimeType"] = FOLDER_TYPE if item["data"] is None else "application/json"
        if item["data"] is not None:
            answer["md5Checksum"] = hashlib.md5(item["data"]).hexdigest()  # noqa: S324
        return answer

    def _new_id(self) -> str:
        self.next_id += 1
        return f"id{self.next_id}"


def _metadata(files):
    return json.loads(files["metadata"][1])


def store_on(drive: FakeDrive) -> GoogleDriveUploadStore:
    return GoogleDriveUploadStore("root", lambda: "token", drive, sleep=lambda s: None)
