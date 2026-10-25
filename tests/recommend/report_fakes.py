"""Receipted recommendation and check files for REC1d's section tests: each `put` writes the record's bytes and its
receipt under the repository's receipts folder, as the real publisher does."""

import hashlib
from dataclasses import dataclass, field
from datetime import date, timedelta

from fno.recommend.check import FoundOutcome, OutcomeLookup, check, unreadable
from fno.recommend.codec import encode
from fno.recommend.constants import EvidenceRung
from fno.recommend.report_section import ReportPorts
from fno.recommend.shelf import ReceiptShelf, check_path
from fno.recommend.store import record_path
from tests.recommend.builders import DAY, MADE_AT, candidate, evidence_of, no_trade

CS1 = "school:CS1@1"
TUESDAY, WEDNESDAY = DAY + timedelta(days=1), DAY + timedelta(days=2)


class Closed(OutcomeLookup):
    def __init__(self, net=None):
        self.net = net

    def outcome(self, cand, session, until):
        return None if self.net is None else FoundOutcome(self.net, False)

    def ticket(self, cand, session):
        return False


def previous_weekday(day: date) -> date:
    back = day - timedelta(days=1)
    return back if back.weekday() < 5 else previous_weekday(back)


@dataclass
class Store:
    root: object
    files: dict = field(default_factory=dict)
    steps: dict = field(default_factory=dict)

    def put(self, path: str, data: bytes) -> None:
        self.files[path] = data
        receipt = self.root / f"{path}.sha256"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(hashlib.sha256(data).hexdigest())

    def record(self, record=None, day: date = DAY):
        record = record or no_trade(session=day)
        self.put(record_path(record.session), encode(record))
        return record

    def check(self, record, on: date, net: float | None = None, last: bool = False):
        made = check(record, "0" * 64, on, MADE_AT, Closed(net), last)
        self.put(check_path(record.session, on), made.to_bytes())
        return made

    def failed_check(self, day: date, on: date, problem: str):
        self.put(check_path(day, on), unreadable(day, on, MADE_AT, problem).to_bytes())

    def ports(self) -> ReportPorts:
        return ReportPorts(ReceiptShelf(self.root), lambda path: self.files[path], previous_weekday, self.steps.get)


def traded(day: date = DAY):
    return no_trade(session=day, versions=(evidence_of(CS1),), candidates=(candidate(CS1, traded=True),))


def quiet(day: date = DAY):
    """A no-trade day on which no candidate traded: complete at its first check."""
    return no_trade(session=day, candidates=(candidate(CS1, EvidenceRung.EXPLORATORY, traded=False),
                                             candidate("school:N0@1", traded=False, n=2)))  # fmt: skip
