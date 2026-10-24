"""`last_commit` in the frozen fno/forecast_scoring/wiring.py (FREEZE_v3.md) reads a failed `git log` as "" (a known
silent read, left as it is under the v3 freeze; orchestrator, 22 Oct 2026). Its one caller, `score_forecasts`, passes
that "" straight to `require_frozen_before`: the score is refused by name (NotFrozen), never accepted. Tested
through the real functions on the repository's own freeze, without editing the frozen file."""

import subprocess

import pytest

from fno.config import ROOT
from fno.forecast.freeze import NotFrozen, require_frozen_before
from fno.forecast_scoring.wiring import BACKFILL_FILE, last_commit
from fno.research_engine.ledger import Git

REAL = subprocess.run


def test_the_real_backfill_commit_is_scored_under_the_freeze():
    commit = last_commit(ROOT, BACKFILL_FILE)
    assert commit and require_frozen_before(ROOT, commit, Git(ROOT)).protocol_commit


def test_a_failed_git_log_in_last_commit_refuses_the_score(monkeypatch):
    def run(args, *a, **k):
        if args[:3] == ["git", "log", "-1"] and BACKFILL_FILE in args:
            return subprocess.CompletedProcess(args, 128, "", "fatal: unable to read tree (simulated)")
        return REAL(args, *a, **k)

    monkeypatch.setattr(subprocess, "run", run)
    commit = last_commit(ROOT, BACKFILL_FILE)
    assert commit == ""  # the frozen file's silent read, unchanged
    with pytest.raises(NotFrozen, match="the freeze is not in the history of"):  # score_forecasts' next step: refused
        require_frozen_before(ROOT, commit, Git(ROOT))
