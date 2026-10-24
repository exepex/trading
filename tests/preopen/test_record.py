"""Criteria 4-6 end to end (the desk in `desk.py`). No value reaches a committed path, an O10 row or an alert."""

from __future__ import annotations

import requests

from fno.intraday.candle_source import CandleCallFailed
from fno.preopen.parts import FO_PREOPEN_URL, GIFT_URL
from fno.research_data.calendar import CalendarError
from fno.storage.raw_store import LocalFolderStore

from .desk import VALUES, Committer, Desk, Response
from .fixtures import DAY, candles, gift, ist


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
    assert desk.out[-1] == "open check: 0 checked, 0 waiting for NSE's file" and desk.sender.sent == []
    assert "pre-open recorded" in desk.out  # the capture's line, before the open check's (A22d)
    assert [c.calls for c in desk.committers] == [["pre-open 2026-10-22"] * 2] * 2  # the capture's, then the check's
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


def test_gift_gets_its_own_file_pushed_when_its_part_ends_for_the_0850_edition(tmp_path):
    desk = Desk(tmp_path)
    assert desk.recorder().record(DAY) == 0
    row = desk.gift_row()
    assert (row["date"], row["gift_status"], row["gift_seen_at"], row["gift_level"], row["gift_contracts"]) == (
        "2026-10-22", "ok", "08:40:00", "1234.5", "4321")  # fmt: skip
    assert desk.early.calls == ["pre-open gift 2026-10-22"] and desk.early.at == [ist(8, 40)]  # before 08:42
    assert (desk.root / "receipts/data/preopen/gift/2026/10/2026-10-22.csv.sha256").is_file()
    assert "receipts committed and pushed (2 file(s))" in desk.out


def test_a_gift_that_never_freshens_is_written_with_its_status_and_no_value(tmp_path):
    desk = Desk(tmp_path, nse={GIFT_URL: gift("22-Oct-2026 07:00")})
    desk.recorder().record(DAY)
    row = desk.gift_row()
    assert (row["gift_status"], row["gift_level"]) == ("incomplete", "") and row["gift_detail"].startswith("stale")
    assert desk.early.at == [ist(8, 44, 59)]  # pushed after the window's last read, still before 08:50


def test_an_early_push_that_fails_is_named_in_the_alert(tmp_path):
    desk = Desk(tmp_path)
    desk.early.outcome = "receipts NOT committed: push failed: rejected. Commit receipts/ by hand"
    assert desk.recorder().record(DAY) == 1
    assert "gift file commit failed: receipts NOT committed" in desk.sender.sent[0]
    assert not any(v in desk.sender.sent[0] for v in VALUES)


def test_a_second_run_finds_the_gift_file_taken(tmp_path):
    Desk(tmp_path).recorder().record(DAY)
    late = Desk(tmp_path, start=ist(9, 30), nse={GIFT_URL: gift("22-Oct-2026 09:29")})
    late.recorder().record(DAY)
    assert "gift file taken" in late.sender.sent[0] and late.gift_row()["gift_status"] == "ok"
    assert late.early.calls == []  # nothing new to push
