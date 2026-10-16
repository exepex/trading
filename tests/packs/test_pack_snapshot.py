"""Story E2e, judge 309: `canonical_snapshot` returns the snapshot the common pack recorded, parsed from its own quote
file and sidecar read by the recorded ID and checked against the recorded SHA-256s; the day's `.canonical` marker is
never followed, so a later capture it names can never be read in the pack's place."""

import json
from datetime import date

import pytest

from fno.desk.common_pack import SNAPSHOT_INPUT, CommonPack
from fno.desk.pack_items import sha256_hex
from fno.desk.pack_snapshot import NotThePacksSnapshot, canonical_snapshot
from fno.quotes.recorder import DATASET, QuoteSnapshotRecorder
from fno.storage.raw_store import LocalFolderStore

DAY = date(2026, 10, 14)
HEADER = "expiry,strike,type,bid,ask,valid,contract_id\n"


def capture(store, snapshot_id, bid, finished="2026-10-14T14:55:40+05:30"):
    csv_bytes = (HEADER + f"2026-10-27,21950,CE,{bid},{bid + 1},true,c1\n").encode()
    meta = json.dumps({"finished_at": finished, "spot": 21900.0, "india_vix": 12.0, "futures": []}).encode()
    store.put(QuoteSnapshotRecorder.path(DAY, f"{snapshot_id}.csv"), csv_bytes)
    store.put(QuoteSnapshotRecorder.path(DAY, f"{snapshot_id}.meta.json"), meta)
    return csv_bytes, meta


def pack(snapshot_id, csv_bytes, meta):
    provenance = {SNAPSHOT_INPUT: {"dataset": DATASET, "snapshot_id": snapshot_id, "csv_sha256": sha256_hex(csv_bytes),
                                   "meta_sha256": sha256_hex(meta)}}  # fmt: skip
    return CommonPack(DAY, {"day": DAY.isoformat(), "provenance": provenance, "items": []})


@pytest.fixture
def store(tmp_path):
    return LocalFolderStore(tmp_path / "quotes")


def bids(snapshot):
    return [q.bid for q in snapshot.quotes]


def test_the_packs_own_capture_is_returned(store):
    common = pack("nifty_20261014_145500", *capture(store, "nifty_20261014_145500", 11.55))
    assert bids(canonical_snapshot(DAY, common, store)) == [11.55]


def test_a_marker_naming_a_later_capture_is_never_followed(store):
    """Judge 309's plant: a later capture with a 9,999.99 bid, the marker naming it, the pack recording 14:55."""
    common = pack("nifty_20261014_145500", *capture(store, "nifty_20261014_145500", 11.55))
    capture(store, "nifty_20261014_150500", 9999.99, finished="2026-10-14T15:05:40+05:30")
    store.put(QuoteSnapshotRecorder.path(DAY, "nifty_20261014.canonical"), b"nifty_20261014_150500\n")
    snapshot = canonical_snapshot(DAY, common, store)
    assert bids(snapshot) == [11.55] and snapshot.finished_at.hour == 14


@pytest.mark.parametrize("which", ["csv", "sidecar"])
def test_a_file_that_differs_from_the_packs_hash_is_refused(store, which):
    """The store is write-once, so the pack records other bytes: a capture changed after the pack reads the same."""
    csv_bytes, meta = capture(store, "nifty_20261014_145500", 11.55)
    common = pack("nifty_20261014_145500", csv_bytes + b"x" if which == "csv" else csv_bytes,
                  meta + b" " if which == "sidecar" else meta)  # fmt: skip
    with pytest.raises(NotThePacksSnapshot, match=f"nifty_20261014_145500: {which}"):
        canonical_snapshot(DAY, common, store)


def test_a_missing_file_or_a_pack_naming_no_snapshot_is_refused(store):
    csv_bytes, meta = capture(store, "nifty_20261014_145500", 11.55)
    with pytest.raises(NotThePacksSnapshot, match="names no snapshot"):
        canonical_snapshot(DAY, CommonPack(DAY, {"day": DAY.isoformat(), "provenance": {}, "items": []}), store)
    with pytest.raises(NotThePacksSnapshot, match="nifty_20261014_150000: csv"):
        canonical_snapshot(DAY, pack("nifty_20261014_150000", csv_bytes, meta), store)  # no such capture stored
