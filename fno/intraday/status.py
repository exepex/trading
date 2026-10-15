"""Whether a snapshot is good for its mark (story A16). One function decides it, used both when a snapshot is taken
(the ledger's status) and when a session's realised variance is computed from the stored snapshots, so the two can
never disagree.

The index level is usable only when taken on time (sent at or after the mark, answered within 120 s), with the
source's own time at most 120 s older than our receive time (design 5.2), and not identical to the previous mark's
level (a stale quote repeated, design 2.1)."""

from __future__ import annotations

from dataclasses import dataclass

from .document import SnapshotDocument
from .slots import ON_TIME_SECONDS, window_end

GOOD, MISSED, LATE, STALE, FAILED, INCOMPLETE = "good", "missed", "late", "stale", "failed", "incomplete"
INDEX_FAILED = "index_failed"
INDEX_LATE = "index_late"
INDEX_TIME_MISSING = "index_time_missing"
INDEX_TIME_OLD = "index_time_old"
INDEX_REPEATED = "index_repeated"
SOURCE_AHEAD_OF_HOST = "source_ahead_of_host"
CONTRACTS_MISSING = "contracts_missing"
AHEAD_TOLERANCE_SECONDS = 5  # the source's time after our receive time by more than this: one clock is wrong
INDEX_STATUS = {
    INDEX_FAILED: FAILED, INDEX_LATE: LATE, INDEX_TIME_MISSING: STALE, INDEX_TIME_OLD: STALE, INDEX_REPEATED: STALE,
}  # fmt: skip


@dataclass(frozen=True)
class IndexCheck:
    level: float | None  # the usable level, None when the problem below makes it unusable
    problem: str  # empty when usable


@dataclass(frozen=True)
class SlotVerdict:
    status: str
    failures: tuple[str, ...]  # named reasons: the index problem, missing contracts, failed steps, clock notes


def index_check(doc: SnapshotDocument, previous_level: float | None) -> IndexCheck:
    """The index level if usable for the realised variance, else why not."""
    call = doc.index
    if call.failure or not doc.index_level or doc.index_level < 0 or call.response_received_at is None:
        return IndexCheck(None, INDEX_FAILED)
    if call.request_sent_at < doc.mark or call.response_received_at > window_end(doc.mark):
        return IndexCheck(None, INDEX_LATE)
    if doc.index_source_time is None:
        return IndexCheck(None, INDEX_TIME_MISSING)
    if (call.response_received_at - doc.index_source_time).total_seconds() > ON_TIME_SECONDS:
        return IndexCheck(None, INDEX_TIME_OLD)
    if previous_level is not None and doc.index_level == previous_level:
        return IndexCheck(None, INDEX_REPEATED)
    return IndexCheck(doc.index_level, "")


def verdict(doc: SnapshotDocument, previous_level: float | None) -> SlotVerdict:
    """The slot's status and every named reason behind it."""
    check = index_check(doc, previous_level)
    notes = [check.problem] if check.problem else []
    if not doc.chains or not doc.expected_contracts or doc.recorded_contracts < doc.expected_contracts:
        notes.append(CONTRACTS_MISSING)
    notes += [f for f in doc.failures if f not in notes]
    if _source_ahead(doc):
        notes.append(SOURCE_AHEAD_OF_HOST)
    if check.problem:
        status = INDEX_STATUS[check.problem]
    else:
        status = INCOMPLETE if (CONTRACTS_MISSING in notes or doc.failures) else GOOD
    return SlotVerdict(status, tuple(notes))


def _source_ahead(doc: SnapshotDocument) -> bool:
    received, source_time = doc.index.response_received_at, doc.index_source_time
    return bool(received and source_time and (source_time - received).total_seconds() > AHEAD_TOLERANCE_SECONDS)
