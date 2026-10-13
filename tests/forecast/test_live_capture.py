"""Protocol v2's live capture (ChatGPT review 29, response 63): the closes-through-d-1 gate (`history_stale`), the
pack's 15:00 values standing in for the day's close, the v2 record (`live_1500_proxy`, `iv30_status`, generation by
15:15 IST), write-once records with a receipt, and no record before version 2 is frozen."""

import json
from argparse import Namespace
from datetime import date, datetime, timedelta

import pytest

from fno.forecast.capture import CaptureRefused, LiveCapture, live_probabilities
from fno.forecast.cli import cmd_forecast
from fno.forecast.closes_source import CommittedClosesFile, OfficialCloses
from fno.forecast.freeze_v2 import NotFrozen, NotYetFrozen, require_version_frozen
from fno.forecast.iv30 import AtmIv30
from fno.forecast.live_history import LiveForecastHistory, stale_history, stale_iv30_history
from fno.forecast.live_pack import CUTOFF, LIVE_MODE, LivePack, LivePackBuilder, PackField
from fno.forecast.schema import ForecastRecord, ForecastRecordError
from fno.forecast.schema_v2 import RECORD_COLUMNS_V2, ForecastRecordV2
from fno.models import IST
from fno.research_data.panel_reader import NiftyPanel
from fno.research_engine.implied_vol import Black76
from fno.research_engine.live_features import LiveAtmIvMinusRealised
from fno.storage.raw_store import LocalFolderStore
from tests.forecast.forecast_fixtures import CALENDAR, DAYS, ESTIMATOR
from tests.forecast.test_live_pack import GOLDEN, _build, _files

LIVE_DAY = DAYS[60]
EMPTY_PANEL = NiftyPanel((), {}, {})


def _closes(count: int = 60, skip: int | None = None) -> OfficialCloses:
    rows = {d: (100.0 + i, 15.0) for i, d in enumerate(DAYS[:count]) if i != skip}
    return OfficialCloses("fixture", rows | {LIVE_DAY: (1.0, 1.0)})  # a same-day close the pack must never use


def _pack(spot: float = 200.0) -> LivePack:
    pack = LivePack(LIVE_DAY, {}, {}, "calendar-fixture")
    expiry = LIVE_DAY + timedelta(days=20)
    pack.fields += [PackField("nifty_spot", spot, "fixture", ""), PackField("india_vix", 16.0, "fixture", ""),
                    PackField(f"future_{expiry.isoformat()}", spot + 1, "fixture", ""),
                    PackField(f"future_{expiry.isoformat()}_volume", "500", "fixture", "")]  # fmt: skip
    pack.iv30 = AtmIv30(15.0, True, (expiry,))
    return pack


def test_the_live_day_close_is_the_pack_spot_and_earlier_days_are_official_closes():
    history = LiveForecastHistory(_pack(), _closes(), EMPTY_PANEL, CALENDAR, ESTIMATOR)
    assert history.closes.nifty[LIVE_DAY] == 200.0 and history.closes.vix[LIVE_DAY] == 16.0
    assert history.closes.nifty[DAYS[59]] == 159.0
    assert history.iv30(LIVE_DAY).points == 15.0 and history.near_future(LIVE_DAY)[0] == 201.0


def test_history_stale_unless_every_trading_day_before_the_forecast_day_has_closes():
    assert stale_history(_closes(), CALENDAR, LIVE_DAY) == []
    assert stale_history(_closes(skip=30), CALENDAR, LIVE_DAY) == ["history_stale"]
    assert stale_history(_closes(count=59), CALENDAR, LIVE_DAY) == ["history_stale"]  # the day before is missing
    assert stale_history(OfficialCloses("none", {}), CALENDAR, LIVE_DAY) == ["history_stale"]


def test_a_stale_history_records_no_forecast_for_the_methods_that_read_it():
    history = LiveForecastHistory(_pack(), _closes(skip=30), EMPTY_PANEL, CALENDAR, ESTIMATOR)
    gates = stale_history(_closes(skip=30), CALENDAR, LIVE_DAY) + stale_iv30_history(history, LIVE_DAY)
    assert gates == ["history_stale", "iv30_history_stale"]  # the empty panel has no past IV30 either
    by = live_probabilities(history, gates)
    assert set(by["baseline_b_base_rate"].values()) == {None} and set(by["baseline_c_model"].values()) == {None}
    assert by["baseline_a_risk_neutral"]["q1_nifty_up_20d"] is not None  # needs only the pack


def _record(at: datetime, mode: str = LIVE_MODE, status: str = "flagged") -> ForecastRecordV2:
    cutoff = datetime(2026, 10, 13, 15, 0, tzinfo=IST)
    base = ForecastRecord("book1_rules", date(2026, 10, 13), cutoff, "q1_nifty_up_20d", 0.5, "book1/x", "a" * 64)
    return ForecastRecordV2(base, mode, status, at)


def test_generation_deadline_is_15_15_ist():
    assert _record(datetime(2026, 10, 13, 15, 15, tzinfo=IST)).on_time
    assert not _record(datetime(2026, 10, 13, 15, 15, 1, tzinfo=IST)).on_time


def test_v2_record_columns_mode_and_iv30_status():
    record = _record(datetime(2026, 10, 13, 15, 5, tzinfo=IST))
    row = record.row()
    assert tuple(row) == RECORD_COLUMNS_V2 and ForecastRecordV2.from_row(row) == record
    assert row["input_mode"] == "live_1500_proxy" and row["iv30_status"] == "flagged"
    assert "flag" not in row["method_or_version"]  # input quality stays out of the method label
    with pytest.raises(ForecastRecordError):
        _record(datetime(2026, 10, 13, 15, 5, tzinfo=IST), mode="live")
    with pytest.raises(ForecastRecordError):
        _record(datetime(2026, 10, 13, 15, 5, tzinfo=IST), status="ok")


def _capture(tmp_path, clock=datetime(2026, 10, 13, 15, 5, tzinfo=IST)) -> LiveCapture:
    builder = LivePackBuilder(LiveAtmIvMinusRealised(CUTOFF, 0.065, Black76()))
    store, closes = LocalFolderStore(GOLDEN / "case_a" / "quotes"), CommittedClosesFile(tmp_path / "none.csv")
    return LiveCapture(tmp_path, store, closes, lambda: EMPTY_PANEL, CALENDAR, ESTIMATOR, builder,
                       "calendar-fixture", lambda: clock)  # fmt: skip


def test_capture_writes_once_with_a_receipt_and_refuses_a_different_pack(tmp_path):
    capture = _capture(tmp_path)
    line, receipt = capture.capture(date(2026, 10, 13))  # risk-neutral Q1-Q2 and Book 1 on them (frozen v1 rule)
    assert "recorded; 4 of 20 probabilities; iv30 interpolated" in line and "history_stale" in line
    folder = tmp_path / "research" / "forecasts" / "live_v2" / "2026"
    pack = json.loads((folder / "2026-10-13_pack.json").read_bytes())
    assert receipt.startswith("receipt: 2026-10-13 pack ") and "generated_at 2026-10-13T15:05:00+05:30" in receipt
    assert pack["mode"] == LIVE_MODE and "history_stale" in pack["problems"]
    assert "already recorded" in capture.capture(date(2026, 10, 13))[0]
    (folder / "2026-10-13_pack.json").write_bytes(b"{}")
    with pytest.raises(CaptureRefused):
        capture.capture(date(2026, 10, 13))


def test_a_closed_day_records_nothing(tmp_path):
    assert "not a trading day" in _capture(tmp_path).capture(date(2026, 10, 18))[0]  # a Sunday
    assert not (tmp_path / "research").exists()


def test_without_a_freeze_record_the_capture_records_nothing(tmp_path, capsys, monkeypatch):
    with pytest.raises(NotYetFrozen):
        require_version_frozen(tmp_path, "0" * 40)

    def not_yet(*args, **kwargs):
        raise NotYetFrozen("research/forecasts/FREEZE_v2.md does not exist")

    monkeypatch.setattr("fno.forecast.freeze_v2.require_version_frozen", not_yet)
    assert cmd_forecast(Namespace(forecast_cmd="capture", day=None, run_id=None)) == 0
    assert "nothing recorded" in capsys.readouterr().out


def test_a_failed_freeze_check_fails_the_capture(capsys, monkeypatch):
    def changed(*args, **kwargs):
        raise NotFrozen("frozen files changed after the freeze: fno/forecast/live_pack.py")

    monkeypatch.setattr("fno.forecast.freeze_v2.require_version_frozen", changed)
    assert cmd_forecast(Namespace(forecast_cmd="capture", day=None, run_id=None)) == 1
    assert "freeze check failed" in capsys.readouterr().out


def test_case_a_pack_from_the_golden_inputs_matches_the_committed_pack_values():
    committed = json.loads((GOLDEN / "case_a" / "pack.json").read_bytes())
    assert committed["iv30"]["points"] == pytest.approx(_build(_files("case_a")).iv30.points, abs=1e-12)
