"""Clean-slate criterion 1: no runnable file imports a removed module, and every app module imports cleanly."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_imports  # noqa: E402

APP_MODULES = sorted(
    ".".join(p.relative_to(ROOT).with_suffix("").parts).removesuffix(".__init__")
    for p in (ROOT / "fno").rglob("*.py")
    if "__pycache__" not in p.parts
)


def test_no_runnable_file_imports_a_missing_fno_module():
    assert check_imports.problems() == []


def test_the_archival_replay_is_the_only_skipped_file_and_really_imports_the_old_desk():
    replay = ROOT / "research" / "2026-10-12-backtest" / "replay.py"
    assert {"research/2026-10-12-backtest/replay.py"} == check_imports.ARCHIVAL
    assert any(name.startswith("fno.live") for name in check_imports.missing_fno_imports(replay))


def test_the_check_catches_absolute_and_relative_imports_of_removed_modules(tmp_path):
    (tmp_path / "fno" / "quotes").mkdir(parents=True)
    for init in ("fno/__init__.py", "fno/quotes/__init__.py"):
        (tmp_path / init).write_text("")
    (tmp_path / "fno" / "models.py").write_text("IST = 1\n")
    (tmp_path / "fno" / "quotes" / "a.py").write_text(
        "from ..live.services import x\nfrom .. import journal\nimport fno.backtest.cli\nfrom ..models import IST\n"
    )
    found = check_imports.problems(tmp_path)
    assert len(found) == 3 and all("fno/quotes/a.py" in f for f in found)
    assert any("fno.live.services" in f for f in found) and any("fno.journal" in f for f in found)


@pytest.mark.parametrize("module", APP_MODULES)
def test_every_app_module_imports(module):
    importlib.import_module(module)
