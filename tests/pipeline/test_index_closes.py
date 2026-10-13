"""Story O6 for G3: the daily index-close job appends each new session's NIFTY 50 and India VIX closes to the warm-up
file, never rewriting a row, stops loudly at a session without its file, and the panel reader then gives those days
as closes-only sessions after the panel's last day."""

from datetime import date

import pytest

from fno.pipeline.index_closes import IndexCloseAppender
from fno.research_data.panel_reader import SessionClose, read_nifty_panel
from fno.research_data.panel_store import WARMUP_FILE
from fno.research_data.warmup_closes import WarmupConflict, append_warmup_rows
from tests.pipeline.fakes import RecordingAlerts
from tests.test_warmup_closes import CALENDAR, closes_file, index_files, small_panel  # weekdays are sessions

PANEL_DAY = ("2019-01-01", "regular", 1.0, 1.0, "f", "0" * 64)


def _appender(folder, files, alerts):
    return IndexCloseAppender(index_files(files), CALENDAR, folder, alerts, lambda line: None)


def test_new_sessions_are_appended_once_and_the_reader_shows_them_after_the_panel(tmp_path):
    small_panel(tmp_path, [PANEL_DAY])
    files = {date(2019, 1, 2): closes_file("10792.5", "16.2"), date(2019, 1, 3): closes_file("10672.25", "16.9")}
    alerts = RecordingAlerts()
    assert _appender(tmp_path, files, alerts).run(date(2019, 1, 3)) == 0
    before = (tmp_path / WARMUP_FILE).read_text()
    assert _appender(tmp_path, files, alerts).run(date(2019, 1, 3)) == 0  # nothing new: the file is unchanged
    assert (tmp_path / WARMUP_FILE).read_text() == before and alerts.lines == []
    sessions = read_nifty_panel(tmp_path).sessions
    assert sessions[-2:] == (
        SessionClose(date(2019, 1, 2), "regular", 10792.5, 16.2),
        SessionClose(date(2019, 1, 3), "regular", 10672.25, 16.9),
    )


def test_a_session_without_its_file_stops_keeps_the_earlier_days_and_alerts(tmp_path):
    small_panel(tmp_path, [PANEL_DAY])
    alerts = RecordingAlerts()
    files = {date(2019, 1, 2): closes_file(), date(2019, 1, 4): closes_file()}  # 3 Jan not archived yet
    assert _appender(tmp_path, files, alerts).run(date(2019, 1, 4)) == 1
    days = [line.split(",")[0] for line in (tmp_path / WARMUP_FILE).read_text().splitlines()[1:]]
    assert days == ["2019-01-01", "2019-01-02"]  # never jumps over a missing session
    assert len(alerts.lines) == 1 and "stopped at 2019-01-03" in alerts.lines[0]


def test_rows_are_never_rewritten(tmp_path):
    small_panel(tmp_path, [PANEL_DAY])
    with pytest.raises(WarmupConflict, match="never rewritten"):
        append_warmup_rows(tmp_path, [("2019-01-01", "regular", 2.0, 1.0, "f", "0" * 64)])
    assert append_warmup_rows(tmp_path, [PANEL_DAY]) == 0  # the same row again changes nothing


def test_a_read_of_earlier_years_gets_no_later_closes(tmp_path):
    small_panel(tmp_path, [PANEL_DAY, ("2019-01-02", "regular", 3.0, 3.0, "f", "0" * 64)])
    assert [s.day for s in read_nifty_panel(tmp_path, years=[2018]).sessions] == []
