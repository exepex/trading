"""Story A12: a Drive folder's files and MD5s from its listing (Drive's own checksums, two pages)."""

import pytest

from fno.storage.google_drive import GoogleDriveStore
from fno.storage.raw_store import RawFileConflict


class Answer:
    status_code = 200

    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class ListingDrive:
    """Folders a/b under the root; folder b lists `pages` of files."""

    def __init__(self, pages):
        self.headers, self.pages = {}, pages

    def get(self, url, params=None, timeout=None):
        q = params["q"]
        if "name = 'a'" in q:
            return Answer({"files": [{"id": "A", "name": "a"}]})
        if "name = 'b'" in q:
            return Answer({"files": [{"id": "B", "name": "b"}]})
        if "name = " in q:
            return Answer({"files": []})
        assert q.startswith("'B' in parents")
        if "mimeType = " in q:
            return Answer({"files": [{"name": "2025"}, {"name": "2024"}]})
        page = int(params.get("pageToken", 0))
        body = {"files": self.pages[page]}
        if page + 1 < len(self.pages):
            body["nextPageToken"] = str(page + 1)
        return Answer(body)


def drive(pages):
    return GoogleDriveStore("root", lambda: "token", ListingDrive(pages), sleep=lambda s: None)


def test_lists_every_page_with_md5():
    pages = [[{"name": "x.xml", "md5Checksum": "m1"}], [{"name": "y.xml", "md5Checksum": "m2"}]]
    assert drive(pages).checksums("a/b") == {"x.xml": "m1", "y.xml": "m2"}


def test_a_missing_folder_lists_nothing():
    assert drive([]).checksums("a/missing") == {}


def test_two_files_with_one_name_are_refused():
    pages = [[{"name": "x.xml", "md5Checksum": "m1"}, {"name": "x.xml", "md5Checksum": "m2"}]]
    with pytest.raises(RawFileConflict):
        drive(pages).checksums("a/b")


def test_lists_the_folders_inside_a_folder():
    assert drive([]).folders("a/b") == ["2024", "2025"]
