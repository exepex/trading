"""LM1 round 2a: what the monitor reads about a mark (A16's ledger for the last usable mark, the document's level only
on a usable status, NSE's previous close), the heartbeat, and "monitor silent" (criterion 9: only while positions
are open, inside A16's watched hours, with the story's exact text); the alert records are git-ignored."""

from __future__ import annotations

import subprocess
from datetime import timedelta

from fno.config import ROOT
from fno.intraday.heartbeat import Heartbeat
from fno.monitor.heartbeat import SILENT_TEXT, MonitorHeartbeat, MonitorSilence
from fno.monitor.mark_reader import MarkReader
from fno.monitor.mark_rows import MarkRow
from fno.research_data.calendar import load_session_calendar
from fno.storage.wiring import CALENDAR_FILE

from .fixtures import DAY, at, settings
from .observer_fakes import Closes, document, ledger_row


def reader(tmp_path, statuses: dict[str, str]) -> MarkReader:
    from fno.intraday.ledger import SlotLedger

    ledger = SlotLedger(tmp_path)
    ledger.append(DAY, [ledger_row(DAY, hhmm, status) for hhmm, status in statuses.items()])
    return MarkReader(ledger, Closes(24900.0), load_session_calendar(CALENDAR_FILE), settings())


def test_the_last_usable_mark_comes_from_the_ledger_incomplete_included(tmp_path):
    read = reader(tmp_path, {"10:00": "good", "10:15": "incomplete", "10:30": "missed"})
    mark = read.read(DAY, at("10:30"), None, "missed")
    assert (mark.last_good_at, mark.index_level, mark.previous_close) == (at("10:15"), None, 24900.0)
    assert mark.clock_skew_seconds == 0.4


def test_a_usable_mark_with_its_document_gives_its_level_and_resets_the_clock(tmp_path):
    mark = reader(tmp_path, {"10:30": "good"}).read(DAY, at("10:30"), document(25010.0), "good")
    assert (mark.index_level, mark.last_good_at) == (25010.0, at("10:30"))


def test_a_good_row_without_this_runs_document_does_not_reset_the_clock(tmp_path):
    mark = reader(tmp_path, {"10:00": "good", "10:30": "good"}).read(DAY, at("10:30"), None, "good")
    assert (mark.index_level, mark.last_good_at) == (None, at("10:00"))


def test_incomplete_is_not_usable_when_the_setting_is_off(tmp_path):
    read = reader(tmp_path, {"10:30": "incomplete"})
    read.settings = settings(check_incomplete_marks=False)
    assert read.read(DAY, at("10:30"), document(25000.0), "incomplete").index_level is None


def beat(tmp_path, positions: int, finished):
    MonitorHeartbeat(Heartbeat(tmp_path)).beat(MarkRow(DAY, finished, finished, "good", True, positions))
    return MonitorSilence(Heartbeat(tmp_path), lambda day: True)


def test_silent_after_30_minutes_with_positions_open_with_the_story_text(tmp_path):
    silence = beat(tmp_path, 2, at("11:00"))
    assert not silence.check(at("11:30")).silent
    result = silence.check(at("11:31"))
    assert result.silent and (result.minutes, result.positions) == (31, 2)
    assert result.line == SILENT_TEXT.format(minutes=31, positions=2)


def test_never_silent_with_no_position_or_outside_watched_hours(tmp_path):
    assert not beat(tmp_path, 0, at("11:00")).check(at("13:00")).silent
    assert not beat(tmp_path, 2, at("15:30")).check(at("15:30") + timedelta(minutes=45)).silent


def test_the_alert_records_folder_is_git_ignored():
    name = "journal/monitor/alerts/2026/2026-10-16/1030.csv"
    ignored = subprocess.run(["git", "check-ignore", "-q", name], cwd=ROOT)
    assert ignored.returncode == 0
