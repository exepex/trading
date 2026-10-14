"""The day's canonical A4 quote snapshot as common-pack items (story E2). Times follow the forecast pack's rules
(protocol v2, review 29): an option row is available when its response arrived; India VIX at the later of NSE's own
timestamp and the capture's first request (A4 reads it before any quote); the futures' last prices at that first
request. A day without a canonical snapshot gives no items and says so in the provenance."""

from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime

from ..models import IST
from ..quotes.recorder import NONE_MARKER, QuoteSnapshotRecorder
from ..storage.raw_store import RawFileStore
from .pack_inputs import CommonInput, InputBatch
from .pack_items import PackItem, available_time, sha256_hex

NSE_TIME_FORMATS = ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M")
QUOTE_FIELDS = ("contract_id", "bid", "ask", "bid_qty", "ask_qty", "valid", "invalid_reason", "spot")


def _nse_time(text: str) -> datetime | None:
    for fmt in NSE_TIME_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=IST)
        except ValueError:
            continue
    return None


def _number(text: str) -> float | None:
    return float(text) if text else None


class SnapshotInput(CommonInput):
    name = "a4_snapshot"

    def __init__(self, store: RawFileStore, dataset: str):
        self.store, self.dataset = store, dataset

    def collect(self, day: date) -> InputBatch:
        marker = self.store.get(QuoteSnapshotRecorder.path(day, f"nifty_{day:%Y%m%d}.canonical", self.dataset))
        snapshot_id = marker.decode().strip() if marker else NONE_MARKER
        csv_bytes, meta_bytes = (
            self.store.get(QuoteSnapshotRecorder.path(day, f"{snapshot_id}{suffix}", self.dataset))
            for suffix in (".csv", ".meta.json")
        )
        if snapshot_id == NONE_MARKER or not csv_bytes or not meta_bytes:
            return InputBatch((), {"dataset": self.dataset, "snapshot_id": None})
        rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
        meta = json.loads(meta_bytes)
        source = f"a4 {self.dataset} {snapshot_id}"
        first_request = min((r["request_sent_at"] for r in rows), default="")
        items = [self._option(row, source) for row in rows]
        items += self._vix(meta, source, first_request) + self._futures(meta, source, first_request)
        provenance = {"dataset": self.dataset, "snapshot_id": snapshot_id, "csv_sha256": sha256_hex(csv_bytes),
                      "meta_sha256": sha256_hex(meta_bytes)}  # fmt: skip
        return InputBatch(tuple(items), provenance)

    @staticmethod
    def _option(row: dict, source: str) -> PackItem:
        name = f"option:{row['expiry']}:{float(row['strike']):g}:{row['type']}"
        value = {key: row[key] for key in QUOTE_FIELDS}
        for key in ("bid", "ask", "bid_qty", "ask_qty", "spot"):
            value[key] = _number(value[key])
        value["valid"] = value["valid"] == "true"
        return PackItem(name, value, source, row["response_received_at"])

    @staticmethod
    def _vix(meta: dict, source: str, first_request: str) -> list[PackItem]:
        stamp, value = _nse_time(str(meta.get("india_vix_time", ""))), meta.get("india_vix")
        if value is None:
            return []
        request = available_time(first_request)
        known = max(stamp, request).isoformat() if stamp and request else ""
        return [PackItem("india_vix", float(value), f"{source} meta india_vix (NSE timestamp)", known)]

    @staticmethod
    def _futures(meta: dict, source: str, first_request: str) -> list[PackItem]:
        return [
            PackItem(
                f"future:{f['expiry']}",
                {"last": float(f["last"]), "volume": int(f["volume"])},
                f"{source} meta futures",
                first_request,
            )  # fmt: skip
            for f in meta.get("futures", [])
        ]
