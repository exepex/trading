"""Criterion 7 (story MS-P1a): nothing under fno/school imports an order call, a Slack client or the Groww SDK, and
no production module imports the fakes."""

import ast
from pathlib import Path

import pytest

SCHOOL = Path(__file__).resolve().parents[3] / "fno" / "school"
FORBIDDEN = ("growwapi", "slack_sdk", "requests", "fno.providers", "fno.intraday", "fno.alerts", "fno.desk.git_sync")
FILES = sorted(p for p in SCHOOL.rglob("*.py") if "__pycache__" not in p.parts)


def imports(path: Path) -> list[str]:
    names = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(("." * node.level) + (node.module or ""))
    return names


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.relative_to(SCHOOL).as_posix())
def test_no_order_slack_or_groww_import(path):
    bad = [n for n in imports(path) if any(n == f or n.startswith(f + ".") for f in FORBIDDEN)]
    assert not bad, f"{path.name} imports {bad}"
    assert "place_order" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "path", [p for p in FILES if p.name != "fakes.py"], ids=lambda p: p.relative_to(SCHOOL).as_posix()
)
def test_no_production_module_imports_the_fakes(path):
    assert not [n for n in imports(path) if n.endswith("fakes")]
