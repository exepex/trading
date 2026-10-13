"""Every inline `python -c` snippet in the GitHub Actions workflows compiles as Actions runs it (first panel-days run,
38474280810: a `run: |` block split an alert's Python string over two lines, a SyntaxError, so the #fno-desk line was
never sent, and O6's index-closes.yml had the same). `run: |` keeps newlines and `run: >` folds them, so each step is
read through YAML exactly as the runner receives it."""

import re
from pathlib import Path

import pytest
import yaml

from fno.config import ROOT

WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
SNIPPET = re.compile(r"""python -c (?P<q>["'])(?P<code>.*?)(?P=q)""", re.DOTALL)
EXPRESSION = re.compile(r"\$\{\{.*?\}\}")  # GitHub fills these in before the shell runs


def _snippets(path: Path) -> list[tuple[str, str]]:
    found = []
    for job in yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"].values():
        for step in job["steps"]:
            for match in SNIPPET.finditer(step.get("run", "")):
                found.append((step.get("name", "?"), EXPRESSION.sub("x", match.group("code"))))
    return found


def test_the_workflows_have_inline_snippets_to_check():
    assert sum(len(_snippets(path)) for path in WORKFLOWS) >= 10


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_inline_python_snippet_compiles(path):
    broken = []
    for name, code in _snippets(path):
        try:
            compile(code, f"{path.name}: {name}", "exec")
        except SyntaxError as error:
            broken.append(f"{name}: {error.msg}")
    assert broken == []
