"""Criteria 4-6 end to end: the real adapters over a fake NSE session and fake Groww candles, O9's data store over a
folder, O10's error log, fake committers and alerts. No value reaches a committed path, an O10 row or an alert."""

from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime

import requests

from fno.alerts.sender import SENT
from fno.health.capture_errors import CaptureErrorLog
from fno.intraday.candle_source import CandleAnswer, CandleCallFailed
from fno.preopen.parts import FO_PREOPEN_URL, GIFT_URL, GrowwIndexPreopen, NseGiftNifty, NsePreopenList
from fno.preopen.record import PreopenRecorder
from fno.preopen.run import PreopenRun
from fno.research_data.calendar import CalendarError
from fno.storage.data_store import DataStore
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

from .fakes import FakeClock
from .fixtures import DAY, candles, fo_list, gift, ist

ROUTINE_START = ist(8, 36)
VALUES = ("1234.5", "4321", "5555.5", "101.5")


class Response:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content, self.status_code = content, status_code


class NseSession:
    def __init__(self, answers: dict):
        self.answers = answers  # url -> bytes, or a callable of the clock's time

    def get(self, url, timeout):
        answer = self.answers[url]
        if isinstance(answer, Exception):
            raise answer
        return Response(answer) if isinstance(answer, bytes) else answer


class Candles:
    def __init__(self, clock, raw: bytes | Exception):
        self.clock, self.raw = clock, raw

    def minute_candles(self, day: date) -> CandleAnswer:
        if isinstance(self.raw, Exception):
            raise self.raw
        return CandleAnswer("1m", day, day, self.raw, [], self.clock.now(), self.clock.now())


class Committer:
    def __init__(self, outcome="committed"):
        self.outcome, self.calls = outcome, []

    def commit(self, what):
        self.calls.append(what)
        return self.outcome


class Sender:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return SENT


class Desk:
    """One planted morning: a repository folder, a Drive folder and the parts' answers."""

    def __init__(self, tmp_path, start=ROUTINE_START, nse=None, nifty=None, trading=True, clock_warning=""):
        self.root, self.clock = tmp_path / "repo", FakeClock(start)
        self.drive = LocalFolderStore(tmp_path / "drive")
        answers = {GIFT_URL: gift(), FO_PREOPEN_URL: fo_list()} | (nse or {})
        session = NseSession(answers)
        self.parts = [NseGiftNifty(session, self.clock.now), NsePreopenList(session, self.clock.now),
                      GrowwIndexPreopen("nifty", Candles(self.clock, candles() if nifty is None else nifty)),
                      GrowwIndexPreopen("banknifty", Candles(self.clock, candles(close_0909=6666.5)))]  # fmt: skip
        self.errors = CaptureErrorLog(self.root / "research/ops/capture_errors.csv")
        self.committers, self.sender, self.out = [Committer(), Committer()], Sender(), []
        self.trading, self.clock_warning = trading, clock_warning

    def recorder(self) -> PreopenRecorder:
        store = DataStore(self.drive, "data", ReceiptFolder(self.root / "receipts"), "preopen", "run-1",
                          clock=lambda: datetime(2026, 10, 22, 3, 41, tzinfo=UTC))  # fmt: skip

        def run(done):
            return PreopenRun(self.parts, self.clock.now, self.clock.sleep, done)

        return PreopenRecorder(self._trading, run, store, self.errors, self.committers, self.sender,
                               lambda: self.clock_warning, self.out.append)  # fmt: skip

    def _trading(self, day):
        if isinstance(self.trading, Exception):
            raise self.trading
        return self.trading

    def day_row(self) -> dict:
        data = self.drive.get("data/preopen/day/2026/10/2026-10-22.csv")
        return next(csv.DictReader(io.StringIO(data.decode())))

    def committed_text(self) -> str:
        return "\n".join(p.read_text() for p in self.root.rglob("*") if p.is_file())


def test_a_good_morning_saves_four_answers_and_the_day_row_commits_and_stays_quiet(tmp_path):
    desk = Desk(tmp_path)
    assert desk.recorder().record(DAY) == 0
    row = desk.day_row()
    assert [row[f"{p}_status"] for p in ("gift", "fo_list", "nifty", "banknifty")] == ["ok"] * 4
    assert (row["gift_level"], row["fo_with_iep"], row["nifty_preopen"], row["banknifty_preopen"]) == (
        "1234.5", "2", "5555.5", "6666.5")  # fmt: skip
    assert (row["gift_seen_at"], row["nifty_seen_at"], row["clock"]) == ("08:40:00", "09:10:00", "ok")
    raw = sorted(desk.drive.checksums("data/preopen/raw/2026/10/22"))
    assert raw == ["banknifty_091000.json", "fo_list_090830.json", "gift_084000.json", "nifty_091000.json"]
    assert desk.out[-1] == "pre-open recorded" and desk.sender.sent == []
    assert [c.calls for c in desk.committers] == [["pre-open 2026-10-22"]] * 2
    assert (desk.root / "receipts/data/preopen/day/2026/10/2026-10-22.csv.sha256").is_file()
    assert desk.errors.rows() == [] and not any(v in desk.committed_text() for v in VALUES)


def test_problems_give_one_alert_one_o10_row_each_and_no_values(tmp_path):
    desk = Desk(tmp_path, nse={GIFT_URL: gift("22-Oct-2026 07:00")}, nifty=candles(count=9), clock_warning="slack: 7 s")
    assert desk.recorder().record(DAY) == 1
    [alert] = desk.sender.sent
    assert alert.startswith("A22 pre-open capture 2026-10-22: clock warning: slack: 7 s; gift incomplete: stale")
    assert "nifty incomplete: no 09:09 candle yet" in alert and not any(v in alert for v in VALUES)
    assert [(e.step, e.kind) for e in desk.errors.rows()] == [("clock", "warning"), ("gift", "incomplete"),
                                                               ("nifty", "incomplete")]  # fmt: skip
    row = desk.day_row()
    assert (row["gift_status"], row["gift_level"], row["nifty_preopen"], row["banknifty_status"]) == (
        "incomplete", "", "", "ok")  # fmt: skip
    assert row["gift_reads"] == "11" and not any(v in desk.committed_text() for v in VALUES)


def test_a_part_that_never_answers_is_failed_and_has_no_raw_file(tmp_path):
    desk = Desk(tmp_path, nse={FO_PREOPEN_URL: requests.ConnectionError("x")},
                nifty=CandleCallFailed("Groww 1m 2026-10-22..2026-10-22: Timeout"))  # fmt: skip
    assert desk.recorder().record(DAY) == 1
    assert "fo_list failed: NSE: ConnectionError" in desk.sender.sent[0]
    assert "nifty failed: Groww 1m 2026-10-22..2026-10-22: Timeout" in desk.sender.sent[0]
    assert sorted(desk.drive.checksums("data/preopen/raw/2026/10/22")) == ["banknifty_091000.json", "gift_084000.json"]


def test_an_http_refusal_is_a_failed_read(tmp_path):
    desk = Desk(tmp_path, nse={GIFT_URL: Response(b"denied", 403)})
    desk.recorder().record(DAY)
    assert "gift failed: NSE: HTTP 403" in desk.sender.sent[0]


def test_a_second_run_finds_the_day_row_taken_and_keeps_the_first(tmp_path):
    Desk(tmp_path).recorder().record(DAY)
    late = Desk(tmp_path, start=ist(9, 30), nse={GIFT_URL: gift("22-Oct-2026 09:29")})
    assert late.recorder().record(DAY) == 1
    assert "day row taken" in late.sender.sent[0] and "gift late: seen 09:30:00" in late.sender.sent[0]
    assert late.day_row()["gift_status"] == "ok"  # the on-time run's row stands


def test_a_day_that_is_not_a_trading_day_reads_nothing(tmp_path):
    desk = Desk(tmp_path, trading=False)
    assert desk.recorder().record(DAY) == 0
    assert desk.out == ["not a trading day"] and desk.clock.slept == [] and desk.sender.sent == []


def test_a_calendar_that_cannot_answer_stops_with_one_alert_and_row(tmp_path):
    desk = Desk(tmp_path, trading=CalendarError("no rows for the years [2027]"))
    assert desk.recorder().record(DAY) == 1
    assert desk.sender.sent == ["A22 pre-open capture 2026-10-22: calendar stopped: no rows for the years [2027]"]
    assert [e.kind for e in desk.errors.rows()] == ["stopped"]


def test_a_commit_that_fails_is_named_in_the_alert(tmp_path):
    desk = Desk(tmp_path)
    desk.committers[1] = Committer("receipts NOT committed: push failed: rejected. Commit receipts/ by hand")
    assert desk.recorder().record(DAY) == 1
    assert "commit failed: receipts NOT committed" in desk.sender.sent[0]


def test_drive_down_names_each_unsaved_file(tmp_path):
    desk = Desk(tmp_path)

    class DownDrive(LocalFolderStore):
        def put(self, path, data):
            raise RuntimeError("Drive down")

    desk.drive = DownDrive(tmp_path / "drive")
    assert desk.recorder().record(DAY) == 1
    alert = desk.sender.sent[0]
    assert "gift raw not saved to Drive: RuntimeError" in alert and "day row not saved to Drive: RuntimeError" in alert
    assert not (desk.root / "receipts").exists()
