"""`python -m fno drive-check` messages (no network, no secrets printed)."""

import json

import requests

from fno.constants import ENV_GDRIVE_FOLDER_ID, ENV_GDRIVE_SERVICE_ACCOUNT_JSON
from fno.storage.drive_check import drive_check_lines

KEY = json.dumps({"type": "service_account", "project_id": "fno-research", "private_key": "SECRET-VALUE"})
ENV = {ENV_GDRIVE_SERVICE_ACCOUNT_JSON: KEY, ENV_GDRIVE_FOLDER_ID: "folder123"}


class Reply:
    def __init__(self, status, body=None):
        self.status_code, self.body = status, body or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code), response=self)

    def json(self):
        return self.body


class Drive:
    def __init__(self, status=200, children=()):
        self.headers, self.status, self.children = {}, status, children

    def get(self, url, params=None, timeout=None):
        if url.endswith("/folder123"):
            return Reply(self.status, {"name": "fno-research"})
        return Reply(200, {"files": [{"name": n} for n in self.children]})


def lines(env=ENV, drive=None):
    return drive_check_lines(env, token_for=lambda key: "token", session=drive or Drive())


def test_missing_settings_are_named():
    assert lines({}) == [f"not set: {ENV_GDRIVE_SERVICE_ACCOUNT_JSON}, {ENV_GDRIVE_FOLDER_ID}"]


def test_an_unreadable_key_is_reported_without_its_content():
    out = lines({**ENV, ENV_GDRIVE_SERVICE_ACCOUNT_JSON: "{not json"})
    assert "not a readable key" in out[0] and "{not json" not in out[0]


def test_an_unshared_folder_gets_a_plain_hint():
    out = lines(drive=Drive(status=404))
    assert out[-1].startswith("project folder FAILED: HTTP 404") and "not shared" in out[-1]


def test_success_lists_the_folder_and_never_prints_the_key():
    out = lines(drive=Drive(children=["raw"]))
    assert out[-2:] == ["project folder visible: 'fno-research'", "inside it: raw"]
    assert all("SECRET-VALUE" not in line for line in out)
    assert "nothing yet" in lines()[-1]
