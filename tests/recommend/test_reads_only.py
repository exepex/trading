"""REC1b criterion 8: the recommender reads sealed records only, so it imports no fill, order, exit, account or
desk-writing code (judge 654 S2; J's plant: `from ..desk import exits` in `decide.py`). Criterion 10's card part: the
card cannot read the recommender at all, so its output is the same with the step on or off (judge 653 m1: the
construction argument, proved here by the import graph)."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RECOMMEND = ROOT / "fno" / "recommend"
# Writers and traders the recommender must never reach; only the named readers inside these packages are allowed
FORBIDDEN = ("fno.desk", "fno.books", "fno.playbook", "fno.school.execution", "fno.school.accounts", "fno.school.fleet",
             "fno.school.safety", "fno.school.drivers", "fno.school.tickets", "fno.school.simulator", "fno.providers",
             "fno.risk", "fno.checks", "fno.daily")  # fmt: skip
READERS = frozenset({"fno.desk.run_log", "fno.books.version_registry", "fno.playbook.registry",
                     "fno.playbook.opportunities"})  # fmt: skip


def imported(path: Path, package: str) -> set[str]:
    """Every module a file imports, `from x import y` counted as both `x` and `x.y` (a submodule or a name)."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = package.split(".")[: len(package.split(".")) - node.level + 1] if node.level else []
            module = ".".join(base + ([node.module] if node.module else []))
            found |= {module} | {f"{module}.{alias.name}" for alias in node.names}
    return found


def breaches(path: Path) -> list[str]:
    names = imported(path, "fno.recommend")
    readers = {n for n in names if any(n == r or n.startswith(r + ".") for r in READERS)}
    return sorted(
        n
        for n in names - readers
        if any(n == f or n.startswith(f + ".") for f in FORBIDDEN) and not any(r.startswith(n + ".") for r in READERS)
    )  # a package named only on the way to a reader


@pytest.mark.parametrize("path", sorted(RECOMMEND.glob("*.py")), ids=lambda p: p.name)
def test_the_recommender_imports_no_writer_or_trader(path):
    assert breaches(path) == []


def test_the_planted_desk_import_is_caught(tmp_path):
    planted = tmp_path / "decide.py"
    planted.write_text((RECOMMEND / "decide.py").read_text() + "\nfrom ..desk import exits\n")
    assert breaches(planted) == ["fno.desk.exits"]


def test_no_card_module_reads_the_recommender():
    card_files = sorted((ROOT / "fno" / "cards").glob("*.py"))
    assert card_files
    for path in card_files:
        assert not {n for n in imported(path, "fno.cards") if n.startswith("fno.recommend")}, path.name
