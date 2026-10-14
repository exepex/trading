"""The common market pack (story E2, design 13.5 step 1): the day's market observations, session and events, each
admitted only if available by the cutoff, the common opportunity set, and the provenance to rebuild it. It holds no
book's decisions, positions, P&L, findings or memory: its inputs read market data only, and the finished pack is
refused if it names any book or any journal path."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Protocol

from ..constants import BOOKS, JOURNAL_FOLDER
from ..models import IST
from ..playbook.loader import Playbook
from ..playbook.registry import RegistryRow
from .opportunity_set import OpportunitySet
from .pack_inputs import CommonInput
from .pack_items import PackError, admit, canonical_json, sha256_hex

SCHEMA_VERSION = 1
FUTURE_PREFIX = "future:"
FORBIDDEN = (*BOOKS, f"{JOURNAL_FOLDER}/")  # a book's name or journal path never appears in the common pack


class PlaybookState(Protocol):
    def load(self) -> Playbook: ...

    def registry_rows(self) -> Sequence[RegistryRow]: ...


@dataclass(frozen=True)
class CommonPack:
    day: date
    body: dict

    @property
    def data(self) -> bytes:
        return canonical_json(self.body)

    @property
    def sha256(self) -> str:
        return sha256_hex(self.data)


def require_market_only(data: bytes) -> None:
    text = data.decode("utf-8")
    found = [word for word in FORBIDDEN if word in text]
    if found:
        raise PackError(f"the common pack would contain book data ({found}); it holds market data only")


class CommonPackBuilder:
    def __init__(self, inputs: Sequence[CommonInput], opportunities: OpportunitySet, playbook: PlaybookState):
        self.inputs, self.opportunities, self.playbook = tuple(inputs), opportunities, playbook

    def build(self, day: date, cutoff: time) -> CommonPack:
        moment = datetime.combine(day, cutoff, tzinfo=IST)
        batches = {source.name: source.collect(day) for source in self.inputs}
        items, refused = admit((i for b in batches.values() for i in b.items), moment)
        monthly = sorted(
            date.fromisoformat(i.name.removeprefix(FUTURE_PREFIX)) for i in items if i.name.startswith(FUTURE_PREFIX)
        )
        playbook = self.playbook.load()
        body = {
            "schema_version": SCHEMA_VERSION,
            "kind": "common_market_pack",
            "day": day.isoformat(),
            "cutoff": moment.isoformat(),
            "provenance": {name: batch.provenance for name, batch in sorted(batches.items())},
            "items": [item.record() for item in items],
            "refused": list(refused),
            "opportunities": self.opportunities.build(playbook.strategies, self.playbook.registry_rows(), day, monthly),
        }
        pack = CommonPack(day, body)
        require_market_only(pack.data)
        return pack
