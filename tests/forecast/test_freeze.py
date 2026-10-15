"""Story G1 criterion 3: the forecast protocol is frozen, and the freeze check G4 runs before scoring refuses anything
scored before the freeze or after a frozen file changed."""

import subprocess
from pathlib import Path

import pytest

from fno.config import ROOT
from fno.forecast.freeze import FREEZE_FILE, PROTOCOL_FILE, NotFrozen, file_sha256, require_frozen_before
from fno.research_engine.ledger import Git


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _freeze_text(commit: str, hashes: dict[str, str]) -> str:
    rows = "".join(f"| `{path}` | `{sha}` |\n" for path, sha in hashes.items())
    return f"# Freeze\n\nProtocol commit: `{commit}`\n\n| File | SHA-256 |\n|---|---|\n{rows}"


@pytest.fixture
def repo(tmp_path):
    """A repository with a protocol commit, then a scored-forecast-free freeze commit."""
    _git(tmp_path, "init", "-q")
    protocol = tmp_path / PROTOCOL_FILE
    protocol.parent.mkdir(parents=True)
    protocol.write_text("# Protocol v1\n")
    (tmp_path / "code.py").write_text("X = 1\n")
    before = _commit(tmp_path, "protocol")
    hashes = {PROTOCOL_FILE: file_sha256(protocol), "code.py": file_sha256(tmp_path / "code.py")}
    (tmp_path / FREEZE_FILE).write_text(_freeze_text(before, hashes))
    after = _commit(tmp_path, "freeze")
    return tmp_path, before, after


def test_a_commit_after_the_freeze_passes(repo):
    root, _, after = repo
    (root / "scores.json").write_text("{}")
    scored = _commit(root, "first scored forecast")
    assert require_frozen_before(root, scored, Git(root)).hashes[PROTOCOL_FILE]
    assert require_frozen_before(root, after, Git(root))


def test_a_commit_before_the_freeze_record_is_refused(repo):
    root, before, _ = repo
    with pytest.raises(NotFrozen, match="not in the history"):
        require_frozen_before(root, before, Git(root))


def test_a_frozen_file_changed_after_the_freeze_is_refused(repo):
    root, _, _ = repo
    (root / "code.py").write_text("X = 2\n")
    scored = _commit(root, "edited after the freeze")
    with pytest.raises(NotFrozen, match="code.py"):
        require_frozen_before(root, scored, Git(root))


def test_a_freeze_naming_a_different_protocol_version_is_refused(repo):
    root, before, _ = repo
    freeze = root / FREEZE_FILE
    freeze.write_text(_freeze_text(before, {PROTOCOL_FILE: "0" * 64}))
    scored = _commit(root, "bad freeze")
    with pytest.raises(NotFrozen):
        require_frozen_before(root, scored, Git(root))


def test_no_freeze_file_means_not_frozen(tmp_path):
    _git(tmp_path, "init", "-q")
    (tmp_path / "a").write_text("a")
    head = _commit(tmp_path, "a")
    with pytest.raises(NotFrozen, match="does not exist"):
        require_frozen_before(tmp_path, head, Git(tmp_path))


@pytest.mark.usefixtures("full_history")
def test_the_repository_protocol_is_frozen_before_this_commit_and_unchanged():
    """Every later commit must keep this passing: a change to a frozen file needs a new protocol version."""
    head = Git(ROOT).head()
    freeze = require_frozen_before(ROOT, head)
    for path in (PROTOCOL_FILE, "research/forecasts/golden_iv30_rv20.csv", "fno/forecast/iv30.py"):
        assert path in freeze.hashes
    assert not any(path.startswith("fno/research_engine/") for path in freeze.hashes)  # judge 47: behaviour, not bytes
