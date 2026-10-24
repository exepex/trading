"""The recommendation record (story REC1a, sections 1 and 5): one per NSE session, written once. It holds both answers,
the evidence each version had at decision time, and the day's candidate set fixed at decision time (judge 620 S3 and
620.1), so the evening check never chooses its candidates with hindsight. A record that breaks a rule is refused when
it is made, so no reader ever meets one."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from ..school.contracts.codec import CanonicalRecord
from .constants import RECORD_KIND, RECORD_SCHEMA_VERSION, EvidenceRung, NoTradeReason, PaperAnswer, RealMoneyAnswer
from .rungs import VersionEvidence

SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")


class RecordRefused(ValueError):
    """A recommendation that breaks the story's rules, or bytes that do not read as one."""


@dataclass(frozen=True)
class RecordRef:
    """A sealed record the recommendation read, by path and SHA-256."""

    path: str
    sha256: str


@dataclass(frozen=True)
class Candidate:
    """One version's or control's decision of the day, as the recommendation saw it."""

    version: str
    rung: EvidenceRung
    decision: RecordRef
    traded: bool


@dataclass(frozen=True)
class Recommendation(CanonicalRecord):
    schema_version: int
    kind: str
    session: date
    made_at: datetime
    evidence_cutoff: datetime
    code_commit: str
    config_sha256: str
    rung_rule_sha256: str
    inputs: tuple[RecordRef, ...]
    versions: tuple[VersionEvidence, ...]
    candidates: tuple[Candidate, ...]
    real_money: RealMoneyAnswer
    eligible_version: str | None
    paper: PaperAnswer
    paper_trade: Candidate | None
    reason: NoTradeReason | None

    def __post_init__(self):
        if problems := _problems(self):
            raise RecordRefused("; ".join(problems))


def _problems(rec: Recommendation) -> list[str]:
    checks = (
        (rec.schema_version == RECORD_SCHEMA_VERSION and rec.kind == RECORD_KIND, "not a recommendation record v1"),
        (rec.made_at.utcoffset() is not None, "made_at has no time zone"),
        (rec.evidence_cutoff == rec.made_at, "evidence_cutoff is not made_at"),
        (COMMIT.fullmatch(rec.code_commit) is not None, "code_commit is not a commit id"),
        (all(_is_sha(h) for h in _hashes(rec)), "a SHA-256 is malformed"),
        (list(rec.candidates) == sorted(rec.candidates, key=_candidate_key), "candidates are not sorted"),
        ((rec.real_money is RealMoneyAnswer.ELIGIBLE_FOR_YOUR_OWN_REVIEW) == (rec.eligible_version is not None),
         "eligible_version must be named exactly when the real-money answer is eligible"),
        (_paper_consistent(rec), "the paper answer, its trade and its reason disagree"),
    )  # fmt: skip
    return [problem for ok, problem in checks if not ok]


def _paper_consistent(rec: Recommendation) -> bool:
    if rec.paper is PaperAnswer.NO_TRADE:
        return rec.reason is not None and rec.paper_trade is None
    trade = rec.paper_trade
    return (rec.reason is None and trade is not None and trade.traded and trade in rec.candidates
            and trade.rung is EvidenceRung.ESTABLISHED)  # fmt: skip


def _hashes(rec: Recommendation) -> list[str]:
    refs = [*rec.inputs, *(c.decision for c in rec.candidates)]
    return [rec.config_sha256, rec.rung_rule_sha256, *(ref.sha256 for ref in refs)]


def _is_sha(value: str) -> bool:
    return SHA256.fullmatch(value) is not None


def _candidate_key(candidate: Candidate) -> tuple[str, str]:
    return candidate.version, candidate.decision.path
