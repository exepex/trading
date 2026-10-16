"""The day's canonical 3 pm snapshot exactly as the common pack recorded it (story E2e): the snapshot ID the pack names
under its provenance (`a4_snapshot`), with the same quote file SHA-256. Every reader of the cutoff market (Book 1's
inputs, each book's sheet, each decider's re-check) takes it from here, so a later capture can never be read in its
place, and a decision reads exactly what the pack froze."""

from __future__ import annotations

import hashlib
from datetime import date

from ..quotes.recorder import QuoteSnapshotRecorder
from ..research_data.quote_snapshots import CutoffSnapshot, RecordedSnapshots
from ..storage.raw_store import RawFileStore
from .common_pack import SNAPSHOT_INPUT, CommonPack

NOT_THE_PACK_S = "the canonical snapshot of {day} is not the one its common pack records ({why})"


class NotThePacksSnapshot(ValueError):
    """The stored snapshot is missing or differs from the one the common pack recorded."""


def canonical_snapshot(day: date, common: CommonPack, quotes: RawFileStore) -> CutoffSnapshot:
    recorded = common.body["provenance"].get(SNAPSHOT_INPUT, {})
    snapshot_id = recorded.get("snapshot_id")
    data = quotes.get(QuoteSnapshotRecorder.path(day, f"{snapshot_id}.csv")) if snapshot_id else None
    if data is None or hashlib.sha256(data).hexdigest() != recorded.get("csv_sha256"):
        raise NotThePacksSnapshot(NOT_THE_PACK_S.format(day=day, why=f"snapshot {snapshot_id}"))
    snapshot = RecordedSnapshots(quotes).snapshot(day)
    if snapshot is None:
        raise NotThePacksSnapshot(NOT_THE_PACK_S.format(day=day, why="no canonical snapshot"))
    return snapshot
