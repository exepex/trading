"""An AI book's picks among D2's built candidates (story F6, shared with F5 for Book 2). D2's `RuleEvaluator` builds
every candidate as for Book 1; this allocator, behind the same `allocate` signature as D2's `Allocator`, sends only
the picked ones to D2's `Allocator` (C2, the unproven-version limit, and the no-trade threshold when `threshold` is
on), and marks every other candidate "not chosen by <book>". A pick may carry a width or lots only when the book
supplies `rebuild` (Book 2's envelope rebuilds the candidate with D2's `CandidateBuilder`); Book 3 never does, so such
a pick is refused. A pick that is not a built candidate today, or whose rebuild fails, is never traded and is listed
in `attempted`. C2's refusal reasons stay exactly as D2 writes them ("slot: ...", "cash: ...", "risk: ...")."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass

from ..constants import Decision
from ..risk.inputs import Market, RiskBook
from .allocation import Allocator, Placed, StrategyTradeCounts
from .candidates import Candidate, NotBuilt

PICKED = "picked by {book}: {reason}"
NOT_CHOSEN = "not chosen by {book}"
NO_REBUILD = "{book} picks cannot change width or lots"
NOT_REBUILT = "rebuild refused: {why}"
NOT_A_CANDIDATE = "not a built candidate today"
NAMED_TWICE = "named twice: the first pick of an opportunity stands"


@dataclass(frozen=True)
class Pick:
    opportunity_id: str
    reason: str
    width: float | None = None
    lots: int | None = None

    @property
    def changes_terms(self) -> bool:
        return self.width is not None or self.lots is not None

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Mapping) -> Pick:
        return cls(str(data["opportunity_id"]), str(data["reason"]), data.get("width"), data.get("lots"))


Rebuild = Callable[[Candidate, Pick], Candidate]


@dataclass(frozen=True)
class Attempt:
    pick: Pick
    why: str


class SelectionAllocator:
    def __init__(self, allocator: Allocator, picks: Sequence[Pick], book: str, threshold: bool,
                 rebuild: Rebuild | None = None):  # fmt: skip
        self.allocator, self.book, self.threshold, self.rebuild = allocator, book, threshold, rebuild
        self.picks: dict[str, Pick] = {}
        self._seen: set[str] = set()
        self._refused: list[Attempt] = []
        for pick in picks:  # the first pick of an ID wins; a repeat is refused alone, never silently dropped
            if pick.opportunity_id in self.picks:
                self._refused.append(Attempt(pick, NAMED_TWICE))
            else:
                self.picks[pick.opportunity_id] = pick

    @property
    def attempted(self) -> list[Attempt]:
        """Every pick that cannot trade: not a built candidate in any `allocate` call so far, refused for its terms,
        or a failed rebuild."""
        missing = [Attempt(p, NOT_A_CANDIDATE) for i, p in sorted(self.picks.items()) if i not in self._seen]
        return [*self._refused, *missing]

    def allocate(self, candidates: Sequence[Candidate], book: RiskBook, market: Market, counts: StrategyTradeCounts,
                 threshold: bool = True) -> list[Placed]:  # fmt: skip
        """`threshold` (D2's per-call flag) is ignored: this book's own setting applies to its picks."""
        placed: list[Placed] = []
        picked: dict[str, Pick] = {}
        to_risk: list[Candidate] = []
        for candidate in candidates:
            opportunity_id = candidate.opportunity.opportunity_id
            self._seen.add(opportunity_id)
            pick = self.picks.get(opportunity_id)
            if pick is None:
                placed.append((candidate, Decision.NOT_CHOSEN, NOT_CHOSEN.format(book=self.book), None))
                continue
            ready, refusal = self._terms(candidate, pick)
            if ready is None:
                self._refused.append(Attempt(pick, refusal))
                placed.append((candidate, Decision.NOT_CHOSEN, refusal, None))
                continue
            picked[opportunity_id] = pick
            to_risk.append(ready)
        for candidate, decision, reason, risk in self.allocator.allocate(to_risk, book, market, counts, self.threshold):
            if decision == Decision.CHOSEN:
                pick = picked[candidate.opportunity.opportunity_id]
                reason = PICKED.format(book=self.book, reason=pick.reason)
            placed.append((candidate, decision, reason, risk))
        return placed

    def _terms(self, candidate: Candidate, pick: Pick) -> tuple[Candidate | None, str]:
        if not pick.changes_terms:
            return candidate, ""
        if self.rebuild is None:
            return None, NO_REBUILD.format(book=self.book)
        try:
            return self.rebuild(candidate, pick), ""
        except NotBuilt as why:
            return None, NOT_REBUILT.format(why=why)
