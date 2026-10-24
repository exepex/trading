"""Story G11 criterion C15: G11 is not a money piece because nothing that decides a trade reads the AI books' v4
work. Every module of the deciding packages is read two ways: its imports (an AST walk, relative imports resolved)
and its text (a string in a comment counts too). A later package that decides trades (F1t's `fno/ai_trading`) is
added to `DECIDING` by its builder. Note: O1's daily steps stage all of `research/forecasts/v4/` for commits
(`fno/daily/wiring.py`), which commits files but decides nothing."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DECIDING = ("fno/desk", "fno/books", "fno/book3", "fno/risk", "fno/factory", "fno/playbook")
FORBIDDEN_TEXT = ("research/forecasts/v4/book", "book2_hybrid_v2", "book3_ai_v2")


def imported(path: Path) -> set[str]:
    """Every module `path` imports, relative imports resolved against its own package."""
    package = path.relative_to(ROOT).with_suffix("").parts[:-1]
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - node.level + 1] if node.level else ()
            module = ".".join((*base, node.module)) if node.module else ".".join(base)
            found |= {module} | {f"{module}.{alias.name}" for alias in node.names}
    return found


def problems(path: Path) -> list[str]:
    ai = sorted(m for m in imported(path) if m == "fno.ai" or m.startswith("fno.ai."))
    text = path.read_text(encoding="utf-8")
    return ai + [s for s in FORBIDDEN_TEXT if s in text]


@pytest.mark.parametrize("package", DECIDING)
def test_no_deciding_module_reads_the_ai_books_v4_work(package):
    modules = sorted((ROOT / package).rglob("*.py"))
    assert modules, f"{package} has no modules: the list is stale"
    assert {str(p.relative_to(ROOT)): problems(p) for p in modules if problems(p)} == {}


def test_a_planted_import_or_path_is_found(tmp_path, monkeypatch):
    monkeypatch.setattr(f"{__name__}.ROOT", tmp_path)
    module = tmp_path / "fno" / "desk" / "planted.py"
    module.parent.mkdir(parents=True)
    module.write_text("from ..ai import v4_rows  # reads research/forecasts/v4/book3_ai_v2\n")
    assert problems(module) == ["fno.ai", "fno.ai.v4_rows", "research/forecasts/v4/book", "book3_ai_v2"]


def test_an_empty_module_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(f"{__name__}.ROOT", tmp_path)
    module = tmp_path / "fno" / "risk" / "empty.py"
    module.parent.mkdir(parents=True)
    module.write_text("")
    assert problems(module) == []
