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


def banned(path: Path, package: list[str] | None = None) -> list[str]:
    return [n for n in imports(path, package) if any(n == f or n.startswith(f + ".") for f in NEVER)]


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
