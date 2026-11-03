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

import json
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path

from ..ai_trading.fired_packs import require_fired_packs
from ..ai_trading.ports import SERVED_VERSION, AcceptedDecision, AiBookDecider, DecidedRun, DecisionRefused
from ..books.book1 import Book1Inputs
from ..books.paths import book_folder
from ..constants import BOOK3_AI, VALIDITY_FAILURES_FILE, PlaybookStatus
from ..playbook.decision_run import DecisionRun
from ..playbook.evaluate import RuleEvaluator
from ..playbook.selection import Pick
from ..research_engine.ledger import LEDGER_FILE
from .answer import check_decision
from .day_log import log_path, write_day_log
from .evaluation import Book3Evaluators, day_sheet
from .proposals import REGISTERED, Book3Proposer
from .registry import REGISTRY_FILE, spec_path
from .shadow_file import Widths, shadow_body, shadow_path, write_shadow
from .strategies import Book3Strategies

NO_SHEET = "the private pack holds no day sheet (`evaluation`): Book 3 saw no candidates"
SHEET_DIFFERS = "the day sheet does not reproduce now (pack {seen}, now {now}): nothing decided"
UNKNOWN_CARDS = "cards_used names cards the session was not given: {cards}"
NO_ROLE_SET = "none"
ROLE_SET = "role_set_version"  # F2's item, as F1t fires it: {"role_set_version", "roles": [{"card_id", "card"}]}
STRATEGY_STATUS = PlaybookStatus.RESEARCH  # every Book 3 spec is research (D5): each trade "strategy not yet passed"
LEDGER_REWRITTEN = f"{LEDGER_FILE} changed above its new rows: the trial ledger is append-only, nothing decided"


RunFactory = Callable[[RuleEvaluator, Sequence[Mapping]], DecisionRun]  # (evaluator, stored picks) -> D3's run


class Book3Decider(AiBookDecider):
    def __init__(self, root: Path, inputs: Book1Inputs, strategies: Book3Strategies, evaluators: Book3Evaluators,
                 proposer: Book3Proposer, runs: RunFactory, head: Callable[[], str],
                 served: Callable[[date], Mapping[str, str]],
                 widths: Widths, prompt_version: str):  # fmt: skip
        """`served(day)`: Book 3's own D6 components (`constitution`, `book3_prompt`) in every record's `served`."""
        self.root, self.inputs, self.strategies, self.evaluators = Path(root), inputs, strategies, evaluators
        self.proposer, self.runs, self.head, self.served = proposer, runs, head, served
        self.widths, self.prompt_version = widths, prompt_version

    def decide(self, accepted: AcceptedDecision) -> DecidedRun:
        decision, day = accepted.decision, accepted.day
        problems = check_decision(decision)
        if problems:
            raise DecisionRefused("; ".join(problems))
        card_ids, role_set = _cards(accepted.analyst_cards)
        unknown = sorted(set(decision["cards_used"]) - card_ids)
        if unknown:
            raise DecisionRefused(UNKNOWN_CARDS.format(cards=", ".join(unknown)))
        self._require_new_day(day)
        tradable = self.strategies.on(day, self.head())
        today = self.inputs.day(day)
        require_fired_packs(today.context, accepted)
        arguments = (day, tradable.snapshot.playbook(), today.market, today.features, today.book, today.counts,
                     today.shadow)  # fmt: skip
        self._require_sheet(accepted, arguments, tradable.snapshot.commit)
        picks = [Pick(t["opportunity_id"], t["reason"]) for t in decision["trades"]]
        evaluator, selection = self.evaluators.with_picks(picks)
        run = self.runs(evaluator, [p.to_json() for p in picks]).decide(
            day, tradable.snapshot, today.market, today.features, today.book, today.counts, today.shadow,
            self._context(today.context, accepted),
        )  # fmt: skip
        ledger = _bytes(self.root / LEDGER_FILE)
        entries = self.proposer.register_all(day, decision["proposals"], accepted.registered_model,
                                             self.prompt_version, role_set)  # fmt: skip
        if not _bytes(self.root / LEDGER_FILE).startswith(ledger):  # judge 652: rows 101-108 are frozen (O12e)
            raise DecisionRefused(LEDGER_REWRITTEN)
        log = write_day_log(self.root, day, decision["reason"], entries, selection.attempted, tradable.excluded)
        body = shadow_body(day, accepted.common_pack.sha256, accepted.common_pack.body["opportunities"],
                           decision["shadow"], self.widths)  # fmt: skip
        return DecidedRun(run, (log, write_shadow(self.root, body), *self._registered_files(entries)))

    def _require_new_day(self, day: date) -> None:
        """One decision a day: a day log or shadow file already written refuses the day before anything is written."""
        for path in (log_path(day), shadow_path(day)):
            if (self.root / path).exists():
                raise DecisionRefused(f"{path} is already written: Book 3 decides once a day")

    def _registered_files(self, entries: Sequence[Mapping]) -> list[Path]:
        """Every other file the day wrote, for F1t's commit: the registry, each new spec and the trial ledger when a
        proposal registered, and C4's failure log when a pick was blocked."""
        registered = [e["strategy_id"] for e in entries if e["status"] == REGISTERED]
        paths = [REGISTRY_FILE, LEDGER_FILE, *(spec_path(i) for i in registered)] if registered else []
        failures = book_folder(self.root, BOOK3_AI) / VALIDITY_FAILURES_FILE
        return [self.root / p for p in paths] + ([failures] if failures.is_file() else [])

    def _require_sheet(self, accepted: AcceptedDecision, arguments: tuple, commit: str) -> None:
        """The sheet the session saw must be exactly what D2 gives again now: every opportunity, rule result and built
        trade (legs, width, lots, maximum loss). Its commit may be older (F1t commits between the pack and now)."""
        seen = accepted.private_pack.body.get("evaluation")
        if seen is None:
            raise DecisionRefused(NO_SHEET)
        evaluator, _ = self.evaluators.with_picks(())
        now = day_sheet(arguments[0], evaluator.evaluate(*arguments), commit, {})
        if json.loads(json.dumps(seen.get("opportunities"))) != json.loads(json.dumps(now["opportunities"])):
            raise DecisionRefused(SHEET_DIFFERS.format(seen=_ids(seen), now=_ids(now)))

    def _context(self, context: Mapping, accepted: AcceptedDecision) -> dict:
        """The run's context: the inputs' own (code, config, D6 version), the packs the session was fired with, the
        model F1t checked, the session link, the judge's verdict file (D3 `judge`; Book 3's verdict never blocks) and
        Book 3's served components with the decision version and the strategies' status (F1t criteria 7, 16, 17b)."""
        served = {**self.served(accepted.day), SERVED_VERSION: accepted.version, "strategy_status": STRATEGY_STATUS}
        return {**context, "common_pack_sha256": accepted.common_pack.sha256,
                "private_pack_sha256": accepted.private_pack.sha256, "model_served": accepted.model_reported,
                "session_id": accepted.session, "judge": accepted.judge or None, "served": served}  # fmt: skip


def _bytes(path: Path) -> bytes:
    return path.read_bytes() if path.is_file() else b""


def _ids(sheet: Mapping) -> list[str]:
    return sorted(o["opportunity_id"] for o in sheet.get("opportunities") or ())


def _cards(item: Mapping | None) -> tuple[set[str], str]:
    """(the card IDs given, the role set) from F2's item as F1t fired it: a card counts only when it was passed (a
    usable status); no item, or one with no role set yet (F2 not built), means no card and the role set "none". An
    item without a `roles` list is refused, never read as "no cards"."""
    if item is None:
        return set(), NO_ROLE_SET
    roles = item.get("roles")
    if not isinstance(roles, list):
        raise DecisionRefused("analyst_cards must carry a roles list (F2's item)")
    ids = {r.get("card_id") for r in roles if isinstance(r, Mapping) and r.get("card") is not None and r.get("card_id")}
    return ids, item.get(ROLE_SET) or NO_ROLE_SET
