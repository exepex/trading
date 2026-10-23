"""The simulator reads no new source and touches no counting path (MS-SIM, 7.1 items 1 and 6)."""

from pathlib import Path

import pytest

from tests.school.contracts.test_boundaries import ROOT, forbidden, imports

SIMULATOR = ROOT / "fno" / "school" / "simulator"
FILES = sorted(p for p in SIMULATOR.rglob("*.py") if "__pycache__" not in p.parts)
# no NSE or Groww reader, no store wiring (it falls back to NSE), no order or Slack path, and nothing that counts,
# reports, sets a banner or licenses
NEVER = (
    "fno.storage.wiring", "fno.storage.raw_source", "fno.nse_margins", "fno.providers",
    "fno.school.reports", "fno.school.registration", "fno.school.dashcam", "fno.school.accounts", "fno.school.tickets",
)  # fmt: skip


# `practice/stores.py` names the NSE datasets (their file names and archive paths) to read the archive, and only these:
# `daily_files` and the three source classes, never a library builder, which would fetch. A test (`test_inputs.py`)
# pins that nothing is requested from NSE.
DATASET_NAMES = {
    "practice/stores.py": frozenset({
        "fno.storage.wiring", "fno.storage.wiring.daily_files",
        "fno.storage.raw_source", "fno.storage.raw_source.NseDailyFoSource",
        "fno.storage.raw_source.NseLegacyFoSource", "fno.storage.raw_source.NseIndexCloseSource",
    }),
}  # fmt: skip


def banned(path: Path, package: list[str] | None = None, name: str | None = None) -> list[str]:
    """The path's forbidden imports; `name` (its place under the simulator package) selects an exact-name exception."""
    if name is None and SIMULATOR in path.parents:
        name = path.relative_to(SIMULATOR).as_posix()
    allowed = DATASET_NAMES.get(name, frozenset())
    return [
        n for n in imports(path, package)
        if n not in allowed and any(n == f or n.startswith(f + ".") for f in NEVER)
    ]  # fmt: skip


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
