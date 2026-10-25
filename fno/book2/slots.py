"""Book 2's slots turned into picks (story F5 part 3, steps 2 and 3). Each slot is checked against its default's trade
envelope by D4's own `AuthorityEnvelope` and `resolve`, before D2 runs:
- allowed: the slot's choice is the pick (`follow_rule` the default as built; `trade` the named opportunity at its
  width and lots); `no_trade` picks nothing;
- shadow-only: the account takes the rule default, and the AI's choice is kept as the slot's shadow (day log);
- forbidden: the choice is still picked, so C4's `EnvelopeMode` blocks it on its own and its record reads "no trade,
  blocked by C4" with the attempt; a forbidden `no_trade` picks nothing.
The rule defaults come from D2's rule-default evaluation, never from the AI (judge 260)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..constants import Decision
from ..playbook.envelope import ActionStatus, AuthorityEnvelope, BookTerms, TradeEnvelope, VersionKey, resolve
from ..playbook.outcomes import DayEvaluation, Outcome
from ..playbook.selection import Pick

SHADOW_TAKEN = "rule default (the slot's choice is shadow-only: {reason})"


@dataclass(frozen=True)
class Default:
    opportunity_id: str
    terms: BookTerms


@dataclass(frozen=True)
class SlotResult:
    default: Default
    action: str
    pick: Pick | None  # what goes to D2's allocator, C2 and C4
    status: str  # the envelope's verdict on the choice
    why: str
    shadow: BookTerms | None = None  # a shadow-only trade choice, never the account's

    def record(self) -> dict:
        shadow = None if self.shadow is None else terms_json(self.shadow)
        return {"default": self.default.opportunity_id, "action": self.action, "status": self.status, "why": self.why,
                "pick": self.pick.to_json() if self.pick else None, "shadow": shadow}  # fmt: skip

    def stored(self) -> dict:
        """The pick as `inputs.json` keeps it, with its default's terms, so a replay gives C4 the same rule default."""
        return {**self.pick.to_json(), "default": {"opportunity_id": self.default.opportunity_id,
                                                   **terms_json(self.default.terms)}}  # fmt: skip


def terms_json(terms: BookTerms) -> dict:
    return {"version": list(terms.version), "width": terms.width, "lots": terms.lots}


def terms_from_json(data: Mapping) -> BookTerms:
    return BookTerms((str(data["version"][0]), int(data["version"][1])), float(data["width"]), int(data["lots"]))


def rule_defaults(evaluation: DayEvaluation) -> list[Default]:
    """D2's chosen trades in the sheet's order, with the terms D2 built."""
    return [Default(o.opportunity.opportunity_id, terms_of(o)) for o in evaluation.outcomes
            if o.decision == Decision.CHOSEN]  # fmt: skip


def terms_of(outcome: Outcome) -> BookTerms:
    built = outcome.candidate.proposal.terms
    return BookTerms(outcome.opportunity.strategy.key, float(built.width), int(built.lots))


class SlotResolver:
    def __init__(self, evaluation: DayEvaluation, envelopes: Mapping[VersionKey, TradeEnvelope]):
        """`evaluation`: D2's rule-default evaluation of the day, every opportunity of Book 2's tradable versions."""
        self.outcomes = {o.opportunity.opportunity_id: o for o in evaluation.outcomes}
        self.eligible, self.authority = evaluation.eligible, AuthorityEnvelope(envelopes)

    def resolve(self, slots: Sequence[Mapping], defaults: Sequence[Default]) -> list[SlotResult]:
        return [self._one(slot, default) for slot, default in zip(slots, defaults, strict=True)]

    def _one(self, slot: Mapping, default: Default) -> SlotResult:
        action, reason = slot["action"], slot["reason"]
        if action == "no_trade":
            verdict = self.authority.permits(None, default.terms, None, self.eligible)
            taken = resolve(None, default.terms, verdict).account
            pick = Pick(default.opportunity_id, SHADOW_TAKEN.format(reason=reason)) if taken else None
            return SlotResult(default, action, pick, verdict.status, verdict.reason)
        target = default.opportunity_id if action == "follow_rule" else slot["opportunity_id"]
        outcome = self.outcomes[target]
        choice = self._choice(outcome, slot) if action == "trade" else default.terms
        verdict = self.authority.permits(choice, default.terms, outcome.opportunity.strategy, self.eligible)
        if verdict.status == ActionStatus.SHADOW_ONLY:
            taken = Pick(default.opportunity_id, SHADOW_TAKEN.format(reason=reason))
            return SlotResult(default, action, taken, verdict.status, verdict.reason, choice)
        width, lots = (slot["width"], slot["lots"]) if action == "trade" else (None, None)
        return SlotResult(default, action, Pick(target, reason, width, lots), verdict.status, verdict.reason)

    @staticmethod
    def _choice(outcome: Outcome, slot: Mapping) -> BookTerms:
        """The traded terms: the slot's width and lots, else the candidate's as built, else the version's own."""
        spec = outcome.opportunity.strategy.structure
        built = outcome.candidate.proposal.terms if outcome.candidate else None
        width = slot["width"] if slot["width"] is not None else (built.width if built else spec.widths[0])
        lots = slot["lots"] if slot["lots"] is not None else (built.lots if built else spec.lots)
        return BookTerms(outcome.opportunity.strategy.key, float(width), int(lots))
