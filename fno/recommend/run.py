"""One day's recommendation (story REC1b): gather, decide, check that the rung rule in force is the pinned one, save
write-once with its receipt pushed, and only then post the line. Any failed input is alerted by name beside the line;
a record that could not be saved or pushed is never posted: one problem line goes out instead."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..alerts.sender import AlertSender
from .decide import decide
from .gather import Header, Ports, gather
from .post import recommendation_line
from .rungs import RUNG_RULE_PATH, RUNG_RULE_SHA256
from .store import DriveRecommendations, NotSaved

RULE_CHANGED = "recommendation NOT made for {day}: {path} is not the pinned rung rule (a new version needs a new pin)"
NOT_SAVED = "recommendation NOT posted for {day}: {why}"
INPUT_PROBLEM = "recommendation for {day}, input problem: {line}"


@dataclass(frozen=True)
class DayResult:
    lines: tuple[str, ...]  # what the command prints
    ok: bool  # False: the step fails, so the run's last line names it


class RecommendRun:
    def __init__(self, root: Path, ports: Ports, store: DriveRecommendations, alerts: AlertSender,
                 header: Callable[[], Header], clock: Callable[[], datetime]):  # fmt: skip
        self.root, self.ports, self.store, self.alerts = root, ports, store, alerts
        self.header, self.clock = header, clock

    def run(self, day: date) -> DayResult:
        if hashlib.sha256((self.root / RUNG_RULE_PATH).read_bytes()).hexdigest() != RUNG_RULE_SHA256:
            return self._fail(RULE_CHANGED.format(day=day, path=RUNG_RULE_PATH))
        gathered = gather(day, self.clock(), self.header(), self.ports)
        record = decide(gathered.facts)
        try:
            saved = self.store.save(record)
        except NotSaved as failed:
            return self._fail(NOT_SAVED.format(day=day, why=failed))
        line = recommendation_line(record, saved)
        problems = [INPUT_PROBLEM.format(day=day, line=p) for p in gathered.problems]
        sent = [self.alerts.send(text) for text in (line, *problems)]
        return DayResult((line, *problems, *sent), ok=not problems)

    def _fail(self, line: str) -> DayResult:
        return DayResult((line, self.alerts.send(line)), ok=False)
