"""Owner's engineering standard (CLAUDE.md, Code): no file and no class over 350 lines; break it down instead."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LIMIT = 350
CODE_FOLDERS = ("fno", "tests", "tools", "research")


def python_files() -> list[Path]:
    files = (p for folder in CODE_FOLDERS for p in (ROOT / folder).rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(files)


@pytest.mark.parametrize("path", python_files(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_file_and_classes_within_limit(path):
    text = path.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= LIMIT, f"file has more than {LIMIT} lines: break it down"
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef):
            size = node.end_lineno - node.lineno + 1
            assert size <= LIMIT, f"class {node.name} has {size} lines: break it down"
