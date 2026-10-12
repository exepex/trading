"""Guards for the whole test run."""

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROTECTED = [ROOT / "data" / "live", ROOT / "journal"]  # real results and paper trades: tests must never write here
# Set this when running the tests on the same checkout as a running live desk (which writes there itself).
BESIDE_LIVE_DESK = "FNO_TESTS_BESIDE_LIVE_DESK"


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
    if os.environ.get(BESIDE_LIVE_DESK):
        return
    after = _snapshot()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))  # new, changed, deleted
    assert not changed, f"tests changed the repository's data: {changed}"
