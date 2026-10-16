"""A20a: the ban list is filed under the trade date it names and a stale one is refused; the job takes nothing on a
non-trading day, runs every step even after one fails, and sends ONE alert naming every failure (exit 1)."""

from datetime import date
from pathlib import Path

import pytest

from fno.alerts.dry_run import DryRunAlertSender
from fno.alerts.run_location import NO_RUN_URL, run_location
from fno.fo_masters.job import NOT_A_TRADING_DAY, FoMastersJob, Step, StepFailed, taken
from fno.storage.content_checks import COVERED_SESSION, VALIDATORS
from fno.storage.manifest_commit import ManifestRecorder
from fno.storage.raw_store import LocalFolderStore
from fno.storage.session_filed_taker import CurrentSessionTaker, LaterSession, StaleCopy
from fno.storage.snapshot_source import FoBanListSource
from fno.storage.snapshot_taker import NOT_SERVED, TAKEN
from fno.storage.wiring import build_session_calendar

BAN_16 = (Path(__file__).parents[1] / "fixtures" / "nse" / "fo_masters" / "fo_secban_16102026.csv").read_bytes()
D15, D16, D17, D19 = date(2026, 10, 15), date(2026, 10, 16), date(2026, 10, 17), date(2026, 10, 19)


class Serving:
    FILENAME, path_for = FoBanListSource.FILENAME, FoBanListSource.path_for

    def __init__(self, data):
        self.data = data

    def fetch(self, path):
        return self.data


def ban_taker(store, data=BAN_16) -> CurrentSessionTaker:
    source = FoBanListSource
    return CurrentSessionTaker(store, Serving(data), VALIDATORS[source], COVERED_SESSION[source])


def test_the_ban_list_is_filed_under_its_trade_date(tmp_path):
    store = LocalFolderStore(tmp_path)
    assert ban_taker(store).take(D16) == TAKEN.format(path=FoBanListSource.path_for(D16), size=len(BAN_16))
    assert FoBanListSource.path_for(D16) == "nse/derivatives/fo-ban-list/2026/10/16/fo_secban.csv"
    assert store.get(FoBanListSource.path_for(D16)) == BAN_16


def test_a_ban_list_for_an_earlier_session_is_stale_and_nothing_is_written(tmp_path):
    store = LocalFolderStore(tmp_path)
    with pytest.raises(StaleCopy, match="stale"):
        ban_taker(store).take(D19)  # NSE still serves 16 Oct's list on 19 Oct: today's is not written yet
    assert store.get(FoBanListSource.path_for(D16)) is None


def test_a_ban_list_for_a_later_session_is_refused(tmp_path):
    with pytest.raises(LaterSession):
        ban_taker(LocalFolderStore(tmp_path)).take(D15)


class Recorder(ManifestRecorder):
    def __init__(self, outcome="manifest rows committed and pushed (1 file(s))"):
        self.outcome, self.commits = outcome, []

    def pending(self):
        return []

    def commit(self, what):
        self.commits.append(what)
        return self.outcome


def job(steps, recorder=None, alerts=None, out=None):
    alerts = alerts or DryRunAlertSender()
    return FoMastersJob(
        build_session_calendar(), steps, recorder or Recorder(), alerts, "RUN", ([] if out is None else out).append
    )


def ok(line):
    return lambda day: line


def fails(error):
    def run(day):
        raise error

    return run


def test_a_non_trading_day_takes_nothing_and_succeeds():
    out, recorder, called = [], Recorder(), []
    assert job([Step("ban list", called.append)], recorder, out=out).run(D17) == 0  # a Saturday
    assert out == [NOT_A_TRADING_DAY.format(day=D17)] and called == [] and recorder.commits == []


def test_every_step_runs_and_one_alert_names_every_failure():
    out, alerts, recorder = [], DryRunAlertSender(), Recorder()
    steps = [Step("ban list", fails(StaleCopy("stale: 16 Oct"))), Step("lot sizes", ok("taken")),
             Step("lot sizes again", fails(StepFailed("not served")))]  # fmt: skip
    assert job(steps, recorder, alerts, out).run(D16) == 1
    assert out[:3] == ["ban list: failed: stale: 16 Oct", "lot sizes: ok: taken", "lot sizes again: failed: not served"]
    assert recorder.commits == ["fo-masters 2026-10-16"]  # the rows of what was taken are still committed
    assert (
        len(alerts.would_send) == 1
        and "ban list: failed" in alerts.would_send[0]
        and "lot sizes again: failed" in alerts.would_send[0]
    )
    assert "RUN" in alerts.would_send[0]


def test_all_steps_ok_sends_no_alert():
    alerts = DryRunAlertSender()
    assert job([Step("ban list", ok("taken")), Step("lot sizes", ok("taken"))], alerts=alerts).run(D16) == 0
    assert alerts.would_send == []


def test_manifest_rows_not_committed_is_a_failure():
    alerts = DryRunAlertSender()
    recorder = Recorder("manifest rows NOT committed: push failed: rejected. Commit research/data/manifests/ by hand")
    assert job([Step("lot sizes", ok("taken"))], recorder, alerts).run(D16) == 1
    assert "NOT committed" in alerts.would_send[0]


def test_a_file_nse_does_not_serve_is_a_failure_not_news():
    with pytest.raises(StepFailed):
        taken(NOT_SERVED.format(path="nse/derivatives/fo-lot-sizes/2026/10/16/fo_mktlots.csv"))
    assert taken("x: archived (10 bytes)") == "x: archived (10 bytes)"


def test_the_alert_points_to_the_actions_run():
    env = {"GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": "o/r", "GITHUB_RUN_ID": "7"}
    assert run_location(env) == "https://github.com/o/r/actions/runs/7" and run_location({}) == NO_RUN_URL
