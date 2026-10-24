"""Criterion 7 (story MS-P1a, judge 479 finding 1): the school imports no order call, Slack client, Groww SDK or
provider, by absolute or relative import; the contracts, constants, settings and fakes load nothing outside the
standard library and `fno/school` at all, checked in a fresh interpreter."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCHOOL = ROOT / "fno" / "school"
FILES = sorted(p for p in SCHOOL.rglob("*.py") if "__pycache__" not in p.parts)
FORBIDDEN = ("growwapi", "slack_sdk", "fno.providers", "fno.intraday", "fno.alerts", "fno.desk.git_sync")
LEAF = ("fno.school.constants", "fno.school.settings", "fno.school.fakes", "fno.school.fake_fleet",
        *(f"fno.school.contracts.{p.stem}" for p in sorted((SCHOOL / "contracts").glob("*.py"))))  # fmt: skip


def module_name(path: Path) -> list[str]:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    return parts[:-1] if parts[-1] == "__init__" else parts


def imports(path: Path, package: list[str] | None = None) -> list[str]:
    """Absolute dotted names of every import, relative ones resolved against the file's package."""
    if package is None:
        package = module_name(path) if path.name == "__init__.py" else module_name(path)[:-1]
    names = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - node.level + 1] if node.level else []
            module = ".".join(base + ([node.module] if node.module else []))
            names += [module] + [f"{module}.{a.name}" for a in node.names]
    return names


def forbidden(names: list[str]) -> list[str]:
    return [n for n in names if any(n == f or n.startswith(f + ".") for f in FORBIDDEN)]


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.relative_to(SCHOOL).as_posix())
def test_no_order_slack_groww_or_provider_import(path):
    assert not forbidden(imports(path)), f"{path.name} imports {forbidden(imports(path))}"
    assert "place_order" not in path.read_text(encoding="utf-8")


def test_a_planted_relative_import_is_caught(tmp_path):
    path = tmp_path / "planted.py"  # read as if it sat in fno/school/roads/
    path.write_text("from ...providers.groww import GrowwProvider\nfrom ...alerts import slack\n")
    assert forbidden(imports(path, ["fno", "school", "roads"])) == [
        "fno.providers.groww", "fno.providers.groww.GrowwProvider", "fno.alerts", "fno.alerts.slack"]  # fmt: skip


def test_the_contracts_load_only_the_standard_library_and_the_school():
    code = (f"import sys; before = set(sys.modules); import importlib\n"
            f"for m in {LEAF!r}: importlib.import_module(m)\n"
            "print('\\n'.join(sorted(m for m in set(sys.modules) - before)))")  # fmt: skip
    loaded = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    names = loaded.stdout.split()
    outside = [n for n in names if n.split(".")[0] not in sys.stdlib_module_names and not n.startswith("fno.school")]
    assert outside == ["fno"], f"the contracts load {outside}"  # only the empty `fno` package itself


PRODUCTION = [p for p in FILES if not p.name.startswith("fake")]


@pytest.mark.parametrize("path", PRODUCTION, ids=lambda p: p.relative_to(SCHOOL).as_posix())
def test_no_production_module_imports_the_fakes(path):
    assert not [n for n in imports(path) if n.startswith(("fno.school.fakes", "fno.school.fake_fleet"))]
