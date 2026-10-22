"""Criterion 7 (back-fill): one post per month at least 10 s apart, one retry only, resume, rows in the table, and no
NSDL value in a committed path, a printed line or an alert."""

from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime

import pytest

from fno.flow_history import cli
from fno.flow_history.nsdl_backfill import NsdlArchiveForm, NsdlBackfill, NsdlUnavailable
from fno.flow_history.table import COLUMNS
from fno.storage.data_store import DataStore
from fno.storage.part_table import PartTable
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder
from fno.storage.trading_days import next_trading_day
from fno.storage.wiring import build_session_calendar

from .nsdl_pages import page

JAN, FEB = date(2019, 1, 31), date(2019, 2, 28)
PAGES = {JAN: page("31-Jan-2019", ("01-Jan-2019", "02-Jan-2019")), FEB: page("28-Feb-2019", ("01-Feb-2019",))}
VALUES = ("16.0", "13.0", "11.1111")
CALENDAR = build_session_calendar()  # NSE's real 2019 sessions


def _next(day: date) -> date:
    return next_trading_day(CALENDAR, day)


class Clock:
    def __init__(self):
        self.now, self.slept = 0.0, []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


class Form:
    def __init__(self, answers: dict, clock: Clock):
        self.answers, self.clock, self.posts, self.forgotten = answers, clock, [], 0

    def month(self, up_to):
        self.posts.append((up_to, self.clock.now))
        answer = self.answers[up_to]
        outcome = answer.pop(0) if isinstance(answer, list) else answer
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def forget(self):
        self.forgotten += 1


class Desk:
    def __init__(self, tmp_path, answers, run_id="run-1"):
        self.clock, self.drive = Clock(), LocalFolderStore(tmp_path / "drive")
        self.receipts = ReceiptFolder(tmp_path / "receipts")
        store = DataStore(self.drive, "data", self.receipts, "flow-history", run_id,
                          clock=lambda: datetime(2026, 10, 22, tzinfo=UTC))  # fmt: skip
        self.form = Form(answers, self.clock)
        self.backfill = NsdlBackfill(self.form, store, self.receipts, PartTable(store, "flows/history/nsdl-fpi",
                                     COLUMNS), _next, self.clock.sleep, self.clock.monotonic)  # fmt: skip

    def table_rows(self) -> list[dict]:
        rows = []
        for path in sorted(self.drive.checksums("data/flows/history/nsdl-fpi/2019/01")):
            rows += csv.DictReader(io.StringIO(self.drive.get(f"data/flows/history/nsdl-fpi/2019/01/{path}").decode()))
        return rows


def test_one_post_per_month_at_least_10_s_apart_and_rows_in_the_table(tmp_path):
    desk = Desk(tmp_path, dict(PAGES))
    result = desk.backfill.run([JAN, FEB])
    assert result.saved == [JAN, FEB] and result.failed == {} and result.rows == (2 + 1) * (7 * 4 + 1)
    times = [at for _, at in desk.form.posts]
    assert len(times) == 2 and times[1] - times[0] >= 10  # the story's gentle pace, not the constant itself
    assert desk.drive.get("data/flows/nsdl/raw/2019-01.html") == PAGES[JAN].encode()
    row = desk.table_rows()[0]
    assert (row["session"], row["dataset"], row["available_from"], row["rewritten"], row["last_modified"]) == (
        "2019-01-01", "nsdl/fpi/daily-trends", "2019-01-02", "publication_time_unknown", "")  # fmt: skip
    assert (row["series"], row["measure"], row["value"]) == ("Equity:Stock Exchange", "gross_purchases_crores", "10.0")


def test_a_month_that_fails_twice_is_listed_and_never_tried_a_third_time(tmp_path):
    desk = Desk(
        tmp_path, {JAN: [NsdlUnavailable("HTTP 503"), NsdlUnavailable("HTTP 503"), PAGES[JAN]], FEB: PAGES[FEB]}
    )
    result = desk.backfill.run([JAN, FEB])
    assert result.failed == {JAN: "HTTP 503"} and result.saved == [FEB]
    assert [m for m, _ in desk.form.posts] == [JAN, JAN, FEB] and desk.form.forgotten == 2
    assert all(b - a >= 10 for (_, a), (_, b) in zip(desk.form.posts, desk.form.posts[1:]))


def test_one_failure_then_success_is_saved(tmp_path):
    desk = Desk(tmp_path, {JAN: ["<html>busy</html>", PAGES[JAN]]})
    assert desk.backfill.run([JAN]).saved == [JAN] and len(desk.form.posts) == 2


def test_a_resumed_pass_skips_months_already_saved_and_entered(tmp_path):
    Desk(tmp_path, dict(PAGES)).backfill.run([JAN])
    later = Desk(tmp_path, dict(PAGES), run_id="run-2")
    result = later.backfill.run([JAN, FEB])
    assert result.skipped == [JAN] and result.saved == [FEB] and [m for m, _ in later.form.posts] == [FEB]


def test_month_ends_from_january_2019_through_a_month():
    ends = cli.month_ends(date(2019, 1, 31), date(2019, 3, 1))
    assert ends == [date(2019, 1, 31), date(2019, 2, 28), date(2019, 3, 31)]
    assert len(cli.month_ends(date(2019, 1, 31), date(2026, 9, 30))) == 93


ACTIONS_RUN = {"GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": "exepex/trading", "GITHUB_RUN_ID": "7"}


# The alert names where the run's lines are (fno/alerts/run_location.py), read from the environment: each case sets
# it in full, so the test means the same locally and inside GitHub Actions, which sets these variables itself.
@pytest.mark.parametrize(
    ("environment", "where"),
    [
        ({}, "the command's output (not a GitHub Actions run)"),
        (ACTIONS_RUN, "https://github.com/exepex/trading/actions/runs/7"),
    ],
)
def test_the_command_prints_and_alerts_counts_and_months_only(tmp_path, monkeypatch, environment, where):
    for name in ACTIONS_RUN:
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    desk = Desk(tmp_path, {JAN: [NsdlUnavailable("HTTP 503"), NsdlUnavailable("HTTP 503")], FEB: PAGES[FEB]})
    sent, lines = [], []

    class Sender:
        def send(self, text):
            sent.append(text)
            return "alert sent to #fno-desk"

    class Committer:
        def commit(self, what):
            return "receipts committed and pushed (2 file(s))"

    import fno.flow_history.wiring as wiring
    import fno.storage.data_wiring as data_wiring

    monkeypatch.setattr(wiring, "build_nsdl_backfill", lambda: desk.backfill)
    monkeypatch.setattr(wiring, "build_alerts", Sender)
    monkeypatch.setattr(data_wiring, "build_receipt_committer", Committer)
    args = type("Args", (), {"through": FEB})()
    assert cli.cmd_nsdl_backfill(args, out=lines.append) == 1
    assert lines[0].startswith("nsdl-backfill: 1 month(s) saved (29 rows, 0 with no reporting date)")
    assert sent == [f"Omenix F&O NSDL FPI back-fill: 1 month(s) failed twice: 2019-01; see {where}"]
    printed = "\n".join(lines + sent)
    committed = "\n".join(p.read_text() for p in (tmp_path / "receipts").rglob("*") if p.is_file())
    assert not any(value in printed or value in committed for value in VALUES)


def test_the_form_reads_its_state_once_and_again_only_after_a_failure():
    class Session:
        def __init__(self):
            self.calls = []

        def get(self, url, timeout):
            self.calls.append("get")
            fields = "".join(f'<input id="{n}" value="v{n}" />' for n in
                             ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"))  # fmt: skip
            return type("R", (), {"status_code": 200, "text": fields})()

        def post(self, url, timeout, data):
            self.calls.append(("post", data["hdnDate"], data["__VIEWSTATE"]))
            return type("R", (), {"status_code": 200, "text": "page"})()

    session = Session()
    form = NsdlArchiveForm(session)
    form.month(JAN), form.month(FEB)
    form.forget()
    form.month(JAN)
    assert session.calls == ["get", ("post", "31-Jan-2019", "v__VIEWSTATE"), ("post", "28-Feb-2019", "v__VIEWSTATE"),
                             "get", ("post", "31-Jan-2019", "v__VIEWSTATE")]  # fmt: skip
