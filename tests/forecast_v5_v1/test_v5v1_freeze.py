"""Criteria 9 and 12 (judge 596 addendum 2): the freeze record lists exactly today's walk, each file marked "v4 row"
or "v5 only", the shared modules recorded with their hashes, not checked; the check refuses a missing record, a
missing `Frozen on:` line, a changed byte (planted on A16b's candle table) and a list other than the walk."""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest

from fno.config import ROOT
from fno.forecast_v5_v1.freeze import NotFrozen, check, record_text, sha256
from fno.forecast_v5_v1.method import FREEZE_STARTS, SHARED, freeze_files, recorded

DAY = date(2026, 10, 25)
CANDLE_TABLE = "fno/intraday/candle_rv_table.py"


@pytest.fixture
def copy(tmp_path) -> Path:
    for relative in {*freeze_files(ROOT), *recorded(ROOT, FREEZE_STARTS)}:
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, tmp_path / relative)
    return tmp_path


def _v4(root: Path, *paths: str) -> str:
    return "\n".join(f"| `{p}` | `{sha256(root, p)}` |" for p in paths)


def _frozen(root: Path, v4: str = "") -> Path:
    record = root / "FREEZE_v5_v1.md"
    record.write_text(record_text(root, v4, DAY), encoding="utf-8")
    return record


def test_a_written_record_holds_and_gives_its_day(copy):
    assert check(copy, _frozen(copy)) == DAY


def test_each_file_is_marked_v4_row_or_v5_only_and_the_shared_ones_are_recorded(copy):
    text = record_text(copy, _v4(copy, "fno/forecast_v4_rules/capture.py"), DAY)
    assert "| `fno/forecast_v4_rules/capture.py` | `" in text and text.count("| v4 row |") == 1
    assert f"| `{CANDLE_TABLE}` | `{sha256(copy, CANDLE_TABLE)}` | v5 only |" in text
    assert "| `fno/intraday/rv_table.py` |" in text and "only records it" in text
    for shared in recorded(copy, FREEZE_STARTS):
        assert f"| `{shared}` | `{sha256(copy, shared)}` |" in text.split("## Recorded, not checked")[1]
    assert set(recorded(copy, FREEZE_STARTS)) == set(SHARED)


def test_a_v4_row_that_differs_refuses_the_record(copy):
    v4 = "| `fno/forecast_v4_rules/capture.py` | `" + "0" * 64 + "` |"
    with pytest.raises(NotFrozen, match="FREEZE_v4.md row"):
        record_text(copy, v4, DAY)


def test_a_missing_record_refuses(copy):
    with pytest.raises(NotFrozen, match="missing"):
        check(copy, copy / "FREEZE_v5_v1.md")


def test_a_record_without_its_day_refuses(copy):
    record = _frozen(copy)
    record.write_text(record.read_text().replace(f"Frozen on: {DAY}", "Frozen on: soon"))
    with pytest.raises(NotFrozen, match="Frozen on"):
        check(copy, record)


@pytest.mark.parametrize("planted", [CANDLE_TABLE, "fno/forecast_v5_v1/wiring.py", "fno/forecast_v4_rules/series.py"])
def test_one_changed_byte_refuses(copy, planted):
    record = _frozen(copy)
    (copy / planted).write_bytes((copy / planted).read_bytes() + b"\n")
    with pytest.raises(NotFrozen, match="differs"):
        check(copy, record)


def test_a_shared_module_change_does_not_refuse(copy):
    record = _frozen(copy)
    (copy / "fno/constants.py").write_bytes((copy / "fno/constants.py").read_bytes() + b"\n")
    assert check(copy, record) == DAY


def test_a_new_package_file_needs_a_new_record(copy):
    record = _frozen(copy)
    (copy / "fno/forecast_v5_v1/extra.py").write_text('"""new"""\n')
    with pytest.raises(NotFrozen, match="other files"):
        check(copy, record)
