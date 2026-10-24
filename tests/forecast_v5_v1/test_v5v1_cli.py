"""Criterion 7's command half and criterion 9 end to end: `forecast-v5-v1 capture` writes the five rows before
14:30 IST only with a holding freeze record, and exits 1 on any refusal (O1 records it as refused); `freeze` is
written once and only after FREEZE_v4.md; `report` reads A16's live rows and G7b's pairing."""

from __future__ import annotations

from datetime import date, datetime, time
from types import SimpleNamespace

import pytest

from fno.config import ROOT
from fno.forecast_scoring.v4.freeze_check import table
from fno.forecast_v5_v1 import cli, wiring
from fno.forecast_v5_v1.capture import FORECASTERS
from fno.forecast_v5_v1.freeze import record_text, sha256
from fno.models import IST

DAY = datetime(2026, 10, 22).date()


@pytest.fixture
def paths(tmp_path, monkeypatch):
    monkeypatch.setattr(wiring, "RECORDS_FOLDER", tmp_path / "v1_candle")
    monkeypatch.setattr(wiring, "FREEZE_FILE", tmp_path / "FREEZE_v5_v1.md")
    monkeypatch.setattr(wiring, "V4_FREEZE_FILE", tmp_path / "FREEZE_v4.md")
    return tmp_path


def _run(monkeypatch, command: str, at: time = time(14, 12)) -> int:
    monkeypatch.setattr("fno.models.now_ist", lambda: datetime.combine(DAY, at, IST))
    return cli.cmd_forecast_v5_v1(SimpleNamespace(forecast_v5_v1_cmd=command))


def _freeze(paths, day=DAY) -> None:
    (paths / "FREEZE_v5_v1.md").write_text(record_text(ROOT, "", [], day))


def test_capture_without_a_freeze_record_refuses_with_exit_1(paths, monkeypatch, capsys):
    assert _run(monkeypatch, "capture") == 1
    assert "nothing written: FREEZE_v5_v1.md is missing" in capsys.readouterr().out
    assert not (paths / "v1_candle").exists()


def test_capture_at_14_30_refuses_with_exit_1(paths, monkeypatch, capsys):
    _freeze(paths)
    assert _run(monkeypatch, "capture", time(14, 30)) == 1
    assert "nothing written:" in capsys.readouterr().out
    assert not (paths / "v1_candle").exists()


def test_a_record_frozen_after_today_refuses(paths, monkeypatch, capsys):
    _freeze(paths, date(2026, 10, 23))
    assert _run(monkeypatch, "capture") == 1
    assert "after today" in capsys.readouterr().out


def test_a_changed_byte_refuses_the_capture(paths, monkeypatch, capsys):
    _freeze(paths)
    record = paths / "FREEZE_v5_v1.md"
    digest = sha256(ROOT, "fno/intraday/rv_table.py")  # as if rv_table.py's bytes had changed since the freeze
    record.write_text(record.read_text().replace(digest, "0" * 64))
    assert _run(monkeypatch, "capture") == 1
    assert "nothing written: fno/intraday/rv_table.py differs" in capsys.readouterr().out
    assert not (paths / "v1_candle").exists()


def test_a_different_row_already_written_refuses_with_its_line(paths, monkeypatch, capsys):
    _freeze(paths)
    assert _run(monkeypatch, "capture") == 0
    file = next((paths / "v1_candle").glob("v5c_ewma_094/*.csv"))
    file.write_text(file.read_text().replace(",ok,", ",not_eligible,"))
    assert _run(monkeypatch, "capture") == 1
    assert "a different row is already written" in capsys.readouterr().out


def test_capture_before_the_cutoff_writes_five_rows(paths, monkeypatch, capsys):
    _freeze(paths)
    assert _run(monkeypatch, "capture") == 0
    assert "5 rows written" in capsys.readouterr().out
    assert sorted(p.parent.name for p in (paths / "v1_candle").glob("*/*.csv")) == sorted(FORECASTERS.values())


def test_o1s_pathspecs_name_each_forecasters_folder():
    assert wiring.record_folders() == [f"research/forecasts/v5/v1_candle/{n}/" for n in sorted(FORECASTERS.values())]


def test_freeze_waits_for_the_v4_record_and_is_written_once(paths, monkeypatch, capsys):
    assert _run(monkeypatch, "freeze") == 1
    assert "FREEZE_v4.md is not in this tree yet" in capsys.readouterr().out
    (paths / "FREEZE_v4.md").write_text("")
    assert _run(monkeypatch, "freeze") == 1
    assert "FREEZE_v4.md has no row" in capsys.readouterr().out
    (paths / "FREEZE_v4.md").write_text(table(ROOT))
    assert _run(monkeypatch, "freeze") == 0
    assert "Frozen on: 2026-10-22" in (paths / "FREEZE_v5_v1.md").read_text()
    assert _run(monkeypatch, "freeze") == 1
    assert "never rewritten" in capsys.readouterr().out


def test_the_report_prints_the_table_and_the_real_gap(paths, monkeypatch, capsys):
    _freeze(paths)
    _run(monkeypatch, "capture")
    assert _run(monkeypatch, "report") == 0
    out = capsys.readouterr().out
    assert "| v5c_har_intraday | 1 | 0 | 1 | 0 | 0 | not enough data yet |" in out  # 22 Oct's target, 23 Oct: void
    assert "| 22 Oct 2026 | 1.210651e-04 | 1.221083e-04 | 1.009 |" in out
