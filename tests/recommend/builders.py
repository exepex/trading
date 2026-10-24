"""A valid recommendation and its parts, for REC1's tests: each test changes one thing."""

from dataclasses import replace
from datetime import UTC, date, datetime

from fno.recommend.constants import (
    RECORD_KIND,
    RECORD_SCHEMA_VERSION,
    EvidenceRung,
    NoTradeReason,
    PaperAnswer,
    RealMoneyAnswer,
)
from fno.recommend.contracts import Candidate, Recommendation, RecordRef
from fno.recommend.rungs import RUNG_RULE_SHA256, VersionEvidence

DAY = date(2026, 11, 2)
MADE_AT = datetime(2026, 11, 2, 9, 50, tzinfo=UTC)  # 15:20 IST


def sha(n: int) -> str:
    return f"{n:064x}"


def candidate(version: str = "school:CS1@1", rung: EvidenceRung = EvidenceRung.UNPROVEN, traded: bool = True,
              n: int = 1) -> Candidate:  # fmt: skip
    return Candidate(version, rung, RecordRef(f"school/dashcam/{version}/{DAY}.json", sha(n)), traded)


def no_trade(**changes) -> Recommendation:
    record = Recommendation(
        schema_version=RECORD_SCHEMA_VERSION, kind=RECORD_KIND, session=DAY, made_at=MADE_AT,
        evidence_cutoff=MADE_AT, code_commit="a" * 40, config_sha256=sha(7), rung_rule_sha256=RUNG_RULE_SHA256,
        inputs=(RecordRef("playbook/registry.csv", sha(8)),),
        versions=(VersionEvidence("school:CS1@1", EvidenceRung.EXPLORATORY, 3, date(2026, 10, 28), date(2026, 11, 1)),),
        candidates=(candidate("school:CS1@1", EvidenceRung.EXPLORATORY), candidate("school:N0@1", traded=False, n=2)),
        real_money=RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY, eligible_version=None, paper=PaperAnswer.NO_TRADE,
        paper_trade=None, reason=NoTradeReason.NO_ESTABLISHED_VERSION,
    )  # fmt: skip
    return replace(record, **changes) if changes else record


def paper_trade(rung: EvidenceRung = EvidenceRung.ESTABLISHED) -> Recommendation:
    trade = candidate("school:CS1@1", rung)
    return no_trade(candidates=(trade,), paper=PaperAnswer.PAPER_TRADE, paper_trade=trade, reason=None)
