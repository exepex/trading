"""Story A4b: the 3 pm recorder through the Drive-only store, and the Drive-down case. Raw quote rows go to the private
store only; a quote file that cannot be saved makes the attempt incomplete (never canonical), kept as a sidecar with
the reason, printed, alerted once, exit 1, and never saved in the repository instead."""

import hashlib
import json
from datetime import date, datetime

from fno.models import IST
from fno.quotes.cli import record_today
from fno.quotes.recorder import QuoteSnapshotRecorder
from tests.quotes.drive_fakes import FakeDrive, split_store
from tests.quotes.test_quote_recorder import Clock, FakeProvider
from tests.quotes.test_recorder_calendar import Alerts

DAY = date(2026, 10, 13)
START, LATE = datetime(2026, 10, 13, 14, 55, tzinfo=IST), datetime(2026, 10, 13, 15, 9, 30, tzinfo=IST)
SIDECAR_KEYS = {  # the story's table: identity, times, counts, hashes, NSE's public levels; never a quote row
    "snapshot_id", "underlying", "provider", "started_at", "finished_at", "in_window", "note", "expiries",
    "expiry_source", "monthly_check", "expected_contracts", "recorded_contracts", "complete", "failures",
    "csv_sha256", "raw_file_saved", "spot", "india_vix", "india_vix_time", "futures", "levels_source",
    "levels_failures",
}  # fmt: skip


def _recorder(tmp_path, drive, start=START):
    clock = Clock(start)
    store = split_store(tmp_path, drive)
    return QuoteSnapshotRecorder(FakeProvider(), store, clock.now, clock.sleep), store


def _sidecars(tmp_path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(tmp_path.rglob("*.meta.json"))]


def test_a_recording_puts_the_rows_in_drive_and_the_sidecar_in_the_repository(tmp_path):
    drive = FakeDrive()
    rec, store = _recorder(tmp_path, drive)
    result = rec.record()
    assert result.complete and rec.canonical(DAY) == result.snapshot_id
    csv_path = QuoteSnapshotRecorder.path(DAY, f"{result.snapshot_id}.csv")
    assert list(drive.files) == [csv_path] and not list(tmp_path.rglob("*.csv"))
    (meta,) = _sidecars(tmp_path)
    assert meta["csv_sha256"] == hashlib.sha256(drive.files[csv_path]).hexdigest()
    assert "raw_file_saved" not in meta and store.get(csv_path) == drive.files[csv_path]


def test_the_sidecar_holds_only_the_allowed_keys(tmp_path):
    rec, _ = _recorder(tmp_path, FakeDrive(down_saves=1))
    rec.record()  # one failed save, then a complete attempt: both kinds of sidecar
    sidecars = _sidecars(tmp_path)
    assert len(sidecars) == 2 and all(set(meta) <= SIDECAR_KEYS for meta in sidecars)


def test_the_committed_14_october_sidecar_holds_only_the_allowed_keys():
    from fno.storage.wiring import QUOTES_FOLDER

    path = QUOTES_FOLDER / QuoteSnapshotRecorder.path(date(2026, 10, 14), "nifty_20261014_145500.meta.json")
    assert set(json.loads(path.read_text())) <= SIDECAR_KEYS


def test_drive_down_on_one_attempt_is_kept_as_a_sidecar_and_the_next_one_is_canonical(tmp_path):
    rec, _ = _recorder(tmp_path, FakeDrive(down_saves=1))
    result = rec.record()
    assert result.complete and not result.raw_file_error and rec.canonical(DAY) == result.snapshot_id
    failed, done = _sidecars(tmp_path)
    assert failed["raw_file_saved"] is False and not failed["complete"]
    assert failed["failures"] == ["raw quote file not saved: DriveDown"]  # the type only: no error text in public
    assert "raw_file_saved" not in done and done["complete"]
    assert not list(tmp_path.rglob("*.csv"))


def test_drive_down_for_the_whole_window_ends_none_with_nothing_raw_in_the_repository(tmp_path):
    rec, store = _recorder(tmp_path, FakeDrive(down_saves=10**6), LATE)
    result = rec.record()
    assert not result.complete and result.raw_file_error.startswith("raw quote file not saved: DriveDown")
    assert rec.canonical(DAY) == "none" and not list(tmp_path.rglob("*.csv"))
    assert all(meta["raw_file_saved"] is False for meta in _sidecars(tmp_path))
    assert store.get(QuoteSnapshotRecorder.path(DAY, f"{result.snapshot_id}.csv")) is None


def test_drive_down_is_printed_alerted_once_and_exits_1(tmp_path, capsys):
    alerts = Alerts()
    code = record_today(lambda: _recorder(tmp_path, FakeDrive(down_saves=10**6), LATE)[0], alerts, False, "cal.csv")
    out = capsys.readouterr().out
    assert code == 1 and "complete=False) - raw quote file not saved: DriveDown" in out
    assert len(alerts.sent) == 1 and alerts.sent[0].startswith("3 pm quote recorder: raw quote file NOT saved to Drive")
    assert (
        "(DriveDown: drive unreachable (HTTP 503); nifty_" in alerts.sent[0]
        and "FNO_GDRIVE_* settings" in alerts.sent[0]
    )


def test_without_drive_settings_every_attempt_fails_loudly_and_saves_nothing_raw(tmp_path, capsys):
    alerts = Alerts()
    code = record_today(lambda: _recorder(tmp_path, None, LATE)[0], alerts, False, "cal.csv")
    assert code == 1 and "RawQuoteStoreUnavailable" in capsys.readouterr().out and len(alerts.sent) == 1
    assert not list(tmp_path.rglob("*.csv"))


def test_a_complete_recording_sends_no_drive_alert(tmp_path, capsys):
    alerts = Alerts()
    assert record_today(lambda: _recorder(tmp_path, FakeDrive())[0], alerts, False, "cal.csv") == 0
    assert alerts.sent == [] and "not saved" not in capsys.readouterr().out


def test_an_outside_window_attempt_whose_save_failed_exits_1(tmp_path):
    start = datetime(2026, 10, 13, 20, 0, tzinfo=IST)
    alerts = Alerts()
    assert record_today(lambda: _recorder(tmp_path, FakeDrive(down_saves=1), start)[0], alerts, True, "c") == 1
    assert len(alerts.sent) == 1


class LeakyDrive(FakeDrive):
    def put(self, path, data):
        raise ConnectionError("POST https://drive.example/files?q='planted-folder-id' in parents failed")


def test_a_drive_error_s_text_stays_out_of_the_sidecar_and_the_result_line(tmp_path, capsys):
    alerts = Alerts()
    assert record_today(lambda: _recorder(tmp_path, LeakyDrive(), LATE)[0], alerts, False, "cal.csv") == 1
    assert "planted-folder-id" not in capsys.readouterr().out
    assert all("planted-folder-id" not in p.read_text() for p in tmp_path.rglob("*") if p.is_file())
    assert "planted-folder-id" in alerts.sent[0]  # the private #fno-desk alert keeps the detail for the fix


class LeakyProvider(FakeProvider):
    def quote_book(self, chain, strike, kind):
        raise ConnectionError("GET https://api.example/quote?token=planted-provider-value failed")


def test_a_provider_error_s_text_never_reaches_a_public_file_or_the_result_line(tmp_path, capsys):
    clock = Clock(LATE)
    rec = QuoteSnapshotRecorder(LeakyProvider(), split_store(tmp_path, FakeDrive()), clock.now, clock.sleep)
    assert record_today(lambda: rec, Alerts(), False, "cal.csv") == 1
    assert "planted-provider-value" not in capsys.readouterr().out
    assert all("planted-provider-value" not in p.read_text() for p in tmp_path.rglob("*") if p.is_file())
    failures = _sidecars(tmp_path)[-1]["failures"]
    assert failures and all(f.endswith("ConnectionError (provider message withheld)") for f in failures)
