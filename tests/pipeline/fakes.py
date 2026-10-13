"""Fakes for the pipeline tests (story O6): a trigger that records fires, alerts that record lines, and a store that
refuses writes like a Drive that declined the upload."""

from __future__ import annotations

import hashlib
from datetime import date, datetime

from fno.alerts.sender import AlertSender
from fno.models import IST
from fno.pipeline.trigger import FireFailed, RoutineTrigger
from fno.storage.manifest_folder import Fingerprint, ManifestFolder
from fno.storage.raw_source import ParticipantOiSource
from fno.storage.raw_store import RawFileStore
from fno.storage.revisions import Revision, RevisionIndex

TODAY = date(2026, 10, 13)
NOW = datetime(2026, 10, 13, 19, 0, tzinfo=IST)


class FakeTrigger(RoutineTrigger):
    def __init__(self, name: str = "dry-run", failure: str = ""):
        self.name, self.failure, self.fired = name, failure, []

    def fire(self, pointer) -> str:
        if self.failure:
            raise FireFailed(self.failure)
        self.fired.append(pointer)
        return f"https://claude.ai/code/session_{len(self.fired)}"


class RecordingAlerts(AlertSender):
    def __init__(self):
        self.lines = []

    def send(self, text: str) -> str:
        self.lines.append(text)
        return "alert sent to #fno-desk"


class RefusingStore(RawFileStore):
    """Reads through to a real store; refuses writes (or everything) as a Drive that declined would."""

    def __init__(self, store: RawFileStore, refuse_reads: bool = False):
        self.store, self.refuse_reads = store, refuse_reads

    def get(self, path: str) -> bytes | None:
        if self.refuse_reads:
            raise RuntimeError("Google refused the Drive upload sign-in")
        return self.store.get(path)

    def put(self, path: str, data: bytes) -> None:
        raise RuntimeError("Drive refused the upload")


def add_day(manifests: ManifestFolder, day: date, data: bytes) -> str:
    """A participant-OI day as the librarian leaves it: its manifest row. Returns its SHA-256."""
    path = ParticipantOiSource.path_for(day)
    manifests.record(ParticipantOiSource, Fingerprint.of(ParticipantOiSource, path, data))
    return hashlib.sha256(data).hexdigest()


def add_revision(index: RevisionIndex, day: date, data: bytes, found_at: datetime = NOW) -> str:
    """A later NSE version of a day's file, as A11's sweep records it. Returns its SHA-256."""
    sha = hashlib.sha256(data).hexdigest()
    path = ParticipantOiSource.path_for(day)
    index.append(ParticipantOiSource, Revision(day, path, sha, len(data), found_at, found_at, found_at))
    return sha
