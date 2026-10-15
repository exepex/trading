"""Experiment 1 stays reproducible from its frozen worktree while the panel on `main` grows (owner, 14 Oct 2026; G1 v3,
ChatGPT review 30 item 6, response 69). The 45 files FREEZE.md lists have their frozen bytes at the run commit, the
published result has its recorded SHA-256, and README.md gives the exact reproduction. Runs need full history."""

import hashlib
import re
import subprocess

import pytest

from fno.config import ROOT

EXPERIMENT = ROOT / "research" / "2026-10-12-experiment-1"
RUN_COMMIT = "0c1c957eb49cfa3c2ea3efb6b93befa66d6b6928"  # the frozen worktree the challenge ran from (RESULTS.md)
RESULT_SHA256 = "4826897ed4d7e4edf738ec49b926111eb924e3c47cf471fb0aaa73d4e6aff9b6"
HASH_LINE = re.compile(r"^([0-9a-f]{64})  (\S+)$", re.MULTILINE)


def _at(commit: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, check=True).stdout


@pytest.mark.usefixtures("full_history")
def test_every_frozen_file_has_its_frozen_bytes_at_the_run_commit():
    frozen = HASH_LINE.findall((EXPERIMENT / "FREEZE.md").read_text(encoding="utf-8"))
    assert len(frozen) == 45
    changed = [path for sha, path in frozen if hashlib.sha256(_at(RUN_COMMIT, path)).hexdigest() != sha]
    assert changed == []


def test_the_published_result_is_the_frozen_run_and_the_reproduction_is_written_down():
    result = EXPERIMENT / "results_challenge.json"
    assert hashlib.sha256(result.read_bytes()).hexdigest() == RESULT_SHA256
    readme = (EXPERIMENT / "README.md").read_text(encoding="utf-8")
    assert f"git worktree add ../experiment-1-frozen {RUN_COMMIT}" in readme
    assert "python -m fno research run 2026-10-12-experiment-1 --period challenge" in readme
    assert RESULT_SHA256 in readme
