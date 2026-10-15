"""Story A16 criteria 12 and 13: the commands' exit codes, the dry run (outside the repository, no alert, no commit)
and the composition root."""

from argparse import Namespace
from pathlib import Path

import pytest

from fno.alerts.sender import NoAlertSender
from fno.intraday import wiring
from fno.intraday.cli import cmd_intraday, report
from fno.intraday.dry_run import NOT_PUBLISHED, NoPublish
from fno.intraday.first_version_store import FirstVersionStore
from fno.intraday.recorder import ALREADY, NO_MARK, NOT_TRADING_DAY, SlotOutcome
from fno.storage.manifest_commit import GitManifestRecorder
from fno.storage.wiring import REPOSITORY
from tests.intraday.groww_fakes import FakeGrowwProvider

PLANTED = "PLANTED-SECRET-9c1d"


@pytest.mark.parametrize(
    "statuses, code",
    [(["good"], 0), ([ALREADY], 0), ([NOT_TRADING_DAY], 0), ([NO_MARK], 0), (["good", "stale"], 1), (["missed"], 1),
     (["late"], 1), (["failed"], 1), (["incomplete"], 1)],
)  # fmt: skip
def test_exit_codes(statuses, code, capsys):
    assert report([SlotOutcome(s, "10:00") for s in statuses]) == code
    assert capsys.readouterr().out.startswith("10:00 ")


def test_a_dry_run_folder_inside_the_repository_is_refused(capsys):
    args = Namespace(intraday_cmd="snapshot", dry_run=REPOSITORY / "research" / "tmp", config="config.yaml")
    assert cmd_intraday(args) == 1
    assert "must be outside the repository" in capsys.readouterr().out


def test_the_dry_run_wiring_uses_local_folders_no_alert_and_no_commit(tmp_path, monkeypatch):
    monkeypatch.setattr(wiring, "GrowwProvider", lambda cfg: FakeGrowwProvider())
    recorder = wiring.build_intraday_recorder({}, tmp_path)
    assert isinstance(recorder.store, FirstVersionStore) and recorder.store.raw.store.folder == tmp_path / "drive"
    assert isinstance(recorder.alerts, NoAlertSender) and recorder.alerts.send("x") == "alert NOT sent: dry run"
    assert isinstance(recorder.publisher, NoPublish) and recorder.publisher.commit("x") == NOT_PUBLISHED
    assert recorder.ledger.folder == tmp_path and recorder.heartbeat.file == tmp_path / "heartbeat.json"
    assert [s.name for s in recorder.clock_check.servers] == ["github", "slack"]


def test_the_live_wiring_needs_the_owners_drive_settings(monkeypatch):
    monkeypatch.setattr(wiring, "GrowwProvider", lambda cfg: FakeGrowwProvider())
    with pytest.raises(RuntimeError, match="FNO_GDRIVE_FOLDER_ID"):
        wiring.build_intraday_recorder({})


def test_the_live_wiring_writes_to_the_repository_folder_and_commits_it(monkeypatch, tmp_path):
    monkeypatch.setattr(wiring, "GrowwProvider", lambda cfg: FakeGrowwProvider())
    monkeypatch.setattr(wiring, "build_owner_drive", lambda: wiring.LocalFolderStore(tmp_path))
    recorder = wiring.build_intraday_recorder({})
    assert recorder.ledger.folder == wiring.INTRADAY_FOLDER == REPOSITORY / "research" / "data" / "intraday"
    assert isinstance(recorder.publisher, GitManifestRecorder) and recorder.publisher.folder == "research/data/intraday"
    assert recorder.publisher.message.format(what="x") == "Data: intraday slots (x)"
    assert Path(recorder.store.index_file) == wiring.INTRADAY_FOLDER / "revisions.csv"


def test_a_failure_while_building_or_running_is_named_alerted_and_exits_1_and_a_dry_run_sends_nothing(
    tmp_path, monkeypatch, capsys
):
    def broken(cfg, folder):
        raise ConnectionError(f"refused {PLANTED}")

    monkeypatch.setattr(wiring, "build_intraday_recorder", broken)
    args = Namespace(intraday_cmd="snapshot", dry_run=tmp_path, config="config.yaml")
    assert cmd_intraday(args) == 1
    out = capsys.readouterr().out
    assert "stopped with ConnectionError" in out and "alert NOT sent: dry run" in out and PLANTED not in out


def test_a_dry_run_outside_the_calendar_sends_no_real_alert(tmp_path, monkeypatch, capsys):
    from fno.research_data.calendar import CalendarError

    def outside(cfg, folder):
        raise CalendarError("2027-01-04 is outside the calendar")

    monkeypatch.setattr(wiring, "build_intraday_recorder", outside)
    assert cmd_intraday(Namespace(intraday_cmd="run", dry_run=tmp_path, until=None, config="config.yaml")) == 1
    assert "alert NOT sent: dry run" in capsys.readouterr().out


def test_rv_refusals_exit_1(tmp_path, monkeypatch, capsys):
    from fno.intraday.recorder import SettleRefused

    class Refusing:
        def settle_day(self, day):
            raise SettleRefused("2026-10-20 is not a recorded session")

    monkeypatch.setattr(wiring, "build_intraday_recorder", lambda cfg, folder: Refusing())
    assert cmd_intraday(Namespace(intraday_cmd="rv", dry_run=None, day=None, config="config.yaml")) == 1
    assert "rv refused: 2026-10-20 is not a recorded session" in capsys.readouterr().out


def test_the_nse_listing_used_for_expiries_is_read_only(monkeypatch):
    monkeypatch.setattr(wiring, "GrowwProvider", lambda cfg: FakeGrowwProvider())
    plan = wiring.build_intraday_recorder({}, Path("/tmp/a16-dry")).source.plan
    assert plan.fallback.library.archive is None and plan.monthlies.history is plan.fallback


def test_the_silence_check_reads_githubs_copy():
    beat = wiring.build_heartbeat()
    assert beat.path == "research/data/intraday/heartbeat.json" and beat.branch == "main"
