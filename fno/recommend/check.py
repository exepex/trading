"""The evening check of one recommended day (story REC1c): every candidate the recommendation fixed at decision time,
looked up in its sealed outcomes, each reported and summed; never a new search of the day's decisions, never a price.
A candidate that traded and has no outcome yet is open, so the day is not known yet; a candidate whose outcome
cannot be read fails the whole check, never a smaller total (judge 620 S3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime

from .check_record import (
    CHECK_KIND,
    CHECK_SCHEMA_VERSION,
    CandidateResult,
    CandidateState,
    CheckRecord,
    verdict_for,
)
from .constants import SourceState
from .contracts import Candidate, Recommendation


@dataclass(frozen=True)
class FoundOutcome:
    net: float  # rupees after every charge
    is_ticket: bool


class OutcomeLookup(ABC):
    @abstractmethod
    def outcome(self, candidate: Candidate, session: date, until: date) -> FoundOutcome | None:
        """The candidate's sealed closed outcome between its session and `until`, None while none is sealed; an
        unreadable outcome raises `InputFailed`."""


def check(record: Recommendation, record_sha256: str, checked_on: date, made_at: datetime,
          lookup: OutcomeLookup) -> CheckRecord:  # fmt: skip
    results = tuple(_result(c, record.session, checked_on, lookup) for c in record.candidates)
    unavailable = tuple(sorted(s.name.value for s in record.candidate_sources if s.state is SourceState.UNAVAILABLE))
    closed = [r.net for r in results if r.state is CandidateState.CLOSED]
    open_trades = sum(r.state is CandidateState.OPEN for r in results)
    return CheckRecord(
        schema_version=CHECK_SCHEMA_VERSION, kind=CHECK_KIND, session=record.session, checked_on=checked_on,
        made_at=made_at, recommendation_sha256=record_sha256, results=results, closed_net=round(sum(closed), 2),
        open_trades=open_trades, unavailable_sources=unavailable, verdict=verdict_for(unavailable, open_trades),
    )  # fmt: skip


def _result(candidate: Candidate, session: date, until: date, lookup: OutcomeLookup) -> CandidateResult:
    found = lookup.outcome(candidate, session, until)
    key = (candidate.version, candidate.decision.path)
    if found is not None and found.is_ticket:
        return CandidateResult(*key, CandidateState.TICKET, found.net)  # a ticket is never counted as a trade
    if not candidate.traded:
        return CandidateResult(*key, CandidateState.NO_TRADE, None)
    if found is None:
        return CandidateResult(*key, CandidateState.OPEN, None)
    return CandidateResult(*key, CandidateState.CLOSED, found.net)
