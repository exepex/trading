"""The recommender's #fno-desk line (story REC1b, section 3; judge 641 m2): it says it is the recommender's answer,
not the card's, gives both answers with their codes, the candidate counts per source (an unavailable source by name
with its status), the count of paper trades that are not recommendations, and the record's receipt. It names no
strike, price or strategy internal: only answers, codes, counts, version IDs and the record's path and hash."""

from __future__ import annotations

from .constants import REASON_TEXT, EvidenceRung, PaperAnswer, RealMoneyAnswer, SourceState
from .contracts import Recommendation, source_of
from .store import Saved

HEAD = "PAPER ONLY. Recommender (not the card) for {day:%d %b %Y}."
DO_NOT = "Real money: DO NOT TRADE ({why})."
ELIGIBLE = "Real money: {version} is eligible for your own review, never a buy (RM1)."
NO_TRADE = "Paper: NO TRADE ({code}: {text})."
TRADE = "Paper: TRADE of {version} (established, rung 3)."
SOURCE = "{name}: {count} candidate(s)"
UNAVAILABLE = "{name}: unavailable ({status})"
NOT_RECOMMENDED = "Paper, not a recommendation: {count} trade(s) of versions below rung 3."
RECORD = "Record {path}, SHA-256 {short}."
NO_PROVEN = "no version has passed"
NOT_ELIGIBLE = "no established version is eligible under the real-money gate, RM1"


def recommendation_line(record: Recommendation, saved: Saved) -> str:
    parts = [HEAD.format(day=record.session), _real_money(record), _paper(record), _sources(record) + ".",
             NOT_RECOMMENDED.format(count=_not_recommended(record)),
             RECORD.format(path=saved.path, short=saved.sha256[:12])]  # fmt: skip
    return " ".join(parts)


def _real_money(record: Recommendation) -> str:
    if record.real_money is RealMoneyAnswer.ELIGIBLE_FOR_YOUR_OWN_REVIEW:
        return ELIGIBLE.format(version=record.eligible_version)
    if not any(v.rung is EvidenceRung.ESTABLISHED for v in record.versions):
        return DO_NOT.format(why=NO_PROVEN)
    return DO_NOT.format(why=NOT_ELIGIBLE)


def _paper(record: Recommendation) -> str:
    if record.paper is PaperAnswer.PAPER_TRADE:
        return TRADE.format(version=record.paper_trade.version)
    return NO_TRADE.format(code=record.reason.value, text=REASON_TEXT[record.reason])


def _sources(record: Recommendation) -> str:
    lines = []
    for source in record.candidate_sources:
        if source.state is SourceState.UNAVAILABLE:
            lines.append(UNAVAILABLE.format(name=source.name.value, status=source.step_status))
        else:
            count = sum(1 for c in record.candidates if source_of(c.version) is source.name)
            lines.append(SOURCE.format(name=source.name.value, count=count))
    return "Candidates: " + "; ".join(lines)


def _not_recommended(record: Recommendation) -> int:
    return sum(1 for c in record.candidates if c.traded and c.rung is not EvidenceRung.ESTABLISHED)
