"""Story M1, criteria 7, 8 and 11 and judge 129's notes: the US flag reaches only the private Drive part (never a
repository file or a printed line), the drivers change no forecast, invalid values are never written, and nothing
first seen after the cutoff reaches a day's weather."""

from dataclasses import replace
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from fno.forecast_v4_rules import records as v4
from fno.forecast_v4_rules.baselines import OK, Value
from fno.forecast_v4_rules.records import InvalidRecord
from fno.models import IST
from fno.weather import cli as weather_cli
from fno.weather import wiring
from fno.weather.capture import PRIVATE_NOT_SAVED, PRIVATE_SAVED, capture_weather
from fno.weather.day import WeatherDays
from fno.weather.records import WeatherRecords
from fno.weather.wiring import build_weather_days, is_session, previous_regular

from .fakes import FakeStore

DAY = date(2026, 10, 15)
BEFORE = datetime(2026, 10, 15, 14, 55, tzinfo=IST)
FLAG = "flag-sentinel-7f3a"  # stands for the private flag: must never reach a repository file or a printed line
WEATHER = build_weather_days()


def _capture(folder, flag=FLAG, store=None, weather=WEATHER):
    writer = lambda f, q, rows: v4.write(folder / "v4", f, q, rows)  # noqa: E731
    return capture_weather(weather, WeatherRecords(folder / "weather"), DAY, BEFORE, is_session, writer, lambda: flag,
                           store, previous_regular)  # fmt: skip


def _repository_text(folder) -> str:
    return "".join(p.read_text() for p in folder.rglob("*") if p.is_file())


def test_the_flag_goes_only_to_the_private_drive_part(tmp_path):
    store = FakeStore()
    lines = _capture(tmp_path, store=store)
    assert store.files == {"weather/2026/2026-10-15.json": b'{\n "day": "2026-10-15",\n "us_move": "' + FLAG.encode()
                           + b'"\n}\n'}  # fmt: skip
    assert FLAG not in _repository_text(tmp_path) and FLAG not in "\n".join(lines)
    assert WeatherRecords(tmp_path / "weather").for_day(DAY)["drivers"]["us_move"] == "private"
    assert lines[-1] == PRIVATE_SAVED


def test_without_drive_settings_the_public_record_is_still_written_and_the_capture_says_so(tmp_path):
    lines = _capture(tmp_path, store=None)
    assert lines[-1] == PRIVATE_NOT_SAVED.format(why="the owner's Drive settings are not set")
    assert WeatherRecords(tmp_path / "weather").for_day(DAY) is not None
    failing = _capture(tmp_path / "b", store=FakeStore(fail=OSError("drive said no: " + FLAG)))
    assert failing[-1] == PRIVATE_NOT_SAVED.format(why="OSError") and FLAG not in "\n".join(failing)


def test_the_us_flag_changes_no_forecast_and_no_colour(tmp_path):
    _capture(tmp_path / "large", flag="large")
    _capture(tmp_path / "normal", flag="normal")
    assert _repository_text(tmp_path / "large") == _repository_text(tmp_path / "normal")


def test_no_committed_v4_file_holds_a_us_flag():
    for file in wiring.V4_FOLDER.rglob("*"):
        text = file.read_text() if file.is_file() else ""
        assert '"us_move": "large"' not in text and '"us_move": "normal"' not in text, file
    for file in wiring.WEATHER_FOLDER.rglob("*.json"):
        assert WeatherRecords(wiring.WEATHER_FOLDER).for_day(date.fromisoformat(file.stem))["drivers"]["us_move"] == (
            "private")  # fmt: skip


def test_the_printed_capture_never_shows_the_flag(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fno.models.now_ist", lambda: BEFORE)
    monkeypatch.setattr(wiring, "build_records", lambda: WeatherRecords(tmp_path / "weather"))
    monkeypatch.setattr(wiring, "build_writer", lambda: lambda f, q, rows: v4.write(tmp_path / "v4", f, q, rows))
    monkeypatch.setattr(wiring, "build_private_store", lambda: FakeStore())
    monkeypatch.setattr(wiring, "build_cue_reader", lambda: None)
    monkeypatch.setattr("fno.weather.drivers.us_move_flag", lambda *a, **k: FLAG)
    assert weather_cli.cmd_weather(SimpleNamespace(weather_cmd="capture", day=None)) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("weather 2026-10-15: ") and FLAG not in printed and PRIVATE_SAVED in printed
    assert weather_cli.cmd_weather(SimpleNamespace(weather_cmd="capture", day=date(2026, 10, 14))) == 0
    assert "nothing written" in capsys.readouterr().out


class Broken:
    def forecast(self, d, horizon):
        return Value(OK, 1.5)


def test_an_invalid_value_is_refused_and_nothing_is_written(tmp_path):
    weather = build_weather_days()
    weather.models["weather_vix_v1"] = Broken()
    with pytest.raises(InvalidRecord):
        _capture(tmp_path, weather=weather)
    assert not (tmp_path / "weather").exists() and not (tmp_path / "v4").exists()


def _moved_after(d: date) -> WeatherDays:
    """The committed inputs with every close and VIX from `d` on changed, and an event announced after `d`."""
    inputs = WEATHER.inputs
    rows = [replace(r, close=r.close * 1.2, vix=r.vix * 3) if r.day >= d else r for r in inputs.rows]
    lines = [f"{line},moved" if line[:10] >= d.isoformat() else line for line in inputs.closes_lines]
    late = replace(inputs.events[0], day=date(2026, 10, 16), announced=date(2026, 10, 16))
    return WeatherDays(replace(inputs, rows=rows, closes_lines=lines, events=[*inputs.events, late]))


def test_nothing_first_seen_after_the_cutoff_reaches_the_days_weather():
    for d in (DAY, date(2024, 6, 4), date(2020, 3, 23)):
        moved = _moved_after(d)
        assert moved.day(d, "live", "", {}).public == WEATHER.day(d, "live", "", {}).public
        assert moved.day(d, "live", "", {}).rows == WEATHER.day(d, "live", "", {}).rows
    later = date(2024, 6, 5)
    assert _moved_after(date(2024, 6, 4)).values(later) != WEATHER.values(later)  # the moved close is seen next day


def test_the_previous_session_is_the_previous_regular_one():
    days = WEATHER.days
    assert date(2024, 1, 20) not in days and date(2023, 11, 12) not in days  # special and muhurat sessions
    assert previous_regular(date(2024, 1, 23)) == date(2024, 1, 19)  # not the special Saturday of 20 Jan
    assert previous_regular(date(2023, 11, 13)) == date(2023, 11, 10)  # not the muhurat Sunday of 12 Nov
    assert WEATHER.latest_row(date(2024, 1, 23)) == date(2024, 1, 19)
    vix_19 = next(r.vix for r in WEATHER.inputs.rows if r.day == date(2024, 1, 19))
    assert WEATHER.models["weather_vix_v1"].scale(date(2024, 1, 23)) == pytest.approx(vix_19 / 100 / 252**0.5)


def test_the_method_hash_covers_every_file_that_decides_a_value():
    fno = wiring.ROOT / "fno"
    assert {"weather/wiring.py", "forecast_v4/sessions.py", "forecast_v4_rules/series.py"} <= set(wiring.METHOD_FILES)
    assert all((fno / name).is_file() for name in wiring.METHOD_FILES)


def test_the_method_hash_changes_when_a_weather_constant_changes(tmp_path):
    """The thresholds and colours (`fno/weather/constants.py`) are part of the method: a changed red floor changes the
    record's method hash."""
    fno = wiring.ROOT / "fno"
    for name in wiring.METHOD_FILES:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_bytes((fno / name).read_bytes())
    before = wiring.method_sha256(tmp_path)
    assert before == wiring.method_sha256(fno)
    constants = tmp_path / "weather" / "constants.py"
    constants.write_text(constants.read_text().replace("(0.10, 0.35)", "(0.11, 0.35)"))
    assert wiring.method_sha256(tmp_path) != before
