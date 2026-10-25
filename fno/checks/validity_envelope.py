"""C4's Book 2 mode (story D4, criteria 2, 4, 5 and 9): the playbook mode's checks on the version the trade claims,
with lots allowed down to 1 but never above the version's, then the authority envelope of that version, checked
independently of the decider, among the versions D2 found eligible that day (fired with a valid candidate), never
the approved list alone. The envelope file's hash must equal the version's registered D6 component
(`trade_envelope:<name>-v<n>`): a file edited after registration fails closed. The action must be `allowed`: a
`shadow-only` action is never the account's trade (the account takes the rule default), and a forbidden one fails.
A damaged envelope file fails the named `envelope` check. The unproven limit is checked again here, independently of
D2's allocator (story F5, judge 260 addendum 2): a version with fewer than 20 completed paper trades may hold at most
one open trade, counting the book's trades that passed C4 earlier the same day."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date

from ..constants import UNPROVEN_BELOW_COMPLETED_TRADES, UNPROVEN_MAX_OPEN_TRADES
from ..playbook.envelope import AuthorityEnvelope, BookTerms, TradeEnvelope, VersionKey
from ..playbook.envelope_files import EnvelopeError, component_key
from .validity_evidence import Evidence
from .validity_modes import PlaybookMode, ValidityMode
from .validity_proposal import CheckResult, ValidityProposal
from .validity_shapes import Shape

RegisteredComponents = Callable[[str, date], Mapping[str, str]]  # (book, day) -> the active D6 version's components


NO_COUNTS = "no paper-trade counts given for the version: fails closed"
UNPROVEN = "{completed} completed paper trades (limit applies below {below}); {holding} open or passed earlier today"


def at_most_lots(lots: int, version_lots: int) -> bool:
    return 1 <= lots <= version_lots


def unproven_check(proposal: ValidityProposal, key: VersionKey) -> CheckResult:
    if proposal.version_counts is None:
        return CheckResult("unproven", False, NO_COUNTS)
    completed, held = proposal.version_counts
    holding = held + sum(1 for e in proposal.earlier if e.strategy is not None and e.strategy.key == key)
    ok = completed >= UNPROVEN_BELOW_COMPLETED_TRADES or holding < UNPROVEN_MAX_OPEN_TRADES
    reason = UNPROVEN.format(completed=completed, below=UNPROVEN_BELOW_COMPLETED_TRADES, holding=holding)
    return CheckResult("unproven", ok, reason, {"completed": completed, "holding": holding})


class EnvelopeMode(ValidityMode):
    name = "envelope"

    def __init__(self, shapes: Mapping[str, Shape], envelopes: Callable[[], Mapping[VersionKey, TradeEnvelope]],
                 registered: RegisteredComponents):  # fmt: skip
        self.playbook = PlaybookMode(shapes, lots_rule=at_most_lots)
        self.envelopes, self.registered = envelopes, registered

    def checks(self, proposal: ValidityProposal, evidence: Evidence | None) -> list[CheckResult]:
        results = self.playbook.checks(proposal, evidence)
        strategy = proposal.strategy
        if strategy is None:
            return results
        try:
            envelopes = self.envelopes()
        except EnvelopeError as damaged:
            return results + [CheckResult("envelope", False, f"damaged trade envelope: {damaged}")]
        key = strategy.key
        envelope = envelopes.get(key)
        if envelope is None:
            return results + [CheckResult("envelope", False, f"no trade envelope for {key[0]} v{key[1]}")]
        component = self.registered(proposal.book, proposal.day).get(component_key(key))
        shown = f"file {envelope.sha256[:12]} vs registered {(component or 'none')[:12]}"
        results.append(CheckResult("envelope_registered", envelope.sha256 == component, shown))
        results.append(unproven_check(proposal, key))
        if proposal.rule_default is None:
            return results + [CheckResult("envelope", False, "no rule default given: the rules offered no trade")]
        choice = BookTerms(key, proposal.width, proposal.lots)
        verdict = AuthorityEnvelope(envelopes).permits(choice, proposal.rule_default, strategy, proposal.eligible)
        verdict_check = CheckResult("envelope", verdict.allowed, f"{verdict.status}: {verdict.reason}")
        return results + [verdict_check]
