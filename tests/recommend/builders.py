"""A valid recommendation and its parts, for REC1's tests: each test changes one thing."""

from dataclasses import replace
from datetime import UTC, date, datetime

from fno.recommend.constants import (
    RECORD_KIND,
    RECORD_SCHEMA_VERSION,
    CandidateSourceName,
    EvidenceRung,
    NoTradeReason,
    PaperAnswer,
    RealMoneyAnswer,
    SourceState,
)
from fno.recommend.contracts import Candidate, CandidateSource, Recommendation
from fno.recommend.refs import RecordRef
from fno.recommend.rungs import RUNG_RULE_SHA256, EvidenceReports, VersionEvidence

DAY = date(2026, 11, 2)
COMPLETE = tuple(CandidateSource(name, SourceState.COMPLETE, None) for name in sorted(CandidateSourceName))
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
        versions=(evidence_of("school:CS1@1", EvidenceRung.EXPLORATORY), evidence_of("school:N0@1")),
        candidates=(candidate("school:CS1@1", EvidenceRung.EXPLORATORY), candidate("school:N0@1", traded=False, n=2)),
        candidate_sources=COMPLETE, braked_versions=(),
        real_money=RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY, eligible_version=None, paper=PaperAnswer.NO_TRADE,
        paper_trade=None, reason=NoTradeReason.NO_ESTABLISHED_VERSION,
    )  # fmt: skip
    return replace(record, **changes) if changes else record


def report(name: str, n: int) -> RecordRef:
    return RecordRef(f"research/recommend/reports/{name}.md", sha(n))


REVIEWED = EvidenceReports(review=report("p2_review", 20))
ESTABLISHED = EvidenceReports(report("p2_review", 20), report("sample_plan", 21), report("lower_bound", 22),
                              report("second_window", 23))  # fmt: skip
REPORTS = {EvidenceRung.UNPROVEN: EvidenceReports(), EvidenceRung.EXPLORATORY: EvidenceReports(),
           EvidenceRung.WATCHING: REVIEWED, EvidenceRung.ESTABLISHED: ESTABLISHED}  # fmt: skip


def evidence_of(version: str, rung: EvidenceRung = EvidenceRung.UNPROVEN) -> VersionEvidence:
    """The record's evidence line for a version at `rung`, with the count and reports the rung rule needs for it."""
    if rung is EvidenceRung.UNPROVEN:
        return VersionEvidence(version, rung, 0, None, None, REPORTS[rung])
    counted = 3 if rung is EvidenceRung.EXPLORATORY else 30
    return VersionEvidence(version, rung, counted, date(2026, 9, 1), date(2026, 11, 1), REPORTS[rung])


def paper_trade(rung: EvidenceRung = EvidenceRung.ESTABLISHED) -> Recommendation:
    trade = candidate("school:CS1@1", rung)
    return no_trade(versions=(evidence_of("school:CS1@1", rung),), candidates=(trade,), paper=PaperAnswer.PAPER_TRADE,
                    paper_trade=trade, reason=None)  # fmt: skip


def established_day(**changes) -> Recommendation:
    """A no-trade day on which one version is established (rung 3) and made no trade."""
    quiet = candidate("school:CS1@1", EvidenceRung.ESTABLISHED, traded=False)
    day = {"versions": (evidence_of("school:CS1@1", EvidenceRung.ESTABLISHED),), "candidates": (quiet,),
           "reason": NoTradeReason.NO_CANDIDATE}  # fmt: skip
    return no_trade(**(day | changes))
