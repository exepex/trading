"""Guards for the whole test run."""

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


@pytest.fixture(autouse=True)
def no_real_credentials(monkeypatch):
    """Tests never reach a real broker account, Google Drive, #fno-desk, a database, a routine or GitHub through
    credentials that happen to be set on the machine; a test that needs them sets fake ones itself."""
    for name in LIVE_CREDENTIALS:
        monkeypatch.delenv(name, raising=False)
