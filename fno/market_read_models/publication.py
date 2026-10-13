"""One session's publication (story P6): every block's stored row (the read-model columns W11 and P3 name, with the
payload and its SHA-256), checked against the pinned W11 contract the way the dashboard serves it, before anything may
be published. A block that breaks its schema stops the whole publication. The publication ID names the session and
its content (`nse-<day>-<12 hex of the pages' hashes>`), never the code commit: a second run of the same day with
the same pages has the same ID and adds nothing, and NSE's later version of a file makes a new one."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime

from .blocks import BlockBuilder, SessionRows
from .contract import PinnedContract

MARKET, PRODUCT, PUBLISHER, PAPER = "india", "fno", "fno", "Paper"
FRESHNESS_RULE = "fno_calendar"
ID_HEX = 12  # hex digits of the content hash in a publication ID


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
        payloads = {builder.page_key: builder.build(rows) for builder in self.builders}
        sha256 = {key: hashlib.sha256(canonical(payload)).hexdigest() for key, payload in payloads.items()}
        publication_id = publication_id_for(rows.day, sha256)
        records = {}
        for builder in self.builders:
            record = {
                "market": MARKET, "page_key": builder.page_key, "as_of": rows.day.isoformat(), "cutoff": built_at,
                "built_at": built_at, "schema_version": self.contract.version, "source_commit": self.source_commit,
                "payload_sha256": sha256[builder.page_key], "product": PRODUCT, "publication_id": publication_id,
                "payload": payloads[builder.page_key],
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


def hashes(publication: Publication) -> dict[str, str]:
    """Page key -> payload SHA-256: what a store must hold for the publication."""
    return {page_key: record["payload_sha256"] for page_key, record in publication.records.items()}


def publication_id_for(day: date, sha256: dict[str, str]) -> str:
    """The session and its content: the same pages always give the same ID."""
    content = canonical(sha256)
    return f"nse-{day.isoformat()}-{hashlib.sha256(content).hexdigest()[:ID_HEX]}"


def served(record: dict, payload: dict) -> dict:
    """The response the route makes of a stored row: its envelope fields added (fresh: just built)."""
    freshness = {"state": "fresh", "rule": FRESHNESS_RULE, "built_at": record["built_at"], "age_minutes": 0,
                 "reason": None}  # fmt: skip
    return {**record, "publisher": PUBLISHER, "freshness": freshness, "paper": PAPER, "payload": payload}
