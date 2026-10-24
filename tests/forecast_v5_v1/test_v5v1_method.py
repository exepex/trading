"""Amendment 1 sections 3b and 5: the import walk finds the whole input path (the three intraday files included),
lists the shared modules apart, and any byte of a checked file changes the method hash; criterion 11: the package
never reads candle files itself."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from fno.config import ROOT
from fno.forecast_v5_v1.method import (
    FREEZE_STARTS,
    RECORD_STARTS,
    SHARED,
    checked,
    freeze_files,
    method_sha256,
    recorded,
    walk,
)

INTRADAY = ("fno/intraday/candle_rv_table.py", "fno/intraday/rv_table.py", "fno/intraday/row_files.py")


def test_the_walk_reaches_the_candle_table_chain_and_v4s_forecasters():
    files = checked(ROOT, RECORD_STARTS)
    assert set(INTRADAY) <= set(files)
    assert {"fno/forecast_v4_rules/capture.py", "fno/forecast_v4_rules/baselines.py"} <= set(files)
    assert not set(files) & set(SHARED)


def test_the_shared_modules_are_listed_not_hashed():
    assert set(recorded(ROOT, RECORD_STARTS)) == set(SHARED) == {"fno/constants.py", "fno/constants_operations.py",
                                                  "fno/constants_channels.py", "fno/models.py"}  # fmt: skip


def test_the_freeze_walk_adds_the_report_side():
    files = set(checked(ROOT, FREEZE_STARTS))
    assert {"fno/forecast_v5_v1/report.py", "fno/forecast_v5_v1/gap.py", "fno/forecast_v5_v1/method.py"} <= files
    assert "fno/forecast_v5_v1/wiring.py" not in files


@pytest.fixture
def copy(tmp_path) -> Path:
    for relative in {*checked(ROOT, RECORD_STARTS), *SHARED}:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return tmp_path


@pytest.mark.parametrize("planted", ["fno/intraday/candle_rv_table.py", "fno/forecast_v4_rules/baselines.py"])
def test_one_changed_byte_changes_the_method_hash(copy, planted):
    before = method_sha256(copy)
    assert before == method_sha256(ROOT)
    (copy / planted).write_bytes((copy / planted).read_bytes() + b"\n")
    assert method_sha256(copy) != before


def test_a_shared_module_change_leaves_the_method_hash(copy):
    before = method_sha256(copy)
    (copy / "fno/constants.py").write_bytes((copy / "fno/constants.py").read_bytes() + b"\n")
    assert method_sha256(copy) == before


def test_the_package_never_names_the_candle_files_or_their_table():
    for file in (ROOT / "fno" / "forecast_v5_v1").glob("*.py"):
        text = file.read_text(encoding="utf-8")
        assert "rv-candle" not in text and "CandleRvTable" not in text, file.name


def test_the_byte_checked_set_is_the_walk_minus_the_one_exclusion_list():
    walked = set(walk(ROOT, FREEZE_STARTS))
    assert set(checked(ROOT, FREEZE_STARTS)) == walked - set(SHARED)
    assert "fno/intraday/rv_table.py" in checked(ROOT, FREEZE_STARTS)  # v4 only records it; G14 checks it


def test_every_package_file_is_frozen_wiring_and_cli_included_without_walking_them():
    package = {p.relative_to(ROOT).as_posix() for p in (ROOT / "fno" / "forecast_v5_v1").glob("*.py")}
    frozen = set(freeze_files(ROOT))
    assert package <= frozen
    assert frozen == package | set(checked(ROOT, FREEZE_STARTS))


def test_a_new_package_file_is_frozen_at_once(copy):
    (copy / "fno" / "forecast_v5_v1").mkdir(parents=True, exist_ok=True)
    for name in ("history.py", "capture.py", "records.py", "method.py", "report.py", "gap.py"):
        shutil.copyfile(ROOT / "fno" / "forecast_v5_v1" / name, copy / "fno" / "forecast_v5_v1" / name)
    (copy / "fno" / "forecast_v5_v1" / "cli.py").write_text("from ..config import ROOT\n")
    assert "fno/forecast_v5_v1/cli.py" in freeze_files(copy)
    assert "fno/config.py" not in freeze_files(copy)  # cli's imports are not walked
