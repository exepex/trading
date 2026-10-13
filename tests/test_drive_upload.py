"""Story A9: the owner's Drive upload store (create, read, conflict, safe retries) and the owner's sign-in."""

import hashlib
import json

import pytest
import requests

from fno.storage.drive_session import DriveSession
from fno.storage.google_drive import DRIVE_FILES_URL, FOLDER_TYPE
from fno.storage.google_drive_upload import DRIVE_UPLOAD_URL, GENERATE_IDS_URL, GoogleDriveUploadStore
from fno.storage.owner_token import GOOGLE_TOKEN_URL, DriveSignInRefused, OwnerAccessToken
from fno.storage.raw_store import RawFileConflict, StoredCopyDamaged

PATH = "nse/derivatives/participant-oi/2019/01/fao_participant_oi_01012019.csv"


class Answer:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code, self.body, self.content = status, body, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code), response=self)

    def json(self):
        return self.body


class InMemoryDrive:
    """Drive's file API in memory: folders and files by ID, IDs reserved with generateIds, 409 on a reused ID.
    `drop_after_create` loses the answer to that many creates after Drive has made them (a dropped connection)."""

    def __init__(self, drop_after_create=0, corrupt=False):
        self.headers, self.items, self.next_id = {}, {}, 0
        self.drop_after_create, self.corrupt, self.creates = drop_after_create, corrupt, []

    def get(self, url, params=None, timeout=None):
        if url == GENERATE_IDS_URL:
            ids = [f"id{self.next_id + n}" for n in range(params["count"])]
            self.next_id += params["count"]
            return Answer(body={"ids": ids})
        if url == DRIVE_FILES_URL:
            q = params["q"]
            parent, name, folder = q.split("'")[1], q.split("'")[3], "mimeType = " in q
            found = [
                {"id": i, "name": n} for i, (p, n, f, _) in self.items.items() if (p, n, f) == (parent, name, folder)
            ]
            return Answer(body={"files": found})
        return Answer(content=self.items[url.rsplit("/", 1)[1]][3])

    def post(self, url, json=None, files=None, params=None, timeout=None):
        if url == DRIVE_FILES_URL:
            meta, folder, data = json, True, b""
            assert meta["mimeType"] == FOLDER_TYPE
        else:
            assert url == DRIVE_UPLOAD_URL
            meta, folder, data = _metadata(files), False, files["file"][1]
        if meta["id"] in self.items:
            return Answer(409, {"error": {"errors": [{"reason": "fileIdInUse"}]}})
        self.items[meta["id"]] = (meta["parents"][0], meta["name"], folder, data)
        self.creates.append(meta["name"])
        if self.drop_after_create:
            self.drop_after_create -= 1
            raise requests.ConnectionError("connection reset after the create")
        md5 = hashlib.md5(b"other" if self.corrupt else data).hexdigest()
        return Answer(body={"id": meta["id"], "md5Checksum": md5})


def _metadata(files):
    return json.loads(files["metadata"][1])


def store_on(drive):
    return GoogleDriveUploadStore("root", lambda: "token", drive, sleep=lambda s: None)


def test_a_file_is_saved_in_the_archive_tree_and_read_back_byte_identical():
    drive = InMemoryDrive()
    store = store_on(drive)
    assert store.get(PATH) is None
    store.put(PATH, b"csv bytes")
    assert store.get(PATH) == b"csv bytes"
    assert drive.creates == ["nse", "derivatives", "participant-oi", "2019", "01", "fao_participant_oi_01012019.csv"]
    store.put(PATH.replace("01012019", "02012019"), b"day two")  # the folders are reused, not made twice
    assert drive.creates[-1] == "fao_participant_oi_02012019.csv" and len(drive.creates) == 7


def test_the_same_bytes_again_change_nothing_and_different_bytes_are_refused():
    drive = InMemoryDrive()
    store = store_on(drive)
    store.put(PATH, b"original")
    store.put(PATH, b"original")
    assert len(drive.creates) == 6
    with pytest.raises(RawFileConflict):
        store.put(PATH, b"changed")
    assert len(drive.creates) == 6 and store_on(drive).get(PATH) == b"original"


def test_a_file_another_writer_saved_after_our_lookup_is_still_found():
    drive = InMemoryDrive()
    first, second = store_on(drive), store_on(drive)
    assert second.get(PATH) is None  # second now remembers "absent"
    first.put(PATH, b"original")
    with pytest.raises(RawFileConflict):
        second.put(PATH, b"changed")
    second.put(PATH, b"original")
    assert drive.creates.count("fao_participant_oi_01012019.csv") == 1
    assert drive.creates.count("nse") == 1  # folders looked up again before creating: no twin folders


def test_a_create_retried_after_a_dropped_connection_never_makes_a_second_copy():
    drive = InMemoryDrive(drop_after_create=6)  # every create's answer is lost once
    store = store_on(drive)
    store.put(PATH, b"csv bytes")
    assert len(drive.creates) == 6  # each retry got 409 "fileIdInUse" instead of a duplicate
    assert store_on(drive).get(PATH) == b"csv bytes"


def test_bytes_that_drive_reports_differently_are_never_trusted():
    with pytest.raises(StoredCopyDamaged):
        store_on(InMemoryDrive(corrupt=True)).put(PATH, b"csv bytes")


def test_ids_are_reserved_in_batches():
    drive = InMemoryDrive()
    store = store_on(drive)
    store.put(PATH, b"a")
    store.put(PATH.replace("01012019", "02012019"), b"b")
    assert drive.next_id == 100  # one generateIds call for 7 items


class Uploads:
    """A session that answers posts from a list (statuses or exceptions)."""

    def __init__(self, answers):
        self.headers, self.answers, self.calls = {}, list(answers), 0

    def post(self, url, timeout=None, **kwargs):
        self.calls += 1
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, Answer) else Answer(answer, {})


def test_uploads_share_the_drive_sign_in_and_retry_rules():
    tokens, waits = iter(["old", "new"]), []
    session = Uploads([401, 503, requests.ConnectionError("reset"), 200])
    drive = DriveSession(lambda: next(tokens), session, sleep=waits.append)
    assert drive.post("u").status_code == 200
    assert session.headers["Authorization"] == "Bearer new" and waits == [2, 8] and session.calls == 4
    assert DriveSession(lambda: "t", Uploads([409])).post("u", accept=frozenset({409})).status_code == 409
    with pytest.raises(requests.HTTPError):
        DriveSession(lambda: "t", Uploads([409])).post("u")


class TokenEndpoint:
    def __init__(self, status, body):
        self.status, self.body, self.form = status, body, None

    def post(self, url, data=None, timeout=None):
        assert url == GOOGLE_TOKEN_URL
        self.form = data
        return Answer(self.status, self.body)


def test_the_owner_sign_in_swaps_the_refresh_token_for_an_access_token():
    endpoint = TokenEndpoint(200, {"access_token": "access-1"})
    assert OwnerAccessToken("cid", "secret", "refresh", endpoint)() == "access-1"
    assert endpoint.form["grant_type"] == "refresh_token" and endpoint.form["refresh_token"] == "refresh"


@pytest.mark.parametrize(
    "status, body, reason",
    [
        (400, {"error": "invalid_grant", "error_description": "Token has been expired or revoked."}, "invalid_grant"),
        (401, {"error": "invalid_client"}, "invalid_client"),
        (400, {"error": "secret-value with spaces"}, "no error code"),  # never echoes free text
    ],
)
def test_a_refused_sign_in_names_googles_error_code_and_nothing_else(status, body, reason):
    with pytest.raises(DriveSignInRefused) as refused:
        OwnerAccessToken("cid-value", "secret-value", "refresh-value", TokenEndpoint(status, body))()
    assert refused.value.reason == reason
    assert not any(v in str(refused.value) for v in ("cid-value", "secret-value", "refresh-value"))


class RateLimited(Answer):
    def __init__(self, reason):
        super().__init__(403, {"error": {"errors": [{"reason": reason}]}})


def test_googles_403_rate_limit_is_retried_but_a_real_403_is_raised_at_once():
    waits = []
    session = Uploads([RateLimited("userRateLimitExceeded"), RateLimited("rateLimitExceeded"), 200])
    assert DriveSession(lambda: "t", session, sleep=waits.append).post("u").status_code == 200 and waits == [2, 8]
    refused = Uploads([RateLimited("insufficientFilePermissions")])
    with pytest.raises(requests.HTTPError):
        DriveSession(lambda: "t", refused, sleep=waits.append).post("u")
    assert waits == [2, 8]


def test_a_drive_error_names_googles_reason():
    with pytest.raises(requests.HTTPError, match="Google: insufficientFilePermissions"):
        DriveSession(lambda: "t", Uploads([RateLimited("insufficientFilePermissions")])).post("u")
