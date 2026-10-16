"""Book 3's decider (story F6), behind F1t's `AiBookDecider` port: an accepted answer becomes one D3 run with C2 and
C4 inside, the day's proposals registered by D5, the day log and F7's shadow file. Each step is code:
1. the shape (`check_decision`) and every cited card against the cards the session was given;
2. Book 3's tradable strategies at the base commit (registered before today, D5's checks), before anything is
   registered today, so a proposal of today is on no sheet and in no decision;
3. the day sheet the session saw (the private pack's `evaluation`) must be the one D2 gives again now;
4. D2's evaluation with the picks (`SelectionAllocator`: C2, the unproven limit), C4's `ConstitutionMode`, D3's records
   with the picks in `inputs.json` for replay;
5. the proposals, each registered or refused alone; the day log; the shadow file, whatever happened to the picks.
F1t snapshots every file under Book 3's write paths before calling `decide` and restores them if anything fails."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from ..books.book1 import Book1Inputs
from ..playbook.decision_run import DecisionRun
from ..playbook.evaluate import RuleEvaluator
from ..playbook.selection import Pick
from .answer import check_decision
from .day_log import write_day_log
from .evaluation import Book3Evaluators, day_sheet, sheet_candidates
from .proposals import Book3Proposer
from .shadow_file import Widths, shadow_body, write_shadow
from .strategies import Book3Strategies

NO_SHEET = "the private pack holds no day sheet (`evaluation`): Book 3 saw no candidates"
SHEET_DIFFERS = "the day sheet does not reproduce now (pack {seen}, now {now}): nothing decided"
UNKNOWN_CARDS = "cards_used names cards the session was not given: {cards}"
NO_ROLE_SET = "none"


class DecisionRefused(ValueError):
    """No run can be written (F1t's port: the book-day is `refused`)."""


class Accepted(Protocol):
    """What the decider reads of F1t's `AcceptedDecision`."""

    day: date
    registered_model: str
    model_reported: str
    session: str
    common_pack: object  # CommonPack: `.sha256`, `.body["opportunities"]`
    private_pack: object  # PrivatePack: `.sha256`, `.body["evaluation"]`
    decision: dict
    analyst_cards: Mapping | None


@dataclass(frozen=True)
class DecidedRun:
    run: Path
    files: tuple[Path, ...] = ()


RunFactory = Callable[[RuleEvaluator, Sequence[Mapping]], DecisionRun]  # (evaluator, stored picks) -> D3's run


class Book3Decider:
    def __init__(self, root: Path, inputs: Book1Inputs, strategies: Book3Strategies, evaluators: Book3Evaluators,
                 proposer: Book3Proposer, runs: RunFactory, head: Callable[[], str],
                 served: Callable[[date], Mapping[str, str]],
                 widths: Widths, prompt_version: str):  # fmt: skip
        """`served(day)`: Book 3's own D6 components (`constitution`, `book3_prompt`) in every record's `served`."""
        self.root, self.inputs, self.strategies, self.evaluators = Path(root), inputs, strategies, evaluators
        self.proposer, self.runs, self.head, self.served = proposer, runs, head, served
        self.widths, self.prompt_version = widths, prompt_version

    def decide(self, accepted: Accepted) -> DecidedRun:
        decision, day = accepted.decision, accepted.day
        problems = check_decision(decision)
        if problems:
            raise DecisionRefused("; ".join(problems))
        card_ids, role_set = _cards(accepted.analyst_cards)
        unknown = sorted(set(decision["cards_used"]) - card_ids)
        if unknown:
            raise DecisionRefused(UNKNOWN_CARDS.format(cards=", ".join(unknown)))
        tradable = self.strategies.on(day, self.head())
        today = self.inputs.day(day)
        arguments = (day, tradable.snapshot.playbook(), today.market, today.features, today.book, today.counts,
                     today.shadow)  # fmt: skip
        self._require_sheet(accepted, arguments, tradable.snapshot.commit)
        picks = [Pick(t["opportunity_id"], t["reason"]) for t in decision["trades"]]
        evaluator, selection = self.evaluators.with_picks(picks)
        run = self.runs(evaluator, [p.to_json() for p in picks]).decide(
            day, tradable.snapshot, today.market, today.features, today.book, today.counts, today.shadow,
            self._context(today.context, accepted),
        )  # fmt: skip
        entries = self.proposer.register_all(day, decision["proposals"], accepted.registered_model,
                                             self.prompt_version, role_set)  # fmt: skip
        log = write_day_log(self.root, day, entries, selection.attempted, tradable.excluded)
        body = shadow_body(day, accepted.common_pack.sha256, accepted.common_pack.body["opportunities"],
                           decision["shadow"], self.widths)  # fmt: skip
        return DecidedRun(run, (log, write_shadow(self.root, body)))

    def _require_sheet(self, accepted: Accepted, arguments: tuple, commit: str) -> None:
        seen = accepted.private_pack.body.get("evaluation")
        if seen is None:
            raise DecisionRefused(NO_SHEET)
        evaluator, _ = self.evaluators.with_picks(())
        now = day_sheet(arguments[0], evaluator.evaluate(*arguments), commit)
        if sheet_candidates(seen) != sheet_candidates(now):
            raise DecisionRefused(SHEET_DIFFERS.format(seen=sorted(sheet_candidates(seen)),
                                                       now=sorted(sheet_candidates(now))))  # fmt: skip

    def _context(self, context: Mapping, accepted: Accepted) -> dict:
        """The run's context: the inputs' own (code, config, D6 version), the packs the session was fired with, the
        model F1t checked, the session link and Book 3's served components."""
        return {**context, "common_pack_sha256": accepted.common_pack.sha256,
                "private_pack_sha256": accepted.private_pack.sha256, "model_served": accepted.model_reported,
                "session_id": accepted.session, "served": dict(self.served(accepted.day))}  # fmt: skip


def _cards(item: Mapping | None) -> tuple[set[str], str]:
    """(the card IDs given, the registered role set); no item means no role is registered yet (F2's rule)."""
    if not item:
        return set(), NO_ROLE_SET
    return set(item.get("card_ids", ())), str(item.get("role_set_version") or NO_ROLE_SET)
