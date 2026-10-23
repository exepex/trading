"""The simulator reads no new source and touches no counting path (MS-SIM, 7.1 items 1 and 6)."""

import ast
from pathlib import Path

import pytest

from tests.school.contracts.test_boundaries import ROOT, forbidden, imports, module_name

SIMULATOR = ROOT / "fno" / "school" / "simulator"
FILES = sorted(p for p in SIMULATOR.rglob("*.py") if "__pycache__" not in p.parts)
# no NSE or Groww reader, no store wiring (it falls back to NSE), no order or Slack path, and nothing that counts,
# reports, sets a banner or licenses
NEVER = (
    "fno.storage.wiring", "fno.storage.raw_source", "fno.nse_margins", "fno.providers",
    "fno.school.reports", "fno.school.registration", "fno.school.dashcam", "fno.school.accounts", "fno.school.tickets",
)  # fmt: skip


# `practice/stores.py` names the NSE datasets (their file names and archive paths) to read the archive, and only these:
# `daily_files` and the three source classes, never a library builder, which would fetch. It may import them only as
# `from <module> import <name>`: a bare `import fno.storage.wiring` or `from fno.storage import wiring` would make every
# builder in the module reachable without an import the test could see (judge 515 addendum). A test (`test_inputs.py`)
# pins that nothing is requested from NSE.
DATASET_NAMES = {
    "practice/stores.py": frozenset({
        "fno.storage.wiring.daily_files", "fno.storage.raw_source.NseDailyFoSource",
        "fno.storage.raw_source.NseLegacyFoSource", "fno.storage.raw_source.NseIndexCloseSource",
    }),
    # the margin builder reads the archived SPAN files on Drive (A9's archive), never NSE; the factor seam is MS-P1m's
    "practice/fleet.py": frozenset({"fno.nse_margins.road_wiring.build_road_margin"}),
    # `account_net` is the one rupee sum a report may use (327 item 1): a pure function over outcome records that
    # touches no ticket book, ledger or count
    "practice/runner.py": frozenset({"fno.school.tickets.rupees.account_net"}),
}  # fmt: skip


def _is_never(name: str) -> bool:
    return any(name == f or name.startswith(f + ".") for f in NEVER)


def _resolved(node: ast.ImportFrom, package: list[str]) -> str:
    base = package[: len(package) - node.level + 1] if node.level else []
    return ".".join(base + ([node.module] if node.module else []))


def _banned_with_exception(path: Path, package: list[str], allowed: frozenset) -> list[str]:
    """Each forbidden import, judged as written: a `from` import is judged by the names it brings in, so only the
    allowed names pass; a plain `import` of a forbidden module, or a `from` import of the module itself, is refused."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if _is_never(a.name)]
        elif isinstance(node, ast.ImportFrom):
            module = _resolved(node, package)
            found += [
                f"{module}.{a.name}"
                for a in node.names
                if _is_never(f"{module}.{a.name}") and f"{module}.{a.name}" not in allowed
            ]
    return found


def banned(path: Path, package: list[str] | None = None, name: str | None = None) -> list[str]:
    """The path's forbidden imports; `name` (its place under the simulator package) selects an exact-name exception."""
    if name is None and SIMULATOR in path.parents:
        name = path.relative_to(SIMULATOR).as_posix()
    if package is None:
        package = module_name(path)[:-1] if path.name != "__init__.py" else module_name(path)
    if name in DATASET_NAMES:
        return _banned_with_exception(path, package, DATASET_NAMES[name])
    return [n for n in imports(path, package) if _is_never(n)]


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.relative_to(SIMULATOR).as_posix())
def test_no_simulator_module_reads_a_new_source_or_touches_a_counting_path(path):
    assert not banned(path) and not forbidden(imports(path)), (banned(path), forbidden(imports(path)))


def test_a_planted_banner_import_is_caught(tmp_path):
    planted = tmp_path / "planted.py"
    planted.write_text(
        "from fno.school.reports.banner import Banner\nfrom fno.storage.wiring import build_nse_fo_library\n"
    )
    found = banned(planted, ["fno", "school", "simulator"])
    assert found == [
        "fno.school.reports.banner", "fno.school.reports.banner.Banner",
        "fno.storage.wiring", "fno.storage.wiring.build_nse_fo_library",
    ]  # fmt: skip


def test_a_library_builder_import_in_stores_is_caught_while_the_dataset_names_pass(tmp_path):
    """Judge 515 minor: the exception names exact imports, so a fetching library builder cannot slip in beside them."""
    package = ["fno", "school", "simulator", "practice"]
    clean = tmp_path / "clean.py"
    clean.write_text(
        "from ....storage.wiring import daily_files\nfrom ....storage.raw_source import NseDailyFoSource\n"
    )
    assert banned(clean, package, name="practice/stores.py") == []
    planted = tmp_path / "planted_stores.py"
    planted.write_text("from ....storage.wiring import build_nse_fo_library, daily_files\n")
    assert banned(planted, package, name="practice/stores.py") == ["fno.storage.wiring.build_nse_fo_library"]
    other = tmp_path / "other.py"
    other.write_text("from ....storage.wiring import daily_files\n")  # the exception is for stores.py only
    assert banned(other, package, name="practice/other.py") != []


@pytest.mark.parametrize(
    "line",
    ["import fno.storage.wiring", "from ....storage import wiring", "from fno.storage import wiring as w",
     "import fno.storage.raw_source as raw", "from ....storage.raw_source import RawFileSource",
     "from ....storage.wiring import build_nse_fo_library"],
)  # fmt: skip
def test_a_bare_module_import_in_stores_is_caught_too(tmp_path, line):
    """Judge 515 addendum: the module itself would make every builder in it reachable without a visible import."""
    planted = tmp_path / "planted_stores.py"
    planted.write_text(line + "\n")
    assert banned(planted, ["fno", "school", "simulator", "practice"], name="practice/stores.py") != []
