"""G1-G3 run by code (story R1b): each gate runs once, in order, on a card whose inputs are committed, and logs one
gate-log row. A measurement (B0, FT1) is never screened (R3's registration procedure, step 1). Changing a card's inputs
after its numbers are seen makes a new idea (FACTORY_RULES section 2), so no gate re-runs."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Protocol

from .card import IdeaCard
from .constants import GATES_FILE, Gate, Outcome
from .cost_wall import Screen, screen
from .data_spend import SpendVerdict, data_spend, parse_register
from .gate_log import GateLog, GateRow, figures
from .gate_numbers import plan_numbers, screen_numbers, spend_numbers
from .inputs import plan_inputs, screen_inputs, spend_inputs
from .sample_plan import SamplePlan, sample_plan


class GateStepError(ValueError):
    """The gate did not run; nothing was logged."""


class StepGit(Protocol):
    def head(self) -> str: ...

    def staged_paths(self) -> list[str]: ...

    def tree_matches(self, commit: str, paths: tuple[str, ...]) -> bool: ...


class GateSteps:
    def __init__(self, gates: GateLog, git: StepGit, charges: dict, register_text: Callable[[], str]):
        self.gates, self.git, self.charges, self.register_text = gates, git, charges, register_text

    def screen(self, card: IdeaCard, today: date) -> Screen:
        self._ready(card, Gate.IDEA_CARD, (Outcome.IDEA,))
        result = screen(screen_inputs(card, self.charges))
        self._log(card, Gate.SCREEN, result.outcome, today, screen_numbers(result))
        return result

    def spend(self, card: IdeaCard, today: date) -> SpendVerdict:
        self._ready(card, Gate.SCREEN, (Outcome.PASSED,))
        data_sets, _ = spend_inputs(card)
        verdict = data_spend(parse_register(self.register_text()), data_sets, card.trial_id, card.path)
        self._log(card, Gate.DATA_SPEND, verdict.outcome, today, spend_numbers(verdict))
        return verdict

    def plan(self, card: IdeaCard, today: date) -> SamplePlan:
        self._ready(card, Gate.DATA_SPEND, (Outcome.FRESH, Outcome.EXPLORATORY))
        inputs = plan_inputs(card)
        net = float(figures(self._row(card, Gate.SCREEN))["net"])
        plan = sample_plan(inputs.sd_per_trade, net, inputs.frequency_per_year, inputs.pass_level)
        self._log(card, Gate.SAMPLE_PLAN, plan.outcome, today, plan_numbers(plan))
        return plan

    def _ready(self, card: IdeaCard, after: Gate, outcomes: tuple[Outcome, ...]) -> None:
        if card.measurement:
            raise GateStepError(f"{card.path}: a measurement is never screened (R3 registration, step 1)")
        others = sorted(set(self.git.staged_paths()) - {GATES_FILE})
        if others:
            raise GateStepError(f"other files are staged ({', '.join(others)}): commit them first")
        if not self.git.tree_matches(self.git.head(), (card.path,)):
            raise GateStepError(f"{card.path} has uncommitted changes: commit its inputs before its gate runs")
        self.gates.require_append_only()
        last = self.gates.last(card.trial_id)
        if last is None or last.gate != after or last.outcome not in outcomes:
            reached = f"{last.gate} {last.outcome}" if last else "no gate"
            wanted = " or ".join(f"{after} {outcome}" for outcome in outcomes)
            raise GateStepError(f"trial {card.trial_id}: its last gate is {reached}; this gate runs after {wanted}")

    def _row(self, card: IdeaCard, gate: Gate) -> GateRow:
        return next(row for row in self.gates.rows() if row.trial_id == card.trial_id and row.gate == gate)

    def _log(self, card: IdeaCard, gate: Gate, outcome: Outcome, today: date, numbers: str) -> None:
        self.gates.append(GateRow(card.trial_id, gate, outcome, today.isoformat(), self.git.head(), numbers))
