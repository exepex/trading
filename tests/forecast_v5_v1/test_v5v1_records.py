"""G14's records: G7's row plus three columns, written once (same row again: nothing; a changed day: refused)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from fno.forecast_v4_rules.records import RecordConflict, record
from fno.forecast_v5_v1 import records

DAY = date(2026, 10, 22)


def _row(value=7.0e-5, made_on="python 3.13; numpy 2; libc glibc 2.39", sources="candle:1664;live:1"):
    g7 = record(DAY, "v1_rv_next_session", "ok", value, kind="baseline", slot="reported", label="live",
                method_sha256="a" * 64, inputs_sha256="b" * 64, made_at="2026-10-22T14:12:00+05:30")  # fmt: skip
    return records.v5_record(g7, sources, made_on)


def test_a_row_reads_back_with_every_column(tmp_path):
    assert records.write_day(tmp_path, "v1_rv_next_session", {"v5c_har_intraday": _row()}) == 1
    file = records.path(tmp_path, "v5c_har_intraday", "v1_rv_next_session")
    assert file.read_text().splitlines()[0].endswith("made_at,input_measure,input_sources,platform")
    assert records.read(file) == {DAY.isoformat(): _row()}


def test_the_same_row_from_another_machine_or_time_changes_nothing(tmp_path):
    records.write_day(tmp_path, "q", {"f": _row()})
    again = replace(_row(made_on="python 3.12; numpy 1; libc glibc 2.43"), made_at="later")
    assert records.write_day(tmp_path, "q", {"f": again}) == 0
    assert records.read(records.path(tmp_path, "f", "q"))[DAY.isoformat()].platform.startswith("python 3.13")


@pytest.mark.parametrize("changed", [_row(value=7.1e-5), _row(sources="candle:1663;live:2")])
def test_a_changed_row_for_a_written_day_is_refused(tmp_path, changed):
    records.write_day(tmp_path, "q", {"f": _row()})
    before = records.path(tmp_path, "f", "q").read_text()
    with pytest.raises(RecordConflict):
        records.write_day(tmp_path, "q", {"f": changed})
    assert records.path(tmp_path, "f", "q").read_text() == before


def test_one_changed_forecaster_writes_none_of_the_day(tmp_path):
    records.write_day(tmp_path, "q", {"b": _row()})
    other = replace(_row(), day="2026-10-23")
    with pytest.raises(RecordConflict):
        records.write_day(tmp_path, "q", {"a": _row(), "b": _row(value=7.1e-5), "c": other})
    assert not records.path(tmp_path, "a", "q").exists() and not records.path(tmp_path, "c", "q").exists()


def test_no_file_reads_as_no_rows(tmp_path):
    assert records.read(tmp_path / "none.csv") == {}
    assert records.write_day(tmp_path, "q", {}) == 0
    assert not (tmp_path / "f").exists()


def test_the_platform_names_python_numpy_and_libc():
    text = records.capture_platform()
    assert text.startswith("python ") and "; numpy " in text and "; libc " in text
