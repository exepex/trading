"""When a store says it first held a file (story A17b): the check behind adopting a copy whose fetch time is read
from its own path. A store that cannot say answers None, and the caller refuses."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .google_drive import DRIVE_FILES_URL, GoogleDriveStore

CREATED_FIELD = "createdTime"


class CreationTimes(ABC):
    @abstractmethod
    def created_at(self, path: str) -> datetime | None:
        """When the store first held the file at this path; None when absent or unknown."""


class GoogleDriveCreationTimes(CreationTimes):
    """Drive's own `createdTime` of a file, under an area folder of the Drive project folder (e.g. `raw`)."""

    def __init__(self, drive: GoogleDriveStore, area: str):
        self.drive, self.area = drive, area

    def created_at(self, path: str) -> datetime | None:
        file_id = self.drive.file_id(f"{self.area}/{path}")
        if file_id is None:
            return None
        response = self.drive.drive.get(f"{DRIVE_FILES_URL}/{file_id}", params={"fields": CREATED_FIELD})
        response.raise_for_status()
        stamp = response.json().get(CREATED_FIELD)
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
