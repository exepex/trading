"""Story G10 completion, criterion 3: the day's v4 capture as the pack builder reads it, from A4e's dataset: the
canonical marker, then the attempt's sidecar and quote rows. No marker, a `none` marker, or a missing sidecar or quote
file gives no capture (the day is then system_late), never a guess."""

import json
from datetime import date

from fno.quotes.recorder import NONE_MARKER, QuoteSnapshotRecorder
from fno.storage.raw_store import LocalFolderStore
from fno.v4_pack.capture import StoredV4Capture

DAY = date(2026, 10, 26)
DATASET = "groww/derivatives/quote-snapshots-v4"
SNAPSHOT = "nifty_20261026_143000"


def store(tmp_path, marker=SNAPSHOT, sidecar=True, quotes=True):
    files = LocalFolderStore(tmp_path)
    put = lambda name, data: files.put(QuoteSnapshotRecorder.path(DAY, name, DATASET), data)  # noqa: E731
    if marker is not None:
        put("nifty_20261026.canonical", marker.encode())
    if sidecar:
        put(f"{SNAPSHOT}.meta.json", json.dumps({"clock_status": "clock_ok"}).encode())
    if quotes:
        put(f"{SNAPSHOT}.csv", b"expiry,strike,type\n2026-10-27,25000,CE\n")
    return StoredV4Capture(files, DATASET)


def test_the_canonical_attempt_is_read_with_its_sidecar_and_rows(tmp_path):
    found = store(tmp_path).capture(DAY)
    assert (found.dataset, found.snapshot_id, found.meta["clock_status"]) == (DATASET, SNAPSHOT, "clock_ok")
    assert found.rows == ({"expiry": "2026-10-27", "strike": "25000", "type": "CE"},)


def test_no_marker_a_none_marker_or_a_missing_file_gives_no_capture(tmp_path):
    assert store(tmp_path / "a", marker=None).capture(DAY) is None
    assert store(tmp_path / "b", marker=NONE_MARKER).capture(DAY) is None
    assert store(tmp_path / "c", sidecar=False).capture(DAY) is None
    assert store(tmp_path / "d", quotes=False).capture(DAY) is None
