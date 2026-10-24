"""REH1b: A4's captures in a rehearsal are the day's recorded attempts, republished at their own recorded times into
the rehearsal's store, byte for byte, with the day's canonical marker; nothing is captured live and nothing is
written to the record."""

import json
from datetime import date, datetime, timedelta

import pytest

from fno.models import IST
from fno.quotes.recorder import DATASET, QuoteSnapshotRecorder
from fno.rehearsal.drive import RehearsalWriteRefused
from fno.rehearsal.record_store import RecordReader
from fno.rehearsal.recorded_quotes import RecordedRecorder
from fno.storage.raw_store import LocalFolderStore

DAY = date(2026, 10, 23)
FOLDER = f"{DATASET}/2026/10"


class Clock:
    def __init__(self, at):
        self.at, self.slept = at, []

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.at += timedelta(seconds=seconds)


def attempt(record, snapshot_id, finished, in_window, complete=True, rows=3):
    meta = {"snapshot_id": snapshot_id, "finished_at": finished.isoformat(), "in_window": in_window,
            "complete": complete, "csv_sha256": "x"}  # fmt: skip
    record.put(f"{FOLDER}/{snapshot_id}.meta.json", json.dumps(meta).encode())
    record.put(f"{FOLDER}/{snapshot_id}.csv", b"header\n" + b"row\n" * rows)


@pytest.fixture
def day(tmp_path):
    record = LocalFolderStore(tmp_path / "record")
    attempt(record, "nifty_20261023_145500", datetime(2026, 10, 23, 14, 57, 38, tzinfo=IST), True)
    attempt(record, "nifty_20261023_151500", datetime(2026, 10, 23, 15, 15, 40, tzinfo=IST), False)
    record.put(f"{FOLDER}/nifty_20261023.canonical", b"nifty_20261023_145500")
    clock, store = Clock(datetime(2026, 10, 23, 14, 38, tzinfo=IST)), LocalFolderStore(tmp_path / "rehearsal")
    live = QuoteSnapshotRecorder(None, store, clock_now=clock, sleep=clock.sleep)  # never asked to capture
    return RecordedRecorder(live, RecordReader(record)), record, store, clock


def test_the_3_pm_record_is_the_recorded_attempt_at_its_own_time_with_its_marker(day):
    recorded, record, store, clock = day
    result = recorded.record()
    assert (result.status, result.snapshot_id, result.complete, result.rows) == ("recorded", "nifty_20261023_145500",
                                                                                True, 3)  # fmt: skip
    assert clock() == datetime(2026, 10, 23, 14, 57, 38, tzinfo=IST)  # published when it was recorded, not before
    for name in ("nifty_20261023_145500.csv", "nifty_20261023_145500.meta.json", "nifty_20261023.canonical"):
        assert store.get(f"{FOLDER}/{name}") == record.get(f"{FOLDER}/{name}")
    assert store.get(f"{FOLDER}/nifty_20261023_151500.csv") is None  # the 15:15 capture is not the 3 pm record
    assert recorded.record().status == "already recorded"


def test_the_desk_s_15_15_capture_is_the_recorded_execution_attempt(day):
    recorded, record, store, clock = day
    clock.at = datetime(2026, 10, 23, 15, 15, tzinfo=IST)
    result = recorded.capture()
    assert (result.status, result.snapshot_id, result.complete) == ("recorded", "nifty_20261023_151500", True)
    assert store.get(f"{FOLDER}/nifty_20261023_151500.csv") == record.get(f"{FOLDER}/nifty_20261023_151500.csv")
    assert store.get(f"{FOLDER}/nifty_20261023.canonical") is None  # an execution capture is never canonical


def test_a_day_with_no_recorded_attempt_says_so_and_ends_none(tmp_path):
    clock, store = Clock(datetime(2026, 10, 23, 14, 38, tzinfo=IST)), LocalFolderStore(tmp_path / "rehearsal")
    live = QuoteSnapshotRecorder(None, store, clock_now=clock, sleep=clock.sleep)
    recorded = RecordedRecorder(live, RecordReader(LocalFolderStore(tmp_path / "empty")))
    result = recorded.record()
    assert result.status == "window closed" and "no recorded in-window attempt of nifty" in result.reason
    assert store.get(f"{FOLDER}/nifty_20261023.canonical") == b"none"
    assert recorded.capture().status == "window closed"


def test_the_record_is_never_written(day):
    recorded, record, store, clock = day
    with pytest.raises(RehearsalWriteRefused):
        recorded.source.put(f"{FOLDER}/nifty_20261023.canonical", b"changed")
    assert record.get(f"{FOLDER}/nifty_20261023.canonical") == b"nifty_20261023_145500"


def test_the_record_s_groww_file_comes_from_the_real_drive_checked_against_its_sidecar(tmp_path, monkeypatch):
    import hashlib

    from fno.config import ROOT
    from fno.quotes.drive_only_store import DriveOnlyQuoteStore, RawQuoteHashMismatch
    from fno.rehearsal.drive import DryrunDrive
    from fno.rehearsal.mode import Rehearsal
    from fno.rehearsal.quote_wiring import record_quote_store
    from fno.storage.wiring import QUOTES_FOLDER

    from .fakes import RecordingDrive

    rows = b"header\nrow\n"
    sidecar = tmp_path / "record" / QUOTES_FOLDER.relative_to(ROOT) / FOLDER / "nifty_20261023_145500.meta.json"
    sidecar.parent.mkdir(parents=True)
    sidecar.write_text(json.dumps({"csv_sha256": hashlib.sha256(rows).hexdigest()}))
    real = RecordingDrive(
        {f"raw/{FOLDER}/nifty_20261023_145500.csv": rows, f"raw/{FOLDER}/nifty_20261023_151500.csv": b"x"}
    )
    (sidecar.parent / "nifty_20261023_151500.meta.json").write_text(json.dumps({"csv_sha256": "0" * 64}))
    monkeypatch.setattr("fno.storage.wiring.build_owner_drive", lambda *a, **k: DryrunDrive(real, "dryrun/r", bool))
    live = DriveOnlyQuoteStore(LocalFolderStore(tmp_path / "clone"), lambda: None, DATASET, "settings")
    store = record_quote_store(live, Rehearsal(DAY, "r", tmp_path / "state", tmp_path / "record"))
    assert store.get(f"{FOLDER}/nifty_20261023_145500.csv") == rows and real.writes == []
    with pytest.raises(RawQuoteHashMismatch):
        store.get(f"{FOLDER}/nifty_20261023_151500.csv")


def test_a_late_execution_capture_is_never_served_an_earlier_attempt(day):
    """Judge 559's note: at 15:20 the day recorded no capture, so the 15:15:40 attempt is not passed off as one."""
    recorded, record, store, clock = day
    clock.at = datetime(2026, 10, 23, 15, 20, tzinfo=IST)
    result = recorded.capture()
    assert result.status == "window closed" and "no recorded execution attempt" in result.reason
    assert store.get(f"{FOLDER}/nifty_20261023_151500.csv") is None


def test_the_real_builders_find_the_day_s_attempts_in_the_record(tmp_path, monkeypatch):
    """REH1g (DRY2's crash): the real NIFTY and NSE recorders under the mode list the record's sidecars; before, A4b's
    Drive-only store could not list a folder and both parts and the 15:15 snapshot died."""
    from fno import composition
    from fno.config import ROOT, load_app_config
    from fno.constants import ENV_FNO_REHEARSAL
    from fno.quotes.recorder import NSE_DATASET
    from fno.rehearsal.mode import Rehearsal
    from fno.storage.wiring import QUOTES_FOLDER

    record = tmp_path / "record"
    for dataset, stem in ((DATASET, "nifty"), (NSE_DATASET, "nifty")):
        folder = record / QUOTES_FOLDER.relative_to(ROOT) / dataset / "2026" / "10"
        folder.mkdir(parents=True)
        meta = {"snapshot_id": f"{stem}_20261023_145500", "finished_at": "2026-10-23T14:57:38+05:30",
                "in_window": True, "complete": True, "csv_sha256": "x"}  # fmt: skip
        (folder / f"{stem}_20261023_145500.meta.json").write_text(json.dumps(meta))
    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal(DAY, "r", tmp_path / "state", record).to_env())
    monkeypatch.setattr("fno.storage.wiring.build_owner_drive", lambda *a, **k: None)
    cfg = load_app_config()
    for build in (composition.build_quote_recorder, composition.build_nse_quote_recorder):
        recorder = build(cfg)
        assert isinstance(recorder, RecordedRecorder)
        assert [a.snapshot_id for a in recorder._attempts(DAY)] == ["nifty_20261023_145500"]
