"""Reads files from one Google Drive folder with a service account (read-only).

Setup: create a Google Cloud service account with the Drive API enabled, download its JSON key, share the Drive
folder with the service account's e-mail address as Viewer, and put the key's JSON text and the folder ID in the
environment (names in fno/constants.py). Service accounts have no Drive storage of their own, so uploads go through
Google Drive for desktop on the owner's PC, never through this class.
"""

from __future__ import annotations

import base64
import json

import requests

from .raw_store import RawFileConflict, RawFileStore, ReadOnlyStoreError, path_parts

DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
DRIVE_READ_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
FOLDER_TYPE = "application/vnd.google-apps.folder"
CHILD_QUERY = "'{parent}' in parents and name = '{name}' and trashed = false and mimeType {op} '" + FOLDER_TYPE + "'"
TIMEOUT_SECONDS = 60
ROOT_QUERY = "'{parent}' in parents and trashed = false"
READ_ONLY = "Google Drive is read-only here: save files into the Drive for desktop folder on the PC instead"


def service_account_info(key_text: str) -> dict:
    """The service account key from its JSON text or from that text base64-encoded (one plain line that every
    settings screen keeps intact)."""
    text = key_text.strip()
    if not text.startswith("{"):
        text = base64.b64decode(text).decode("utf-8")
    return json.loads(text)


def service_account_token(key_text: str) -> str:
    """A short-lived access token from a service account key (needs the google-auth package)."""
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    info = service_account_info(key_text)
    credentials = service_account.Credentials.from_service_account_info(info, scopes=[DRIVE_READ_SCOPE])
    credentials.refresh(Request())
    return credentials.token


class GoogleDriveStore(RawFileStore):
    """Files under one shared root folder, in the same tree as the local archive (one folder per path part)."""

    name = "Google Drive"

    def __init__(self, folder_id: str, token: str, session: requests.Session | None = None):
        self.folder_id = folder_id
        self.session = session or requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"
        self._ids: dict[tuple[str, str, bool], str | None] = {}

    def _child(self, parent_id: str, name: str, folder: bool) -> str | None:
        """The ID of the named folder or file directly inside a folder (cached); None if absent."""
        key = (parent_id, name, folder)
        if key not in self._ids:
            query = CHILD_QUERY.format(
                parent=parent_id, name=name.replace("\\", "\\\\").replace("'", "\\'"), op="=" if folder else "!="
            )
            params = {"q": query, "fields": "files(id, name)", "pageSize": 10}
            response = self.session.get(DRIVE_FILES_URL, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            found = response.json().get("files", [])
            if len(found) > 1:
                raise RawFileConflict(f"{len(found)} items named {name!r} in one Drive folder")
            self._ids[key] = found[0]["id"] if found else None
        return self._ids[key]

    def get(self, path: str) -> bytes | None:
        *folders, filename = path_parts(path)
        parent: str | None = self.folder_id
        for name in folders:
            parent = self._child(parent, name, folder=True)
            if parent is None:
                return None
        file_id = self._child(parent, filename, folder=False)
        if file_id is None:
            return None
        response = self.session.get(f"{DRIVE_FILES_URL}/{file_id}", params={"alt": "media"}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.content

    def root_listing(self) -> tuple[str, list[str]]:
        """The root folder's name and the names directly inside it (for the access check)."""
        response = self.session.get(
            f"{DRIVE_FILES_URL}/{self.folder_id}", params={"fields": "name, mimeType"}, timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        listing = self.session.get(
            DRIVE_FILES_URL,
            params={"q": ROOT_QUERY.format(parent=self.folder_id), "fields": "files(name)", "pageSize": 100},
            timeout=TIMEOUT_SECONDS,
        )
        listing.raise_for_status()
        return response.json()["name"], sorted(f["name"] for f in listing.json().get("files", []))

    def put(self, path: str, data: bytes) -> None:
        raise ReadOnlyStoreError(READ_ONLY)
