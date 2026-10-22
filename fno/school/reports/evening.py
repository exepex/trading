"""The 20:05 "How did today go" section (story MS-P1g): each rule driver's trade net, the three counts, refusals and
closures, and the fleet total labelled as separate hypothetical accounts. Tickets are never summed into rupees."""

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
PROBLEM_OUTCOMES = (Outcome.REFUSED, Outcome.ROAD_CLOSED, Outcome.UNAVAILABLE)


class HowDidTodayGoSection:
    def __init__(self, inputs: DayInputs):
        self.inputs = inputs

    def render(self, session: date) -> SectionText:
        records = self.inputs.records(session)
        decisions = [r for r in records if isinstance(r, DecisionRecord)]
        money = [r for r in records if isinstance(r, OutcomeRecord) and not r.is_ticket]  # tickets never in rupees
        closed_roads = {(d.road, d.decision.reason) for d in decisions if d.decision.outcome is Outcome.ROAD_CLOSED}
        candidates = sum(d.decision.outcome in CANDIDATE_OUTCOMES for d in decisions)
        banner = banner_for(len(closed_roads), candidates)
        lines = (
            banner_line(banner),
            *self._trades(money),
            *self._counts(session),
            *_problems(decisions),
            f"Fleet total: {SIGNED_RUPEE.format(amount=sum(r.net for r in money))} ({FLEET_TOTAL_LABEL})",
            *footer(),
        )
        return SectionText(paper_title(TITLE), lines, banner)

    def _trades(self, money: Iterable[OutcomeRecord]) -> list[str]:
        shown = [r for r in money if self.inputs.role_of(r.driver_id) is DriverRole.RULE]
        lines = [f"{r.driver_id} {r.road}: net {SIGNED_RUPEE.format(amount=r.net)} ({r.exit_reason})" for r in shown]
        return lines or [f"Trades closed: {NONE_TODAY}"]

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
