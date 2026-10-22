"""The dashcam's records (story 3.4). One decision record per scheduled (session, slot, road, driver version), one
outcome record when a trade or ticket closes. Never edited: a correction is a new record naming the old one."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

from ..constants import RECORD_SCHEMA_VERSION, ClosureReason, RoadCode
from .accounts import FillResult
from .codec import canonical_bytes, from_bytes
from .decisions import Decision
from .safety import LawResult
from .snapshot import ContractKey, SlotQuote


@dataclass(frozen=True)
class WitnessedQuote:
    key: ContractKey
    quote: SlotQuote


@dataclass(frozen=True)
class DecisionRecord:
    session: date
    slot: str
    road: RoadCode
    card_sha256: str
    snapshot_id: str  # empty when the road had no usable snapshot
    snapshot_sha256: str
    road_closed_by: ClosureReason | None
    decision: Decision
    law_results: tuple[LawResult, ...] = ()
    witnessed: tuple[WitnessedQuote, ...] = ()  # every proposal leg's quote at the snapshot
    inputs: Mapping[str, float | int | str] = field(default_factory=dict)  # e.g. expected move, history sessions
    schema: int = RECORD_SCHEMA_VERSION

    def __post_init__(self):
        if self.decision.session != self.session or self.decision.road != self.road:
            raise ValueError("the record's session and road are its decision's")

    def to_bytes(self) -> bytes:
        return canonical_bytes(self)

    @classmethod
    def from_bytes(cls, data: bytes) -> "DecisionRecord":
        return from_bytes(cls, data)


@dataclass(frozen=True)
class OutcomeRecord:
    position_id: str
    driver_id: str
    road: RoadCode
    decision_sha256: str  # the sealed decision file the entry rests on
    entry: FillResult
    exit: FillResult
    exit_reason: str
    gross: float
    costs: float
    net: float
    return_on_risk: float  # net / maximum loss at entry
    slippage_vs_mid: float  # rupees paid against the mids of the filled legs, entry and exit
    is_ticket: bool = False
    corrects: str = ""  # SHA-256 of the record this one corrects, if any
    schema: int = RECORD_SCHEMA_VERSION

    def __post_init__(self):
        if not (self.entry.filled and self.exit.filled):
            raise ValueError("an outcome closes a position that was filled at entry and at exit (or settlement)")

    def to_bytes(self) -> bytes:
        return canonical_bytes(self)

    @classmethod
    def from_bytes(cls, data: bytes) -> "OutcomeRecord":
        return from_bytes(cls, data)
