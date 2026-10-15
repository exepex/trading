"""Story A16 criteria 3, 4 and 8: the stored document (paths, UTC times, same bytes for the same document) and the
first-version store (A11's revision rule)."""

import gzip
import hashlib
import json
import time
from datetime import timedelta

import pytest

from fno.intraday.document import CallRecord, SnapshotDocument, snapshot_path, utc_text
from tests.intraday.fakes import DAY, ist

MARK = ist(DAY, 9, 15)


def document(level=25000.5) -> SnapshotDocument:
    index = CallRecord("index", MARK, MARK + timedelta(seconds=0.8), {"last_price": level, "x": [1, 2]})
    quote = CallRecord("quote NIFTY", MARK, None, None, "GrowwAPIException", {"symbol": "NIFTY26OCT25000CE"})
    finished = MARK + timedelta(seconds=40)
    return SnapshotDocument("groww", "NIFTY", DAY, MARK, index, level, MARK - timedelta(seconds=1), quotes=[quote],
                            expected_contracts=1, failures=["quote NIFTY"], finished_at=finished)  # fmt: skip


def test_the_archive_path_follows_the_layout_and_names_the_copy_by_its_sha256():
    data = document().to_bytes()
    assert snapshot_path("groww", DAY, MARK, data) == (
        f"groww/derivatives/intraday-snapshots/2026/10/15/nifty_20261015_0915_{hashlib.sha256(data).hexdigest()[:16]}"
        ".json.gz"
    )


def test_equal_documents_give_equal_bytes_even_seconds_apart(monkeypatch):
    """Judge 108 addendum 3, mutation I18: gzip writes the time into its header unless told not to."""
    first = document().to_bytes()
    monkeypatch.setattr(time, "time", lambda: 1_900_000_000.0)  # gzip reads the clock through time.time
    assert document().to_bytes() == first


def test_a_document_round_trips_and_the_same_document_gives_the_same_bytes():
    data = document().to_bytes()
    assert data == document().to_bytes()  # no time in the gzip header
    back = SnapshotDocument.from_bytes(data)
    assert back.to_bytes() == data and back.recorded_contracts == 0 and back.mark == MARK


def test_every_stored_time_is_utc_with_its_offset_and_source_time_is_kept_apart():
    body = json.loads(gzip.decompress(document().to_bytes()))
    assert body["mark"] == "2026-10-15T03:45:00+00:00"
    assert body["index"]["request_sent_at"] == "2026-10-15T03:45:00+00:00"
    assert body["index_source_time"] == "2026-10-15T03:44:59+00:00" and body["finished_at"].endswith("+00:00")
    assert utc_text(None) == ""


def test_a_failed_call_keeps_only_its_exception_class_name():
    body = json.loads(gzip.decompress(document().to_bytes()))
    assert body["quotes"][0]["failure"] == "GrowwAPIException" and body["quotes"][0]["payload"] is None
    assert len(body["index"]["payload_sha256"]) == 64


def test_another_format_is_refused():
    with pytest.raises(ValueError):
        SnapshotDocument.from_bytes(gzip.compress(b'{"format": "other"}'))
