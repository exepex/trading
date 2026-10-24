"""Criterion 7's command half and criterion 9 end to end: `forecast-v5-v1 capture` writes the five rows before
14:30 IST only with a holding freeze record, and exits 1 on any refusal (O1 records it as refused); `freeze` is
written once and only after FREEZE_v4.md; `report` reads A16's live rows and G7b's pairing."""

from __future__ import annotations

from datetime import datetime, time
from types import SimpleNamespace

import pytest

from fno.config import ROOT
from fno.forecast_v5_v1 import cli, wiring
from fno.forecast_v5_v1.capture import FORECASTERS
from fno.forecast_v5_v1.freeze import record_text
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


def _freeze(paths) -> None:
    (paths / "FREEZE_v5_v1.md").write_text(record_text(ROOT, "", DAY))


def test_capture_without_a_freeze_record_refuses_with_exit_1(paths, monkeypatch, capsys):
    assert _run(monkeypatch, "capture") == 1
    assert "nothing written: FREEZE_v5_v1.md is missing" in capsys.readouterr().out
    assert not (paths / "v1_candle").exists()


def test_capture_at_14_30_refuses_with_exit_1(paths, monkeypatch, capsys):
    _freeze(paths)
    assert _run(monkeypatch, "capture", time(14, 30)) == 1
    assert "nothing written:" in capsys.readouterr().out


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
