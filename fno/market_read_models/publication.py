"""One session's publication (story P6): every block's stored row (the read-model columns W11 and P3 name, with the
payload and its SHA-256), checked against the pinned W11 contract the way the dashboard serves it, before anything may
be published. A block that breaks its schema stops the whole publication."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime

from .blocks import BlockBuilder, SessionRows
from .contract import PinnedContract

MARKET, PRODUCT, PUBLISHER, PAPER = "india", "fno", "fno", "Paper"
FRESHNESS_RULE = "fno_calendar"


@dataclass(frozen=True)
class Publication:
    day: date
    publication_id: str
    records: dict[str, dict]  # page key -> stored row


def canonical(payload) -> bytes:
    """The payload's bytes for its SHA-256 (sorted keys, no spaces), as the contract's examples hash them."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class PublicationBuilder:
    def __init__(self, builders: list[BlockBuilder], contract: PinnedContract, source_commit: str, clock=utc_now):
        self.builders, self.contract, self.source_commit, self.clock = builders, contract, source_commit, clock

    def build(self, rows: SessionRows) -> Publication:
        built_at = self.clock()
        publication_id = f"nse-{rows.day.isoformat()}-{self.source_commit[:12]}"
        records = {}
        for builder in self.builders:
            payload = builder.build(rows)
            record = {
                "market": MARKET, "page_key": builder.page_key, "as_of": rows.day.isoformat(), "cutoff": built_at,
                "built_at": built_at, "schema_version": self.contract.version, "source_commit": self.source_commit,
                "payload_sha256": hashlib.sha256(canonical(payload)).hexdigest(), "product": PRODUCT,
                "publication_id": publication_id, "payload": payload,
            }  # fmt: skip
            self.check(builder, record)
            records[builder.page_key] = record
        return Publication(rows.day, publication_id, records)

    def check(self, builder: BlockBuilder, record: dict) -> None:
        """ContractBroken unless the stored payload matches W11's stored schema (where W11 names one) and the response
        the route serves from it alone matches W11's response schema (a paged block: its default page)."""
        if builder.stored_schema:
            self.contract.validate(builder.stored_schema, record["payload"])
        if builder.served_schema:
            self.contract.validate(builder.served_schema, served(record, builder.served(record["payload"])))


def served(record: dict, payload: dict) -> dict:
    """The response the route makes of a stored row: its envelope fields added (fresh: just built)."""
    freshness = {"state": "fresh", "rule": FRESHNESS_RULE, "built_at": record["built_at"], "age_minutes": 0,
                 "reason": None}  # fmt: skip
    return {**record, "publisher": PUBLISHER, "freshness": freshness, "paper": PAPER, "payload": payload}
