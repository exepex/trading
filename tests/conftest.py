"""Guards for the whole test run."""

from pathlib import Path

import pytest

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
def no_real_broker_credentials(monkeypatch):
    """Tests never reach a real broker account or the network through credentials that happen to be set on the
    machine; a test that needs them sets fake ones itself."""
    from fno.constants import ENV_GROWW_ACCESS_TOKEN, ENV_GROWW_API_KEY, ENV_GROWW_API_SECRET, ENV_GROWW_TOTP_SECRET

    for name in (ENV_GROWW_ACCESS_TOKEN, ENV_GROWW_API_KEY, ENV_GROWW_API_SECRET, ENV_GROWW_TOTP_SECRET):
        monkeypatch.delenv(name, raising=False)
