"""A fake AI book decision routine for story F1t's tests: it runs the real routine side (brief, seal, reveal) over a
transport that commits in the test repository, at times the test sets."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fno.ai.run_timing import RunTiming
from fno.ai.sealed_publish import SealedPublisher
from fno.ai_trading.book_wiring import DECISION_RUN
from fno.ai_trading.paths import WORK_FOLDER
from fno.ai_trading.session import DecisionSession
from fno.ai_trading.versions import DecisionRegistry
from tests.ai.fakes import Clock, LocalCommitTransport


class DecisionRoutine:
    def __init__(self, root: Path, registry: DecisionRegistry, clock: Clock, transport=None,
                 session_id: str = "session_test"):  # fmt: skip
        self.root, self.registry, self.clock, self.session_id = Path(root), registry, clock, session_id
        self.transport = transport or LocalCommitTransport(self.root)
        self.printed: list[str] = []

    def session(self) -> DecisionSession:
        publisher = SealedPublisher(self.transport, self.clock, self.clock.sleep)
        timing = RunTiming(self.root, self.transport, self.clock, self.session_id, DECISION_RUN)
        return DecisionSession(self.root, self.registry, publisher, timing, self.printed.append)

    def run(self, text: str, draft: dict, sealed_at: datetime, reveal: bool = True) -> None:
        session = self.session()
        session.brief(text)
        self.clock.now = sealed_at
        answer_file = self.root / WORK_FOLDER / "answer.json"
        answer_file.write_text(json.dumps(draft), encoding="utf-8")
        session.seal(answer_file)
        if reveal:
            session.reveal()
