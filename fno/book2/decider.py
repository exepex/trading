"""Book 2's decider (story F5 part 3), behind F1t's `AiBookDecider` port: an accepted answer becomes one D3 run with
C2 and C4 inside, and Book 2's day log. Each step is code:
1. the shape against the sheet the session saw (`check_decision`: one slot per rule default, opportunities on it);
2. that sheet must be exactly what D2 gives again now, on the packs the session was fired with, from Book 2's view
   (paper versions and registered research candidates, minus Book 2's pauses);
3. each slot against its default's trade envelope (`SlotResolver`); a blocking judge keeps no pick at all;
4. D2 with the picks (`SelectionAllocator`: C2, the unproven limit, the threshold on paper versions only), C4's
   `EnvelopeMode` with the slot's rule default and the recorded counts, D3's records with the picks and their defaults
   in `inputs.json` for replay;
5. every chosen record must carry `served.strategy_status` (criterion 15), before F1t's own check.
F1t snapshots Book 2's write paths before calling `decide` and puts them back if anything fails."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path

from ..ai_trading.fired_packs import require_fired_packs
from ..ai_trading.ports import SERVED_VERSION, AcceptedDecision, AiBookDecider, DecidedRun, DecisionRefused
from ..books.book1 import Book1Inputs
from ..books.paths import book_folder
from ..constants import BOOK2_HYBRID, VALIDITY_FAILURES_FILE, Decision, PlaybookStatus
from ..playbook.allocation import StrategyTradeCounts
from ..playbook.decision_inputs import PlaybookSnapshot
from ..playbook.decision_record import NO_TRADE_ID
from ..playbook.decision_run import DecisionRun
from ..playbook.envelope import BookTerms, TradeEnvelope, VersionKey
from ..playbook.envelope_files import served_envelopes
from ..playbook.evaluate import RuleEvaluator
from ..playbook.outcomes import DayEvaluation
from ..playbook.selection import NOT_CHOSEN
from .answer import check_decision
from .day_log import log_path, write_day_log
from .evaluation import Book2Evaluators
from .sheet import book2_snapshot, day_sheet
from .slots import SlotResolver, SlotResult, rule_defaults

NO_SHEET = "the private pack holds no day sheet (`evaluation`): Book 2 saw no rule default"
SHEET_DIFFERS = "the day sheet does not reproduce now ({part} differs): nothing decided"
NO_STATUS = "a chosen record lacks served.strategy_status: the strategy label needs it"
SHEET_PARTS = ("opportunities", "rule_default", "eligible", "paused")

NO_DEFAULT = "the rules offered no trade: nothing to check"
JUDGE_BLOCKED = "the judge's verdict blocks: no pick, the rule default kept as a shadow"
JUDGE_FAILED, JUDGE_UNAVAILABLE = "no trade, judge failed", "no trade, judge unavailable"  # criterion 11
SAME_PICK = "two slots resolve to the same opportunity ({ids}): nothing decided"

# (evaluator, stored picks, each pick's rule default terms, the run's counts, the rule's action per opportunity)
#   -> D3's run with Book 2's C4 validator
RunFactory = Callable[[RuleEvaluator, Sequence[Mapping], Mapping[str, BookTerms], StrategyTradeCounts,
                       Mapping[str, str]], DecisionRun]  # fmt: skip


class Book2Decider(AiBookDecider):
    def __init__(self, root: Path, inputs: Book1Inputs, snapshot: Callable[[], PlaybookSnapshot],
                 paused: Callable[[date], Sequence[str]], evaluators: Book2Evaluators, runs: RunFactory,
                 envelopes: Callable[[], Mapping[VersionKey, TradeEnvelope]],
                 served: Callable[[date], Mapping[str, str]]):  # fmt: skip
        """`served(day)`: Book 2's own components besides the envelopes (its prompt) in every record's `served`."""
        self.root, self.inputs, self.snapshot, self.paused = Path(root), inputs, snapshot, paused
        self.evaluators, self.runs, self.envelopes, self.served = evaluators, runs, envelopes, served

    def decide(self, accepted: AcceptedDecision) -> DecidedRun:
        decision, day = accepted.decision, accepted.day
        seen = accepted.private_pack.body.get("evaluation")
        if not isinstance(seen, Mapping):
            raise DecisionRefused(NO_SHEET)
        problems = check_decision(decision, seen)
        if problems:
            raise DecisionRefused("; ".join(problems))
        if (self.root / log_path(day)).exists():
            raise DecisionRefused(f"{log_path(day)} is already written: Book 2 decides once a day")
        today = self.inputs.day(day)
        require_fired_packs(today.context, accepted)
        snapshot = book2_snapshot(self.snapshot(), self.paused(day))
        arguments = (day, snapshot.playbook(), today.market, today.features, today.book, today.counts, today.shadow)
        rule = self.evaluators.rule_default().evaluate(*arguments)
        _require_same_sheet(seen, day_sheet(day, rule, snapshot))
        defaults = rule_defaults(rule)
        slots = [] if accepted.judge_blocks else SlotResolver(rule, self.envelopes()).resolve(decision["slots"],
                                                                                           defaults)  # fmt: skip
        taken = [s for s in slots if s.pick is not None]
        _require_one_pick_each(taken)
        unpicked = self._judge_reason(accepted) if accepted.judge_blocks else NOT_CHOSEN
        evaluator, selection = self.evaluators.with_picks([s.pick for s in taken], today.market, unpicked)
        paired = {s.pick.opportunity_id: s.default.terms for s in taken}
        context = {**self._context(today.context, accepted, _status(seen, taken), snapshot.playbook().approved_on(day)),
                   "authority_check": _authority(slots, accepted.judge_blocks)}  # fmt: skip
        run = self.runs(evaluator, [s.stored() for s in taken], paired, today.counts, _rule_actions(rule)).decide(
            day, snapshot, today.market, today.features, today.book, today.counts, today.shadow, context
        )
        _require_labelled(run)
        blocked = defaults if accepted.judge_blocks else None
        trades = {d["opportunity_id"]: d["trade"] for d in seen["rule_default"]}
        log = write_day_log(self.root, day, decision["reason"], slots, selection.attempted, blocked, trades)
        failures = book_folder(self.root, BOOK2_HYBRID) / VALIDITY_FAILURES_FILE
        return DecidedRun(run, (log, *([failures] if failures.is_file() else [])))

    def _judge_reason(self, accepted: AcceptedDecision) -> str:
        """ "no trade, judge failed" or "no trade, judge unavailable", from the verdict file F1t's judge step wrote."""
        try:
            status = json.loads((self.root / accepted.judge).read_text(encoding="utf-8")).get("status")
        except (OSError, ValueError, AttributeError):
            status = None
        return JUDGE_UNAVAILABLE if status == "unavailable" else JUDGE_FAILED

    def _context(self, context: Mapping, accepted: AcceptedDecision, status: str, tradable) -> dict:
        """The inputs' own context, the fired packs, the model F1t checked, the session, the judge's verdict file, and
        Book 2's served components: the envelope files of every version it could trade, as they are now (D4: D6
        unscores a decision made on any other envelope), its prompt, the decision version and the traded strategies'
        status (F1t criteria 7, 16, 17b)."""
        envelopes = served_envelopes(self.envelopes(), [s.key for s in tradable])
        served = {**envelopes, **self.served(accepted.day), SERVED_VERSION: accepted.version, "strategy_status": status}
        return {**context, "common_pack_sha256": accepted.common_pack.sha256,
                "private_pack_sha256": accepted.private_pack.sha256, "model_served": accepted.model_reported,
                "session_id": accepted.session, "judge": accepted.judge or None, "served": served}  # fmt: skip


def _require_same_sheet(seen: Mapping, now: Mapping) -> None:
    for part in SHEET_PARTS:
        if json.loads(json.dumps(seen.get(part))) != json.loads(json.dumps(now[part])):
            raise DecisionRefused(SHEET_DIFFERS.format(part=part))


def _require_one_pick_each(taken: Sequence[SlotResult]) -> None:
    """After the envelope (a shadow-only slot takes its default), two picks of one opportunity would leave C4 one rule
    default for two slots: the day is refused, never decided on whichever pick came first."""
    ids = [s.pick.opportunity_id for s in taken]
    twice = sorted({i for i in ids if ids.count(i) > 1})
    if twice:
        raise DecisionRefused(SAME_PICK.format(ids=", ".join(twice)))


def _rule_actions(rule: DayEvaluation) -> dict[str, str]:
    """The rule's own action per opportunity and for the day, for every record's `rule_default` (D4 criterion 7)."""
    actions = {o.opportunity.opportunity_id: "trade" if o.decision == Decision.CHOSEN else "no trade"
               for o in rule.outcomes}  # fmt: skip
    return {**actions, NO_TRADE_ID: "trade" if "trade" in actions.values() else "no trade"}


def _authority(slots: Sequence[SlotResult], blocked: bool) -> str:
    """The envelope's verdict on each slot, the run's `authority_check` (D4: the verdict, never empty)."""
    if blocked:
        return JUDGE_BLOCKED
    return "; ".join(f"{s.default.opportunity_id} {s.action}: {s.status} ({s.why})" for s in slots) or NO_DEFAULT


def _status(sheet: Mapping, taken: Sequence[SlotResult]) -> str:
    """`research` when any picked version is still research (the run's label is then "strategy not yet passed")."""
    status = {o["opportunity_id"]: o["strategy_status"] for o in sheet["opportunities"]}
    picked = {status.get(s.pick.opportunity_id) for s in taken}
    return PlaybookStatus.RESEARCH if PlaybookStatus.RESEARCH in picked else PlaybookStatus.PAPER


def _require_labelled(run: Path) -> None:
    for path in sorted(Path(run).glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        chosen = (record.get("decision") or {}).get("outcome") == Decision.CHOSEN
        if chosen and not (record.get("served") or {}).get("strategy_status"):
            raise DecisionRefused(NO_STATUS)
