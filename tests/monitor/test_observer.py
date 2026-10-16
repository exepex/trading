"""LM1 round 2a, the observer end to end on fakes: criterion 2 (nothing to watch: only the row and the heartbeat),
criterion 7 (one handling per mark with Drive up, down and recovered; every alert recorded privately; a failed send is
retried at the next mark with its first record kept; no public file names a position, contract or price) and a failure
named by class in the row and the heartbeat."""

from __future__ import annotations

import csv
import io
import json
import re

import pytest

from fno.monitor.alert_records import ALERTS_FOLDER

from .fixtures import DAY, spread
from .observer_fakes import Desk

DANGER_POSITION = spread("T7", loss=8800.0)  # 88% of its maximum loss: one DANGER


def records(desk: Desk, hhmm: str) -> list[dict]:
    path = desk.drive.folder / ALERTS_FOLDER / f"{DAY:%Y}" / f"{DAY:%Y-%m-%d}" / f"{hhmm.replace(':', '')}.csv"
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")))) if path.is_file() else []


def public_text(desk: Desk) -> str:
    return "".join(p.read_text(encoding="utf-8") for p in sorted((desk.folder / "monitor").rglob("*")) if p.is_file())


def test_with_nothing_to_watch_only_the_row_and_heartbeat_are_written(tmp_path):
    desk = Desk(tmp_path)
    desk.mark(DAY, "10:30")
    (row,) = desk.rows.rows(DAY)
    assert (row["positions"], row["checked"], row["alerts_sent"], row["record"]) == ("0", "False", "0", "none")
    assert desk.sender.texts == [] and json.loads(desk.heartbeat.file.read_text())["positions"] == "0"


def test_a_danger_is_sent_recorded_privately_and_counted_publicly(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    desk.mark(DAY, "10:30")
    assert len(desk.sender.texts) == 1 and desk.sender.texts[0].startswith("F&O monitor: DANGER")
    (record,) = records(desk, "10:30")
    assert (record["state"], record["key"], record["trade_id"]) == ("sent", "loss_used:DANGER:T7", "T7")
    (row,) = desk.rows.rows(DAY)
    assert (row["checked"], row["positions"], row["alerts_sent"], row["record"]) == ("True", "1", "1", "ok")


def test_no_public_file_names_a_position_or_a_price(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    desk.mark(DAY, "10:30")
    text = public_text(desk)
    assert "T7" not in text and "Rs" not in text and not re.search(r"\b2[45],?\d{3}\b", text)
    assert "loss" not in text.lower()


def test_a_second_fire_for_a_handled_mark_sends_nothing(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    desk.mark(DAY, "10:30")
    desk.observer.after_mark(DAY, desk.clock.now, None, "good")
    assert len(desk.sender.texts) == 1 and len(desk.rows.rows(DAY)) == 1


def test_drive_down_still_sends_and_the_row_says_the_record_failed_then_no_resend(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    desk.drive.down = True
    desk.mark(DAY, "10:30")
    assert len(desk.sender.texts) == 1 and desk.rows.rows(DAY)[0]["record"] == "alert_record_failed"
    desk.drive.down = False
    desk.observer.after_mark(DAY, desk.clock.now, None, "good")  # a rerun after Drive recovers
    assert len(desk.sender.texts) == 1


def test_a_refused_send_is_recorded_failed_printed_and_sent_again_next_mark(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    desk.sender.refuse = True
    desk.mark(DAY, "10:30")
    assert records(desk, "10:30")[0]["state"] == "failed" and desk.rows.rows(DAY)[0]["alerts_failed"] == "1"
    assert desk.lines and desk.lines[0].startswith("alert NOT sent")
    desk.sender.refuse = False
    desk.mark(DAY, "10:45")
    assert records(desk, "10:45")[0]["state"] == "sent" and records(desk, "10:30")[0]["state"] == "failed"


def test_the_hourly_limit_holds_across_marks_through_the_private_history(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    for hhmm in ("10:30", "10:45", "11:15", "11:30"):
        desk.mark(DAY, hhmm)
    assert len(desk.sender.texts) == 2  # 10:30 and 11:30
    assert [r["state"] for r in records(desk, "10:45")] == ["held"]
    assert [r["held"] for r in desk.rows.rows(DAY)] == ["0", "1", "1", "0"]


def test_a_failure_is_named_in_the_row_and_heartbeat_and_raised(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    desk.source.positions = lambda *args: (_ for _ in ()).throw(KeyError("secret detail"))
    with pytest.raises(KeyError):
        desk.mark(DAY, "10:30")
    (row,) = desk.rows.rows(DAY)
    assert row["failure"] == "KeyError" and "secret" not in public_text(desk)


def test_an_unknown_previous_close_is_said_in_the_row(tmp_path):
    desk = Desk(tmp_path, [spread(loss=100.0)], closes=None)
    desk.mark(DAY, "10:30")
    assert desk.rows.rows(DAY)[0]["previous_close_known"] == "False"


def test_the_sending_row_is_in_drive_before_the_alert_goes_out(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    seen = []
    send = desk.sender.send
    desk.sender.send = lambda text: seen.append([r["state"] for r in records(desk, "10:30")]) or send(text)
    desk.mark(DAY, "10:30")
    assert seen == [["sending"]] and [r["state"] for r in records(desk, "10:30")] == ["sent"]


def test_marks_this_host_wrote_are_read_locally_and_others_from_drive(tmp_path):
    desk = Desk(tmp_path, [DANGER_POSITION])
    desk.mark(DAY, "10:30")
    calls = []
    get = desk.drive.get
    desk.drive.get = lambda path: calls.append(path) or get(path)
    desk.mark(DAY, "10:45")
    assert not any(p.endswith("1030.csv") for p in calls)  # its own 10:30 record: the local copy
    assert any(p.endswith("1015.csv") for p in calls)  # a mark it never wrote: Drive
    assert len(desk.sender.texts) == 1  # the 10:30 alert still holds the hourly limit
