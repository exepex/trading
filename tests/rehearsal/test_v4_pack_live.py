"""Story G10, "The release and the deadline in a rehearsal before the live date" (RL1-RL3): the `v4-pack` children take
the live dates the daily run's root takes (`rehearsed_live`), so a rehearsal of 23 Oct with `v4_pack` live from 26 Oct
exercises the release and the deadline, while a real run of 23 Oct stays not live."""

import copy
from datetime import date

import pytest

from fno.config import load_app_config
from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.mode import Rehearsal
from fno.rehearsal.v4_pack import NO_CAPTURE, rehearsed_release_excuse
from fno.storage.data_store import DataStore
from fno.storage.receipts import ReceiptFolder
from fno.v4_pack import wiring
from fno.v4_pack.release_run import CAUGHT_UP, EXCUSED, NOT_LIVE, ReleaseRun
from tests.v4_pack.test_release import FakeDrive
from tests.v4_pack.test_release_run import Capture, NoPack, at, label, weekdays

DAY, LIVE, FORECASTS = date(2026, 10, 23), date(2026, 10, 26), date(2026, 10, 22)


def rehearsing(tmp_path):
    return {ENV_FNO_REHEARSAL: Rehearsal.new(DAY, tmp_path, tmp_path / "record").to_env()}


def config(v4_pack=LIVE):
    cfg = copy.deepcopy(load_app_config())
    cfg["daily"]["live_from"].update(v4_pack=v4_pack.isoformat(), forecasts_v4=FORECASTS.isoformat())
    return cfg


def test_rl1_the_children_s_dates_are_the_daily_root_s(tmp_path):
    rehearsed = wiring.run_live_dates(config(), rehearsing(tmp_path))
    assert rehearsed["v4_pack"] == DAY and rehearsed["forecasts_v4"] == FORECASTS  # already live: its own date
    real = wiring.run_live_dates(config(), {})
    assert real["v4_pack"] == LIVE and real["forecasts_v4"] == FORECASTS
    assert wiring.run_live_dates(config(v4_pack=FORECASTS), rehearsing(tmp_path))["v4_pack"] == FORECASTS


@pytest.fixture
def no_services(monkeypatch, tmp_path):
    """The builders' Drive, quote store, calendar and push receipts replaced: only the dates they carry are read."""
    monkeypatch.setattr(wiring, "build_data_store", lambda writer, env=None: DataStore(
        FakeDrive(), "data", ReceiptFolder(tmp_path / "receipts"), writer, "run-1"))  # fmt: skip
    monkeypatch.setattr("fno.storage.quote_wiring.build_drive_only_quote_store", lambda *a, **k: object())
    monkeypatch.setattr("fno.storage.wiring.build_session_calendar", lambda: object())
    monkeypatch.setattr(wiring, "build_commitment_times", lambda root=None, env=None: object())


@pytest.mark.parametrize("build", [wiring.build_release_run, wiring.build_deadline_run])
def test_rl2_both_builders_carry_the_rehearsed_date_and_a_real_run_the_real_one(no_services, tmp_path, build):
    assert build(config(), rehearsing(tmp_path)).live_from == DAY
    assert build(config(), {}).live_from == LIVE


def release(tmp_path, env):
    drive, live = FakeDrive(), wiring.run_live_dates(config(), env)
    store = DataStore(drive, "data", ReceiptFolder(tmp_path / "receipts"), "v4-release", "run-1")
    excuse = rehearsed_release_excuse(lambda record, day: False, env)  # the record holds no `v4` attempt
    run = ReleaseRun(store, lambda path: drive.get(path) is not None, Capture(ended=True), NoPack(), weekdays,
                     live["v4_pack"], lambda: at(DAY, 14, 46), live["forecasts_v4"], excuse)  # fmt: skip
    return run, drive


def test_rl3_a_rehearsal_exercises_the_release_and_a_real_run_stays_not_live(tmp_path):
    run, drive = release(tmp_path, rehearsing(tmp_path))
    assert run.run(DAY) == [CAUGHT_UP.format(day=FORECASTS), EXCUSED.format(day=DAY, note=NO_CAPTURE)]
    assert label(drive, FORECASTS) == label(drive, DAY) == "system_late" and not run.failed
    run, drive = release(tmp_path / "real", {})
    assert run.run(DAY) == [NOT_LIVE] and drive.files == {} and not run.failed
