"""The daily run's steps (story E3): each reads what earlier steps committed (the pack file, the decisions, the
capture records, the accounts), never memory, so a restarted run continues where it stopped. Each returns its inputs,
its result and the files to commit."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from ..checks.gate import DataGate
from ..constants import NO_DECISION_LATE
from .common_pack import CommonPack
from .daily_ports import (
    AccountSync,
    CommittedDecision,
    DecisionSource,
    ExecutionCapture,
    ExitRules,
    Packs,
    ValidityGate,
    VersionKeeper,
)
from .entries import EntryDesk
from .exits import ExitDesk
from .no_decision import write_no_decision
from .pack_items import PackError
from .timetable import Timetable

NOT_COMMITTED = "nothing visible at the deadline {deadline} (origin {origin})"
COLLECTED_LATE = "collected at {started}, after the deadline {deadline}: no decision can be shown to be on time"
COLLECTION_GRACE = timedelta(seconds=30)  # the step starts at the deadline; later means a restart: fail closed
NO_SNAPSHOT = "no new risk: no valid execution snapshot after the common retry"
LATE_AT_SNAPSHOT = "late: committed {committed}, not before the execution snapshot started {started}"
NOT_VALIDATED = "not filled: no completed C4 pass ({problems})"


@dataclass(frozen=True)
class StepOutcome:
    inputs: dict
    result: dict
    paths: tuple[Path, ...] = field(default_factory=tuple)


def no_pack(day: date) -> CommonPack:
    """Stands in when no pack could be built: no spot, no snapshot record, so no new trade; exits still run."""
    return CommonPack(day, {"day": day.isoformat(), "kind": "no_pack", "provenance": {}, "items": []})


@dataclass
class DeskSteps:
    root: Path
    books: Sequence[str]
    timetable: Timetable
    versions: VersionKeeper
    packs: Packs
    decisions: DecisionSource
    capture: ExecutionCapture
    gate: DataGate
    validity: ValidityGate
    sync: AccountSync
    entry_desk: EntryDesk
    exit_desk: ExitDesk
    exit_rules: ExitRules
    clock: Callable[[], datetime]

    def keep_versions(self, day: date) -> StepOutcome:
        return StepOutcome({}, {"line": self.versions.keep(day)})

    def build_pack(self, day: date) -> StepOutcome:
        try:
            pack = self.packs.build(day)
        except PackError as refused:
            return StepOutcome({}, {"built": False, "reason": str(refused)})
        return StepOutcome({}, {"built": True, "sha256": pack.sha256}, self.packs.files(day))

    def collect_decisions(self, day: date) -> StepOutcome:
        """What the collector observes at the deadline decides who is on time (judge 82): it pulls once and records,
        per book, the run ID and its holding commit, with the origin commit seen. Started after the deadline (a
        restart), it fails closed: every book is late."""
        deadline, started = self.timetable.at(day, self.timetable.decision_deadline), self.clock()
        if started > deadline + COLLECTION_GRACE:
            why = COLLECTED_LATE.format(started=started.isoformat(), deadline=deadline.isoformat())
            return self._all_late(day, deadline, why, {"deadline": deadline.isoformat(), "origin": None})
        origin, result, paths = self.decisions.observe(), {}, []
        for book in self.books:
            decision = self.decisions.committed(book, day, deadline)
            if decision is None:
                why = NOT_COMMITTED.format(deadline=deadline.isoformat(), origin=origin)
                paths.append(write_no_decision(self.root, book, day, deadline, why))
                result[book] = {"decision": NO_DECISION_LATE, "reason": why}
            else:
                result[book] = {"run_id": decision.run_id, "commit": decision.commit,
                                "committed_at": decision.committed_at.isoformat(),
                                "orders": [o.proposal.trade_id for o in decision.orders]}  # fmt: skip
        return StepOutcome({"deadline": deadline.isoformat(), "origin": origin}, result, tuple(paths))

    def _all_late(self, day: date, deadline: datetime, why: str, inputs: dict) -> StepOutcome:
        paths = tuple(write_no_decision(self.root, book, day, deadline, why) for book in self.books)
        return StepOutcome(inputs, {book: {"decision": NO_DECISION_LATE, "reason": why} for book in self.books}, paths)

    def take_snapshot(self, day: date) -> StepOutcome:
        """One capture for every book; if it is not valid, one common retry for all of them together."""
        attempts = []
        for _ in range(2):
            record = self.capture.capture(day)
            attempts.append(record.snapshot_id if record else None)
            snapshot, report = self.gate.check(self.pack(day))
            if record and snapshot and snapshot.complete and not report.prices_unverified:
                return StepOutcome({}, {"valid": True, "snapshot_id": snapshot.snapshot_id,
                                        "sha256": snapshot.sha256, "attempts": attempts})  # fmt: skip
        return StepOutcome({}, {"valid": False, "attempts": attempts, "reason": NO_SNAPSHOT})

    def pack(self, day: date) -> CommonPack:
        return self.packs.stored(day) or no_pack(day)

    def fill(self, day: date, snapshot_valid: bool, collected: dict) -> StepOutcome:
        """Only the runs the decisions step recorded are filled; a book recorded late never fills (judge 82)."""
        pack, result = self.pack(day), {}
        for book in self.books:
            entry = collected.get(book, {})
            if "run_id" not in entry:
                continue
            decision = self.decisions.recorded(book, day, entry["run_id"], entry["commit"])
            for order in decision.orders:
                result[order.proposal.trade_id] = self._fill_one(pack, decision, order, snapshot_valid)
        return StepOutcome({"snapshot_valid": snapshot_valid, "decisions": collected}, result)

    def _fill_one(self, pack: CommonPack, decision: CommittedDecision, order, snapshot_valid: bool) -> dict:
        if not snapshot_valid:
            return {"outcome": "not filled", "reason": NO_SNAPSHOT}
        problems = self.validity.problems(decision, order)
        if problems:
            return {"outcome": "not filled", "reason": NOT_VALIDATED.format(problems="; ".join(problems))}
        snapshot, report = self.gate.check(pack, order.contracts())
        if snapshot is None:
            return {"outcome": "not filled", "reason": report.reason()}
        if decision.committed_at >= snapshot.started_at:
            late = LATE_AT_SNAPSHOT.format(committed=decision.committed_at, started=snapshot.started_at)
            return {"outcome": "not filled", "reason": late}
        message = f"desk fills {order.book} {order.proposal.trade_id}"
        entered = self.sync.write(order.book, lambda j: self.entry_desk.enter(order, snapshot, j, report), message)
        return {"outcome": entered.outcome, "reason": entered.reason, "snapshot_id": snapshot.snapshot_id,
                "sha256": snapshot.sha256}  # fmt: skip

    def review_exits(self, day: date) -> StepOutcome:
        """Risk-reducing exits run whatever happened to the decisions or the snapshot (design 9)."""
        pack = self.pack(day)
        return StepOutcome({}, {book: self._review_book(pack, book, day) for book in self.books})

    def _review_book(self, pack: CommonPack, book: str, day: date) -> dict:
        rules = self.exit_rules.rules(book)
        snapshot, report = self.gate.check(pack)
        if snapshot is None:  # no desk event without a snapshot: the gate's alert names the exits held up
            due = self.sync.write(book, lambda j: self.exit_desk.due_exits(j, day, rules), f"exit check {book}")
            self.gate.check(pack, due_exits=due)
            return {"reviewed": False, "waiting": due, "reason": report.reason()}
        message = f"desk exits {book}"
        reviewed = self.sync.write(book, lambda j: self.exit_desk.review(book, snapshot, j, rules, report), message)
        return {"reviewed": True, "results": [{"trade_id": r.trade_id, "outcome": r.outcome, "reason": r.reason}
                                              for r in reviewed]}  # fmt: skip
