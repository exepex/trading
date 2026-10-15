"""One 15-minute snapshot as stored in Drive (story A16): every call's raw answer with our own request and response
times, kept apart from the source's own times (design 4.4's clock contract). Stored gzip-compressed JSON; the same
document always gives the same bytes, so saving it again changes nothing."""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

FORMAT = "omenix-intraday-snapshot-v1"
DATASET = "{source}/derivatives/intraday-snapshots"
FILE_NAME = "nifty_{day:%Y%m%d}_{mark:%H%M}.json.gz"


def snapshot_path(source: str, day: date, mark: datetime) -> str:
    """Archive path of a mark's snapshot: `<publisher>/derivatives/intraday-snapshots/<YYYY>/<MM>/<DD>/<file>`."""
    return f"{DATASET.format(source=source)}/{day:%Y}/{day:%m}/{day:%d}/{FILE_NAME.format(day=day, mark=mark)}"


def utc_text(moment: datetime | None) -> str:
    """Every stored time: UTC with its offset (ISO 8601); empty when unknown."""
    return moment.astimezone(UTC).isoformat() if moment else ""


def parse_time(text: str) -> datetime | None:
    return datetime.fromisoformat(text) if text else None


def payload_sha256(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class CallRecord:
    """One request to the source: what was asked (`meta`), when, the raw answer, or the failure's class name only
    (an exception's text could carry a credential, so it is never kept)."""

    name: str
    request_sent_at: datetime
    response_received_at: datetime | None
    payload: dict | list | None
    failure: str = ""
    meta: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "name": self.name, "request_sent_at": utc_text(self.request_sent_at),
            "response_received_at": utc_text(self.response_received_at), "failure": self.failure,
            "meta": self.meta, "payload": self.payload,
            "payload_sha256": "" if self.payload is None else payload_sha256(self.payload),
        }  # fmt: skip

    @classmethod
    def from_json(cls, data: dict) -> CallRecord:
        return cls(
            data["name"], parse_time(data["request_sent_at"]), parse_time(data["response_received_at"]),
            data["payload"], data["failure"], data["meta"],
        )  # fmt: skip


@dataclass
class SnapshotDocument:
    source: str
    underlying: str
    session: date
    mark: datetime
    index: CallRecord
    index_level: float | None  # parsed from the index call by the source adapter
    index_source_time: datetime | None  # the source's own time for that level, never our clock
    future: CallRecord | None = None
    chains: list[CallRecord] = field(default_factory=list)
    quotes: list[CallRecord] = field(default_factory=list)
    expiries: dict = field(default_factory=dict)
    expected_contracts: int = 0
    two_sided_contracts: int = 0
    failures: list[str] = field(default_factory=list)  # every failed step, by name
    finished_at: datetime | None = None  # our clock when the document was complete: its first_seen_at

    @property
    def recorded_contracts(self) -> int:
        return sum(1 for q in self.quotes if not q.failure)

    def to_bytes(self) -> bytes:
        body = {
            "format": FORMAT, "source": self.source, "underlying": self.underlying,
            "session": self.session.isoformat(), "mark": utc_text(self.mark),
            "index_level": self.index_level, "index_source_time": utc_text(self.index_source_time),
            "index": self.index.to_json(), "future": self.future.to_json() if self.future else None,
            "chains": [c.to_json() for c in self.chains], "quotes": [q.to_json() for q in self.quotes],
            "expiries": self.expiries, "expected_contracts": self.expected_contracts,
            "recorded_contracts": self.recorded_contracts, "two_sided_contracts": self.two_sided_contracts,
            "failures": self.failures, "finished_at": utc_text(self.finished_at),
        }  # fmt: skip
        text = json.dumps(body, sort_keys=True, default=str, separators=(",", ":")).encode()
        return gzip.compress(text, mtime=0)  # no time in the gzip header: equal documents, equal bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> SnapshotDocument:
        body = json.loads(gzip.decompress(data))
        if body.get("format") != FORMAT:
            raise ValueError(f"not an intraday snapshot of format {FORMAT}")
        future = body["future"]
        return cls(
            body["source"], body["underlying"], date.fromisoformat(body["session"]), parse_time(body["mark"]),
            CallRecord.from_json(body["index"]), body["index_level"], parse_time(body["index_source_time"]),
            CallRecord.from_json(future) if future else None, [CallRecord.from_json(c) for c in body["chains"]],
            [CallRecord.from_json(q) for q in body["quotes"]], body["expiries"], body["expected_contracts"],
            body["two_sided_contracts"], body["failures"], parse_time(body["finished_at"]),
        )  # fmt: skip
