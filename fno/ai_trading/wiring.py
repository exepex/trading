"""Composition root of the AI books' trading runner, daily-run side (story F1t): the only place that picks the concrete
routine triggers, packs, budget signal, record scan, cards source and each book's parts. Each AI book's parts (its
decider, orders and exit rules) are its story's: F5 (Book 2) and F6 (Book 3) add one line each to `BOOK_PARTS`. The
routine side has its own root (`book_wiring.py`, standard library only)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..alerts.sender import AlertSender
from ..constants import (
    BOOK2_HYBRID,
    BOOK3_AI,
    ENV_ROUTINE_BOOK2_DECISION_TOKEN,
    ENV_ROUTINE_BOOK2_DECISION_TRIGGER_ID,
    ENV_ROUTINE_BOOK3_DECISION_TOKEN,
    ENV_ROUTINE_BOOK3_DECISION_TRIGGER_ID,
)
from ..desk.daily_ports import ExitRules, OrderBuilder, Waiter
from ..pipeline.trigger import RoutineFireTrigger, RoutineTrigger, UnconfiguredTrigger
from .ports import AiBookDecider, AnalystCards, DayPacks, NoAnalystCards
from .versions import REGISTRY

ROUTINES = {
    BOOK2_HYBRID: (ENV_ROUTINE_BOOK2_DECISION_TRIGGER_ID, ENV_ROUTINE_BOOK2_DECISION_TOKEN),
    BOOK3_AI: (ENV_ROUTINE_BOOK3_DECISION_TRIGGER_ID, ENV_ROUTINE_BOOK3_DECISION_TOKEN),
}  # book -> its decision routine's two settings in the daily routine's environment


@dataclass(frozen=True)
class BookParts:
    decider: AiBookDecider
    orders: OrderBuilder
    exits: ExitRules


PartsBuilder = Callable[[dict, Path, AlertSender], BookParts]
BOOK_PARTS: dict[str, PartsBuilder] = {}  # F5 and F6 add their book's builder here


def build_decision_trigger(book: str, env=os.environ) -> RoutineTrigger:
    names = ROUTINES[book]
    trigger_id, token = (env.get(name) for name in names)
    if not (trigger_id and token):
        return UnconfiguredTrigger(book, tuple(n for n in names if not env.get(n)))
    return RoutineFireTrigger(book, trigger_id, token)


def build_book_parts(cfg: dict, root: Path, alerts: AlertSender, books) -> dict[str, BookParts]:
    return {book: BOOK_PARTS[book](cfg, root, alerts) for book in books if book in BOOK_PARTS}


def build_day_packs(root: Path) -> DayPacks:
    from ..desk.common_pack import CommonPack
    from ..desk.pack_store import PackStore
    from ..desk.private_pack import PrivatePack

    store = PackStore(root)

    def private(book: str, day: date) -> PrivatePack:
        return PrivatePack(book, day, json.loads(store.private_path(book, day).read_text(encoding="utf-8")))

    return DayPacks(lambda day: CommonPack.read(day, store.common_path(day)), private)


def build_ai_steps(
    cfg: dict,
    root: Path,
    live,
    parts: dict[str, BookParts],
    processes,
    waiter: Waiter,
    git,
    clock: Callable[[], datetime],
    cards: AnalystCards | None = None,
    env=os.environ,
) -> dict:
    """O1's two steps, unwrapped (the daily run's wiring wraps each in `Alerted` with the run's one sender)."""
    from ..ai.history import RepoHistory
    from ..composition import build_record_scanner
    from ..constants import AI_COLLECT_STEP, AI_FIRE_STEP
    from ..desk.git_sync import GitCommitter
    from ..desk.timetable import timetable_from_config
    from ..learning.writer import SignalFile
    from .collect import DecisionCollector
    from .fire import DecisionFirer
    from .promote import Promoter
    from .steps import AiCollectStep, AiFireStep
    from .timing import decision_timing_from_config

    timing = decision_timing_from_config(cfg, timetable_from_config(cfg))
    packs, cards = build_day_packs(root), cards or NoAnalystCards()
    triggers = {book: build_decision_trigger(book, env) for book in ROUTINES}
    firer = DecisionFirer(root, REGISTRY, triggers, SignalFile(root), packs, cards, build_record_scanner(),
                          GitCommitter(git).commit, clock)  # fmt: skip
    deciders = {book: book_parts.decider for book, book_parts in parts.items()}
    pull = lambda: git("pull", "-q", "--no-rebase", "--no-edit", "origin", git.branch())  # noqa: E731
    collector = DecisionCollector(root, RepoHistory(root), REGISTRY, Promoter(root, deciders), packs, cards, pull)
    return {
        AI_FIRE_STEP: AiFireStep(root, firer, timing, live, processes),
        AI_COLLECT_STEP: AiCollectStep(root, collector, timing, live, waiter, clock),
    }
