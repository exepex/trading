"""Criterion 7 (amendment 2) and criterion 9 end to end: `forecast-v5-v1 capture` writes the five rows before 14:30
IST only with a holding freeze record. A planned "no row" prints "nothing written:" and exits 0 (O1: `refused`); a
fault exits 1 (O1: `failed`), each checked at the command and through O1's own `outcome`. `freeze` is written once and
only after FREEZE_v4.md; `report` reads A16's live rows and G7b's pairing."""

from __future__ import annotations

from datetime import date, datetime, time
from types import SimpleNamespace

import pytest

from fno.config import ROOT
from fno.constants import STEP_FAILED, STEP_REFUSED
from fno.daily.steps import outcome
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


def _o1_status(code: int, out: str) -> str:
    return outcome(("forecast-v5-v1", "capture"), code, out.splitlines()).result["status"]


def _refused(paths, monkeypatch, capsys, why: str, at: time = time(14, 12)) -> None:
    code, out = _run(monkeypatch, "capture", at), capsys.readouterr().out
    assert (code, _o1_status(code, out)) == (0, STEP_REFUSED)
    assert f"nothing written: {why}" in out and not (paths / "v1_candle").exists()


def _failed(paths, monkeypatch, capsys, why: str) -> str:
    code, out = _run(monkeypatch, "capture"), capsys.readouterr().out
    assert (code, _o1_status(code, out)) == (1, STEP_FAILED)
    assert "nothing written:" not in out and why in out
    return out


def test_no_freeze_record_yet_is_refused(paths, monkeypatch, capsys):
    _refused(paths, monkeypatch, capsys, "FREEZE_v5_v1.md is missing")


def test_at_14_30_is_refused(paths, monkeypatch, capsys):
    _freeze(paths)
    _refused(paths, monkeypatch, capsys, "", time(14, 30))


def test_a_record_frozen_after_today_is_refused(paths, monkeypatch, capsys):
    _freeze(paths, date(2026, 10, 23))
    _refused(paths, monkeypatch, capsys, "FREEZE_v5_v1.md is frozen on 2026-10-23, after today")


def test_a_changed_byte_checked_file_fails(paths, monkeypatch, capsys):
    _freeze(paths)
    record = paths / "FREEZE_v5_v1.md"
    digest = sha256(ROOT, "fno/intraday/rv_table.py")  # as if rv_table.py's bytes had changed since the freeze
    record.write_text(record.read_text().replace(digest, "0" * 64))
    _failed(paths, monkeypatch, capsys, "fno/intraday/rv_table.py differs")
    assert not (paths / "v1_candle").exists()


def test_a_walk_list_that_differs_fails(paths, monkeypatch, capsys):
    _freeze(paths)
    record = paths / "FREEZE_v5_v1.md"
    record.write_text(
        "\n".join(line for line in record.read_text().splitlines() if "fno/intraday/row_files.py" not in line)
    )
    _failed(paths, monkeypatch, capsys, "lists other files than today's walk")


def test_an_unparseable_frozen_on_fails(paths, monkeypatch, capsys):
    _freeze(paths)
    record = paths / "FREEZE_v5_v1.md"
    record.write_text(record.read_text().replace(f"Frozen on: {DAY}", "Frozen on: 2026-02-30"))
    _failed(paths, monkeypatch, capsys, "is not a date")


def test_a_different_row_already_written_fails(paths, monkeypatch, capsys):
    _freeze(paths)
    assert _run(monkeypatch, "capture") == 0
    capsys.readouterr()
    file = next((paths / "v1_candle").glob("v5c_ewma_094/*.csv"))
    file.write_text(file.read_text().replace(",ok,", ",not_eligible,"))
    _failed(paths, monkeypatch, capsys, "a different row is already written")


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
