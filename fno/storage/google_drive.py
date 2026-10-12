"""Reads files from one Google Drive folder with a service account (read-only).

Setup: create a Google Cloud service account with the Drive API enabled, download its JSON key, share the Drive
folder with the service account's e-mail address as Viewer, and put the key's JSON text and the folder ID in the
environment (names in fno/constants.py). Service accounts have no Drive storage of their own, so uploads go through
Google Drive for desktop on the owner's PC, never through this class.
"""

from __future__ import annotations

import json

import requests

from .raw_store import RawFileStore, ReadOnlyStoreError

DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
DRIVE_READ_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
LIST_QUERY = "'{folder}' in parents and trashed = false"
PAGE_SIZE = 1000
TIMEOUT_SECONDS = 60
READ_ONLY = "Google Drive is read-only here: save files into the Drive for desktop folder on the PC instead"


def service_account_token(key_json: str) -> str:
    """A short-lived access token from a service account key (needs the google-auth package)."""
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    info = json.loads(key_json)
    credentials = service_account.Credentials.from_service_account_info(info, scopes=[DRIVE_READ_SCOPE])
    credentials.refresh(Request())
    return credentials.token


class GoogleDriveStore(RawFileStore):
    name = "Google Drive"

    def __init__(self, folder_id: str, token: str, session: requests.Session | None = None):
        self.folder_id = folder_id
        self.session = session or requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"
        self._ids: dict[str, str] | None = None

    def _file_ids(self) -> dict[str, str]:
        """Name -> file ID for everything in the folder, read once (all pages)."""
        if self._ids is None:
            ids, page = {}, None
            while True:
                params = {
                    "q": LIST_QUERY.format(folder=self.folder_id),
                    "fields": "nextPageToken, files(id, name)",
                    "pageSize": PAGE_SIZE,
                }
                if page:
                    params["pageToken"] = page
                response = self.session.get(DRIVE_FILES_URL, params=params, timeout=TIMEOUT_SECONDS)
                response.raise_for_status()
                body = response.json()
                ids.update({f["name"]: f["id"] for f in body.get("files", [])})
                page = body.get("nextPageToken")
                if not page:
                    break
            self._ids = ids
        return self._ids

    def get(self, filename: str) -> bytes | None:
        file_id = self._file_ids().get(filename)
        if file_id is None:
            return None
        response = self.session.get(f"{DRIVE_FILES_URL}/{file_id}", params={"alt": "media"}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.content

    def put(self, filename: str, data: bytes) -> None:
        raise ReadOnlyStoreError(READ_ONLY)
