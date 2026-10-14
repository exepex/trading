"""Guards for the whole test run."""

import os
from pathlib import Path

import pytest

from tests.live_credentials import LIVE_CREDENTIALS

ROOT = Path(__file__).resolve().parent.parent
# Recorded research data and paper-desk records: tests must never write here.
PROTECTED = [ROOT / "research" / "data", ROOT / "journal"]


def _snapshot() -> dict[str, float]:
    files = {}
    for folder in PROTECTED:
        for path in folder.rglob("*") if folder.exists() else []:
            if path.is_file():
                files[str(path)] = path.stat().st_mtime
    return files


@pytest.fixture(scope="session", autouse=True)
def repository_data_is_untouched():
    before = _snapshot()
    yield
    after = _snapshot()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))  # new, changed, deleted
    assert not changed, f"tests changed the repository's data: {changed}"


@pytest.fixture(scope="session")
def empty_home(tmp_path_factory):
    return tmp_path_factory.mktemp("home")


@pytest.fixture(autouse=True)
def no_real_credentials(monkeypatch, empty_home):
    """Tests never reach a real broker account, Google Drive, #fno-desk, a database, a routine or GitHub through
    credentials that happen to be set on the machine; a test that needs them sets fake ones itself. The home folder
    is an empty one, so `python -m fno` (in process or as a subprocess) cannot reload them from the machine's env
    file; git keeps the machine's own settings (its identity)."""
    for name in LIVE_CREDENTIALS:
        monkeypatch.delenv(name, raising=False)
    git_config = Path.home() / ".gitconfig"
    if git_config.is_file() and "GIT_CONFIG_GLOBAL" not in os.environ:
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(git_config))
    monkeypatch.setenv("HOME", str(empty_home))
    monkeypatch.setenv("USERPROFILE", str(empty_home))
