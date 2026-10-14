"""The checks on the execution snapshot itself (story C3): it can be read (present, the day's, its file matching the
hash in its own sidecar), it was captured inside its scheduled window (the capture times in its sidecar), and the pack
records this very snapshot with the same hash. A failure of any of them makes the snapshot's prices unusable."""

from __future__ import annotations

from ..desk.common_pack import CommonPack
from .data_checks import CheckSubject, DataCheck

TIME = "%H:%M:%S"


class SnapshotReadable(DataCheck):
    name, prices_unverified = "snapshot", True

    def problems(self, subject: CheckSubject) -> list[str]:
        if subject.capture is None:
            return [f"no execution capture is named for {subject.day}"]
        return [subject.unreadable] if subject.snapshot is None else []


class SnapshotInWindow(DataCheck):
    """Freshness is the capture's own times from its sidecar; a quote's age is never claimed (A4)."""

    name, prices_unverified = "snapshot window", True

    def problems(self, subject: CheckSubject) -> list[str]:
        snapshot, capture = subject.snapshot, subject.capture
        if snapshot is None or capture is None:
            return []
        if capture.start <= snapshot.started_at and snapshot.finished_at <= capture.end:
            return []
        return [
            f"{snapshot.snapshot_id} was captured {snapshot.started_at:{TIME}}-{snapshot.finished_at:{TIME}}, "
            f"outside its window {capture.start:{TIME}}-{capture.end:{TIME}} (stale or early)"
        ]


def pack_hash(pack: CommonPack, snapshot_id: str) -> str | None:
    """The quote file hash the pack records for this snapshot, or None when the pack names no such snapshot."""
    found = [p for p in pack.body["provenance"].values() if p.get("snapshot_id") == snapshot_id]
    return found[0].get("csv_sha256") if found else None


class SnapshotMatchesPack(DataCheck):
    name, prices_unverified = "snapshot hash", True

    def problems(self, subject: CheckSubject) -> list[str]:
        snapshot = subject.snapshot
        if snapshot is None:
            return []
        recorded = pack_hash(subject.pack, snapshot.snapshot_id)
        if recorded is None:
            return [f"the common pack of {subject.day} does not record snapshot {snapshot.snapshot_id}"]
        if recorded != snapshot.sha256:
            return [f"{snapshot.snapshot_id}: quote file hash {snapshot.sha256} differs from the pack's {recorded}"]
        return []
