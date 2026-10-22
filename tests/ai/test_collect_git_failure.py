"""A failed git read during the AI collection writes nothing (orchestrator, 22 Oct 2026): it raises, so the books'
records and audit files are not written and the next collection can run, never a real answer recorded as a miss."""

import subprocess

import pytest

from fno.ai.paths import audit_path, records_path, reveal_path
from fno.constants import AI_BOOKS, BOOK2_HYBRID, BOOK3_AI
from fno.research_engine.ledger import GitFailed
from tests.ai.fakes import DAY
from tests.ai.test_fire_and_collect import Desk

REAL = subprocess.run


def test_a_failed_git_read_raises_and_leaves_no_record_or_audit(tmp_path, monkeypatch):
    desk = Desk(tmp_path)
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.answer(BOOK2_HYBRID)
    target, broken = reveal_path(DAY, BOOK2_HYBRID), [True]

    def run(args, *a, **k):
        if broken[0] and args[:2] == ["git", "log"] and target in args:
            return subprocess.CompletedProcess(args, 128, "", "fatal: unable to read tree (simulated)")
        return REAL(args, *a, **k)

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(GitFailed, match="git log failed"):
        desk.collect()
    assert not any(
        (desk.root / p).exists() for book in AI_BOOKS for p in (audit_path(DAY, book), records_path(DAY, book))
    )
    monkeypatch.undo()
    desk.collect()  # the next collection, with git working again, records the real reveal
    assert desk.audit(BOOK2_HYBRID)["status"] == "on_time"
