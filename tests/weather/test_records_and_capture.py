"""Story M1, criteria 6, 8, 9 and 10 on the committed closes, VIX and events: the RED share, the records, the live
capture's refusals and the back-fill's byte-identical rerun."""

from datetime import date, datetime

import pytest

from fno.forecast_v4_rules import records as v4
from fno.forecast_v4_rules.capture import CaptureRefused
from fno.forecast_v4_rules.records import BACKFILL, LIVE, RecordConflict
from fno.models import IST
from fno.weather.capture import backfill_weather, capture_weather
from fno.weather.records import NOT_ENOUGH, WeatherRecords, red_share
from fno.weather.wiring import build_weather_days, is_session, previous_regular

from .fakes import FakeStore

DAY = date(2026, 10, 15)
BEFORE = datetime(2026, 10, 15, 14, 25, tzinfo=IST)  # before the 14:30 cutoff (G10)
WEATHER = build_weather_days()


def _capture(tmp_path, d=DAY, now=BEFORE, flag="normal", store=None, previous=previous_regular):
    writer = lambda f, q, rows: v4.write(tmp_path / "v4", f, q, rows)  # noqa: E731
    store = FakeStore() if store is None else store
    lines = capture_weather(WEATHER, WeatherRecords(tmp_path / "weather"), d, now, is_session, writer, lambda: flag,
                            store, previous)  # fmt: skip
    return lines, store


def test_red_share_over_250_live_records():
    assert red_share(["RED"] * 37 + ["GREEN"] * 212, "GREEN") == {"red_share": 37 / 250, "over_alarming": False}
    assert red_share(["RED"] * 37 + ["GREEN"] * 212, "RED") == {"red_share": 38 / 250, "over_alarming": True}
    assert red_share(["GREEN"] * 248, "RED") == {"red_share": NOT_ENOUGH, "over_alarming": NOT_ENOUGH}
    assert red_share(["RED"] * 300 + ["GREEN"] * 249, "GREEN")["red_share"] == 0.0  # only the most recent 250


def test_back_fill_records_never_count_toward_the_250(tmp_path):
    records = WeatherRecords(tmp_path)
    for n, label in enumerate([BACKFILL] * 3 + [LIVE] * 2):
        d = date(2026, 1, 5 + n)
        records.write(d, {"day": d.isoformat(), "label": label, "colour": "RED", "made_at": ""})
    assert records.live_colours_before(date(2026, 1, 9)) == ["RED"]  # 8 Jan; 9 Jan is the day itself
    assert records.first_live() == date(2026, 1, 8)


def test_capture_before_the_cutoff_writes_the_record_and_both_forecasters_rows(tmp_path):
    lines, store = _capture(tmp_path)
    public = WeatherRecords(tmp_path / "weather").for_day(DAY)
    assert set(public) == {
        "day", "label", "colour", "status", "operative", "proof", "model_colour", "v0_colour", "v0_status",
        "probabilities", "red_share", "over_alarming", "drivers", "method_sha256", "inputs_sha256", "made_at",
    }  # fmt: skip
    assert (public["label"], public["red_share"], public["made_at"]) == (LIVE, NOT_ENOUGH, "2026-10-15T08:55:00+00:00")
    assert public["status"] == "scored"
    assert set(public["probabilities"]) == {"weather_vix_v1", "weather_checklist_v0", "base_rate"}
    for forecaster, slot, kind in (("weather_vix_v1", "rules", "rule"), ("weather_checklist_v0", "reported",
                                                                         "baseline")):  # fmt: skip
        for question in ("v6_abs_move_2pct_next_session", "v6_abs_move_2pct_within_5_sessions"):
            row = v4.read(v4.path(tmp_path / "v4", forecaster, question))["2026-10-15"]
            assert (row.slot, row.kind, row.label, row.status) == (slot, kind, LIVE, "ok")
            assert float(row.value) == public["probabilities"][forecaster][question]["value"]
    assert lines[0] == f"weather 2026-10-15: {public['colour']} ({public['proof']}); 4 v4 rows written"
    assert WeatherRecords(tmp_path / "weather").for_day(date(2026, 10, 14)) is None


def test_a_rerun_the_same_day_keeps_the_first_record(tmp_path):
    _capture(tmp_path)
    first = (tmp_path / "weather" / "2026" / "2026-10-15.json").read_bytes()
    lines, _ = _capture(tmp_path, now=BEFORE.replace(minute=28))
    assert (tmp_path / "weather" / "2026" / "2026-10-15.json").read_bytes() == first
    assert "0 v4 rows written" in lines[0]
    records = WeatherRecords(tmp_path / "weather")
    with pytest.raises(RecordConflict):
        records.write(DAY, {**records.for_day(DAY), "colour": "RED"})


@pytest.mark.parametrize("d, why", [
    (date(2026, 10, 2), "not a v4 session"),  # Gandhi Jayanti: holiday
    (date(2026, 10, 17), "not a v4 session"),  # Saturday
    (date(2026, 2, 1), "not a v4 session"),  # Sunday Union Budget special session
    (date(2026, 11, 8), "not a v4 session"),  # Diwali muhurat
])  # fmt: skip
def test_no_record_on_a_day_that_is_not_a_regular_session(tmp_path, d, why):
    with pytest.raises(CaptureRefused, match=why):
        _capture(tmp_path, d=d, now=datetime.combine(d, BEFORE.time(), IST))
    assert not (tmp_path / "weather").exists() and not (tmp_path / "v4").exists()


def test_at_or_after_the_cutoff_and_on_another_day_nothing_is_written(tmp_path):
    with pytest.raises(CaptureRefused, match="at or after"):
        _capture(tmp_path, now=BEFORE.replace(hour=15, minute=0))
    with pytest.raises(CaptureRefused, match="not today"):
        _capture(tmp_path, d=date(2026, 10, 14))
    assert not (tmp_path / "weather").exists() and not (tmp_path / "v4").exists()


def test_closes_not_reaching_the_previous_regular_session_write_nothing(tmp_path):
    with pytest.raises(CaptureRefused, match="not at the previous regular session 2026-10-15"):
        _capture(tmp_path, previous=lambda d: date(2026, 10, 15))  # as if the 14 Oct close were not yet committed
    assert not (tmp_path / "weather").exists()


def test_the_back_fill_is_exploratory_ends_before_the_first_live_day_and_reruns_identically(tmp_path):
    def run(folder):
        writer = lambda f, q, rows: v4.write(folder / "v4", f, q, rows)  # noqa: E731
        return backfill_weather(WEATHER, WeatherRecords(folder / "weather"), date(2019, 6, 3), writer)

    lines = run(tmp_path / "a")
    run(tmp_path / "b")
    again = run(tmp_path / "a")
    files = sorted(p.relative_to(tmp_path / "a") for p in (tmp_path / "a").rglob("*") if p.is_file())
    assert files == sorted(p.relative_to(tmp_path / "b") for p in (tmp_path / "b").rglob("*") if p.is_file())
    assert all((tmp_path / "a" / f).read_bytes() == (tmp_path / "b" / f).read_bytes() for f in files)
    records = WeatherRecords(tmp_path / "a" / "weather")
    days = sorted(date.fromisoformat(f.stem) for f in (tmp_path / "a" / "weather").rglob("*.json"))
    assert (days[0], days[-1]) == (date(2017, 1, 3), date(2019, 5, 31))
    assert all(records.for_day(d)["label"] == BACKFILL for d in days)
    assert lines[0].startswith(f"back-fill (exploratory): {len(days)} days; colours ")
    assert again[1] == "0 v4 rows added"


def test_a_capture_writes_only_inside_the_folders_the_daily_run_commits(tmp_path):
    """O1 commits exactly `record_folders()` for the weather step: a real capture, laid out as in the repository,
    writes nothing outside them (so no other step's commit can hold M1's files, nor M1's theirs)."""
    from fno.config import ROOT
    from fno.forecast_v4_rules.wiring import V4_FOLDER
    from fno.weather.folders import record_folders
    from fno.weather.wiring import WEATHER_FOLDER

    v4_root, records = tmp_path / V4_FOLDER.relative_to(ROOT), tmp_path / WEATHER_FOLDER.relative_to(ROOT)
    writer = lambda f, q, rows: v4.write(v4_root, f, q, rows)  # noqa: E731
    capture_weather(WEATHER, WeatherRecords(records), DAY, BEFORE, is_session, writer, lambda: "normal", FakeStore(),
                    previous_regular)  # fmt: skip
    written = [p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()]
    assert written and all(any(w.startswith(folder) for folder in record_folders()) for w in written), written
    assert record_folders() == ("research/forecasts/v4/weather/", "research/forecasts/v4/weather_vix_v1/",
                                "research/forecasts/v4/weather_checklist_v0/")  # fmt: skip
