"""The 20:05 "How did today go" section (story MS-P1g): each rule driver's trade net, the three counts, refusals and
closures, and the fleet total labelled as separate hypothetical accounts. The fleet total and the candidates are rule
drivers only (orchestrator, 22 Oct 2026: separate experiments are never merged into one figure); controls and
measurement-only drivers have their own labelled lines. Tickets are never summed into rupees."""

from collections.abc import Iterable
from datetime import date

from ..constants import FLEET_TOTAL_LABEL, DriverRole, Outcome
from ..contracts.records import DecisionRecord, OutcomeRecord
from ..contracts.reports import SectionText
from .banner import banner_for, banner_line
from .inputs import DayInputs
from .lines import SIGNED_RUPEE, footer, paper_title

TITLE = "How did today go"
NONE_TODAY = "none"
CANDIDATE_OUTCOMES = (Outcome.TRADE, Outcome.TICKET)
OTHER_ROLES = (
    (DriverRole.CONTROL, "Control (not in the fleet total)"),
    (DriverRole.MEASUREMENT_ONLY, "Measurement only (not in the fleet total)"),
)
PROBLEM_OUTCOMES = (Outcome.REFUSED, Outcome.ROAD_CLOSED, Outcome.UNAVAILABLE)


class HowDidTodayGoSection:
    def __init__(self, inputs: DayInputs):
        self.inputs = inputs

    def render(self, session: date) -> SectionText:
        records = self.inputs.records(session)
        decisions = [r for r in records if isinstance(r, DecisionRecord)]
        money = [r for r in records if isinstance(r, OutcomeRecord) and not r.is_ticket]  # tickets never in rupees
        rule = [r for r in money if self._role(r) is DriverRole.RULE]
        closed_roads = {(d.road, d.decision.reason) for d in decisions if d.decision.outcome is Outcome.ROAD_CLOSED}
        candidates = sum(self._is_candidate(d) for d in decisions)
        banner = banner_for(len(closed_roads), candidates)
        lines = (
            banner_line(banner),
            *self.inputs.marks(session),
            *self._trades(rule),
            *self._counts(session),
            *_problems(decisions),
            f"Fleet total, rule drivers only: {SIGNED_RUPEE.format(amount=sum(r.net for r in rule))} "
            f"({FLEET_TOTAL_LABEL})",
            *self._other_accounts(money),
            *footer(),
        )
        return SectionText(paper_title(TITLE), lines, banner)

    def _role(self, record) -> DriverRole:
        return self.inputs.role_of(record.driver_id)

    def _is_candidate(self, decision: DecisionRecord) -> bool:
        """Only a rule driver's trade or ticket is a candidate: controls fire every open session by design."""
        return decision.decision.outcome in CANDIDATE_OUTCOMES and self.inputs.role_of(decision.decision.driver_id) is (
            DriverRole.RULE
        )

    def _trades(self, rule: Iterable[OutcomeRecord]) -> list[str]:
        lines = [f"{r.driver_id} {r.road}: net {SIGNED_RUPEE.format(amount=r.net)} ({r.exit_reason})" for r in rule]
        return lines or [f"Trades closed: {NONE_TODAY}"]

    def _other_accounts(self, money: Iterable[OutcomeRecord]) -> list[str]:
        """Controls and measurement-only drivers on their own labelled lines, never added to the fleet total."""
        lines = []
        for role, label in OTHER_ROLES:
            own = [r for r in money if self._role(r) is role]
            lines += [f"{label}: {r.driver_id} {r.road} net {SIGNED_RUPEE.format(amount=r.net)}" for r in own]
        return lines

    def _counts(self, session: date) -> list[str]:
        rows = [c for c in self.inputs.counts(session) if self.inputs.role_of(c.driver_id) is DriverRole.RULE]
        return ["Counts (eligible / fillable / executed):"] + [
            f"{c.driver_id} {c.road}: {c.eligible} / {c.fillable} / {c.executed}" for c in rows
        ]


def _problems(decisions: list[DecisionRecord]) -> list[str]:
    found = sorted({(d.decision.outcome.value, str(d.road), d.decision.driver_id, d.decision.reason) for d in decisions
                    if d.decision.outcome in PROBLEM_OUTCOMES})  # fmt: skip
    return [f"{outcome}: {driver} {road}, {reason}" for outcome, road, driver, reason in found] or [
        f"Refusals and closures: {NONE_TODAY}"
    ]
