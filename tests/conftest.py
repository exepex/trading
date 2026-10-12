"""Guards for the whole test run."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROTECTED = [ROOT / "data" / "live", ROOT / "journal"]  # real results and paper trades: tests must never write here


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
    changed = sorted(k for k in after if before.get(k) != after[k])
    assert not changed, f"tests wrote into the repository's data: {changed}"
