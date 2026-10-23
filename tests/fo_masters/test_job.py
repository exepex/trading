"""A20a: the ban list is filed under the trade date it names when that is the run day's session or the next one
(boundaries: today, the next session across a weekend, the previous session, two sessions ahead); on a trading day a
run that ends without today's list fails as stale; on other days only the ban list is taken; every step runs even
after one fails, and ONE alert names every failure (exit 1)."""

from datetime import date
from pathlib import Path

import pytest

from fno.alerts.dry_run import DryRunAlertSender
from fno.alerts.run_location import NO_RUN_URL, run_location
from fno.fo_masters.job import NOT_A_TRADING_DAY, FoMastersJob, Step, StepFailed, ban_list_step, taken
from fno.storage.content_checks import COVERED_SESSION, VALIDATORS
from fno.storage.manifest_commit import ManifestRecorder
from fno.storage.raw_store import LocalFolderStore
from fno.storage.session_filed_taker import CurrentSessionTaker, LaterSession, StaleCopy
from fno.storage.snapshot_source import FoBanListSource
from fno.storage.snapshot_taker import NOT_SERVED, TAKEN
from fno.storage.trading_days import is_trading_day, next_trading_day
from fno.storage.wiring import build_session_calendar

BAN_16 = (Path(__file__).parents[1] / "fixtures" / "nse" / "fo_masters" / "fo_secban_16102026.csv").read_bytes()
D15, D16, D17, D19 = date(2026, 10, 15), date(2026, 10, 16), date(2026, 10, 17), date(2026, 10, 19)
CALENDAR = build_session_calendar()


def ban_for(day: date) -> bytes:
    return BAN_16.replace(b"16-OCT-2026", f"{day:%d-%b-%Y}".upper().encode())


class Serving:
    FILENAME, path_for = FoBanListSource.FILENAME, FoBanListSource.path_for

    def __init__(self, data):
        self.data = data

    def fetch(self, path):
        return self.data


def ban_taker(store, data=BAN_16) -> CurrentSessionTaker:
    source = FoBanListSource
    return CurrentSessionTaker(
        store, Serving(data), VALIDATORS[source], COVERED_SESSION[source], lambda day: next_trading_day(CALENDAR, day)
    )


def test_the_ban_list_is_filed_under_its_trade_date(tmp_path):
    store = LocalFolderStore(tmp_path)
    assert ban_taker(store).take(D16) == TAKEN.format(path=FoBanListSource.path_for(D16), size=len(BAN_16))
    assert FoBanListSource.path_for(D16) == "nse/derivatives/fo-ban-list/2026/10/16/fo_secban.csv"
    assert store.get(FoBanListSource.path_for(D16)) == BAN_16


def test_the_next_session_s_list_is_taken_across_a_weekend_under_its_own_date(tmp_path):
    store = LocalFolderStore(tmp_path)  # Friday 16 Oct, 18:45 IST: NSE already shows Monday 19 Oct's list
    ban_taker(store, ban_for(D19)).take(D16)
    assert store.get(FoBanListSource.path_for(D19)) == ban_for(D19) and store.get(FoBanListSource.path_for(D16)) is None
    ban_taker(store, ban_for(D19)).take(D17)  # Saturday: Monday is the next session too; the first copy is kept
    assert store.get(FoBanListSource.path_for(D19)) == ban_for(D19)


def test_a_ban_list_for_an_earlier_session_is_stale_and_nothing_is_written(tmp_path):
    store = LocalFolderStore(tmp_path)
    with pytest.raises(StaleCopy, match="stale"):
        ban_taker(store, ban_for(D15)).take(D16)  # NSE still serves 15 Oct's list on 16 Oct
    assert store.get(FoBanListSource.path_for(D15)) is None


def test_a_ban_list_two_sessions_ahead_is_refused(tmp_path):
    store = LocalFolderStore(tmp_path)
    with pytest.raises(LaterSession):
        ban_taker(store, ban_for(date(2026, 10, 20))).take(D16)  # 20 Oct is two sessions after 16 Oct
    assert store.get(FoBanListSource.path_for(date(2026, 10, 20))) is None


def ban_step(archived_days, line="x: archived (74 bytes)"):
    return ban_list_step(lambda day: line, lambda day: day in archived_days, lambda day: is_trading_day(CALENDAR, day))


def test_on_a_trading_day_a_run_without_today_s_list_is_stale_even_when_it_took_tomorrow_s():
    assert ban_step({D16})(D16) == "x: archived (74 bytes)"
    with pytest.raises(StepFailed, match="no ban list archived for today's session 2026-10-16"):
        ban_step({D19})(D16)  # the 18:45 run took Monday's list, but Friday's was never archived


def test_on_a_weekend_a_holiday_or_a_muhurat_only_day_no_stale_check_runs():
    for day in (D17, date(2026, 10, 2), date(2026, 11, 8)):  # Saturday; Gandhi Jayanti; Diwali muhurat (Sunday)
        assert not is_trading_day(CALENDAR, day) and ban_step(set())(day) == "x: archived (74 bytes)"
    assert is_trading_day(CALENDAR, D16)


def test_a_ban_list_nse_does_not_serve_is_a_failure():
    with pytest.raises(StepFailed):
        ban_step({D16}, NOT_SERVED.format(path="p"))(D16)


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


def test_a_non_trading_day_takes_only_the_every_day_steps():
    out, recorder, called = [], Recorder(), []
    steps = [Step("ban list", lambda day: called.append("ban") or "taken", every_day=True),
             Step("lot sizes", lambda day: called.append("lots") or "taken")]  # fmt: skip
    assert job(steps, recorder, out=out).run(D17) == 0  # a Saturday
    assert (
        out[0] == NOT_A_TRADING_DAY.format(day=D17)
        and called == ["ban"]
        and recorder.commits == ["fo-masters 2026-10-17"]
    )


def test_a_trading_day_takes_every_step():
    called = []
    steps = [Step("ban list", lambda day: called.append("ban") or "taken", every_day=True),
             Step("lot sizes", lambda day: called.append("lots") or "taken")]  # fmt: skip
    assert job(steps).run(D16) == 0 and called == ["ban", "lots"]


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


def test_a_drive_network_error_is_a_named_failure_and_the_rows_are_still_committed():
    import requests

    out, alerts, recorder = [], DryRunAlertSender(), Recorder()
    steps = [
        Step("ban list", fails(requests.ConnectionError("drive down")), every_day=True),
        Step("lot sizes", ok("t")),
    ]
    assert job(steps, recorder, alerts, out).run(D16) == 1
    assert "ban list: failed: drive down" in out and "lot sizes: ok: t" in out and recorder.commits
    assert "drive down" in alerts.would_send[0]


def test_a_list_for_the_trading_day_after_a_muhurat_session_is_taken(tmp_path):
    friday, monday = date(2026, 11, 6), date(2026, 11, 9)  # Sunday 8 Nov is a muhurat-only session
    assert CALENDAR.next_session(friday) == date(2026, 11, 8) and next_trading_day(CALENDAR, friday) == monday
    store = LocalFolderStore(tmp_path)
    ban_taker(store, ban_for(monday)).take(friday)
    assert store.get(FoBanListSource.path_for(monday)) == ban_for(monday)


def test_today_s_list_is_taken_on_the_calendar_s_last_day(tmp_path):
    last = date(2026, 12, 31)  # the calendar ends here: the next trading day is unknown, and not needed
    store = LocalFolderStore(tmp_path)
    ban_taker(store, ban_for(last)).take(last)
    assert store.get(FoBanListSource.path_for(last)) == ban_for(last)
