"""One AI decision day in a test repository (story F1t): the real firer, the real routine side and the real collector,
with a trigger that only keeps the pointer, a fake decider, and the remote observer's readings taken by the test at
the moments it chooses (the repository's `HEAD` stands for the remote)."""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

from fno.ai.history import RepoHistory
from fno.ai.observed_receipts import Observation, ObservationFile
from fno.ai_trading.collect import DecisionCollector
from fno.ai_trading.fire import DecisionFirer, FireTiming
from fno.ai_trading.outcome import Deadlines
from fno.ai_trading.paths import WORK_FOLDER, observations_path
from fno.ai_trading.ports import DayPacks
from fno.ai_trading.promote import Promoter
from fno.composition import build_record_scanner
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.desk.private_pack import PrivatePack
from fno.pipeline.trigger import RoutineTrigger
from tests.ai.fakes import Clock, git

from .builders import CARDS, DAY, FakeDecider, at, common_pack, make_repo, private_body, registry
from .fakes import DecisionRoutine

BOOKS = (BOOK2_HYBRID, BOOK3_AI)
DEADLINES = Deadlines(at(15, 10), at(15, 11))
TIMING = FireTiming(at(15, 7), at(15, 10), at(15, 10, 10))


class KeepPointer(RoutineTrigger):
    def __init__(self):
        self.texts = []

    def fire(self, pointer):
        self.texts.append(pointer.to_text())
        return f"https://example.invalid/{pointer.book}"


class NoStop:
    def ai_roles_stopped(self, day):
        return False


class SameCards:
    def __init__(self, item=CARDS):
        self.value = item

    def item(self, day, units):
        return self.value


class Day:
    def __init__(self, tmp_path: Path, deciders=None, cards=None):
        self.root = make_repo(tmp_path / "repo")
        self.registry, self.clock = registry(self.root), Clock(at(15, 0))
        self.triggers = {book: KeepPointer() for book in BOOKS}
        self.packs = DayPacks(lambda day: common_pack(day), lambda b, d: PrivatePack(b, d, private_body(b, d)))
        self.cards = cards or SameCards()
        self.deciders = deciders if deciders is not None else {b: FakeDecider(self.root) for b in BOOKS}
        self.routines = {b: DecisionRoutine(self.root, self.registry, self.clock) for b in BOOKS}

    def fire(self, books=BOOKS) -> dict:
        firer = DecisionFirer(self.root, self.registry, self.triggers, NoStop(), self.packs, self.cards,
                              build_record_scanner(), self._commit, self.clock)  # fmt: skip
        return firer.fire(DAY, books, TIMING)

    def seal(self, book, draft, when=(15, 8)):
        with self._own_folder(book):
            session = self.routines[book].session()
            session.brief(self.triggers[book].texts[-1])
            self.clock.now = at(*when)
            answer = self.root / WORK_FOLDER / "answer.json"
            answer.write_text(json.dumps(draft), encoding="utf-8")
            session.seal(answer)

    def reveal(self, book):
        with self._own_folder(book):
            self.routines[book].session().reveal()

    @contextmanager
    def _own_folder(self, book):
        """Each real routine has its own checkout: here each book's working folder is kept apart between steps."""
        work, kept = self.root / WORK_FOLDER, self.root / f".{book}_work"
        if kept.exists():
            kept.rename(work)
        try:
            yield
        finally:
            if work.exists():
                work.rename(kept)

    def observe(self, deadline, late=0.4, commit="HEAD"):
        head = git(self.root, "rev-parse", commit).strip() if commit else None
        started = deadline + timedelta(seconds=late)
        reading = Observation(deadline, started, started + timedelta(seconds=1), head, "" if head else "failed")
        ObservationFile(self.root / observations_path(DAY)).append(reading)

    def collect(self, books=BOOKS):
        promoter = Promoter(self.root, self.deciders)
        collector = DecisionCollector(self.root, RepoHistory(self.root), self.registry, promoter, self.packs,
                                      self.cards, lambda: None)  # fmt: skip
        return collector.collect(DAY, books, DEADLINES)

    def _commit(self, paths, message):
        git(self.root, "add", *[str(p) for p in paths])
        git(self.root, "commit", "-q", "-m", message)
