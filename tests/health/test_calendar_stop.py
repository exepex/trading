"""Story O8c (response 239 item 4, judge 246): any command stopped by NSE's calendar prints one named line and exits 1
without posting (the gap is announced by O8b and the health check; the workflow's own line points to the log); the
index-closes workflow posts exactly one line per failing run, through the append step's `posted` output."""

from datetime import date

import pytest
import yaml

from fno.cli import main
from fno.config import ROOT
from fno.health.calendar_stop import CALENDAR_STOP, calendar_stop, command_name
from fno.research_data.calendar import CalendarError

GAP = CalendarError("2027-01-01 is outside the calendar (2017-01-01 to 2026-12-31): add every row of NSE's 2027 ...")


class Sender:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


@pytest.fixture
def sender(monkeypatch):
    found = Sender()
    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: found)
    return found


@pytest.mark.parametrize(
    ("argv", "name"),
    [(["pipeline", "index-closes", "--to", "2027-01-04"], "pipeline index-closes"),
     (["data-librarian", "index-close", "--from", "x"], "data-librarian index-close"), (["--help"], "fno")],
)  # fmt: skip
def test_the_command_is_named_without_its_options(argv, name):
    assert command_name(argv) == name


def test_one_named_line_printed_never_posted_and_exit_1(sender):
    lines = []
    assert calendar_stop("margins nse-span", GAP, lines.append) == 1
    assert lines == [CALENDAR_STOP.format(command="margins nse-span", reason=GAP)] and sender.sent == []


def test_the_real_index_closes_job_on_a_2027_day_prints_the_calendars_own_words(sender, monkeypatch, tmp_path, capsys):
    """Before O8c this died with a traceback and the workflow blamed Drive. The real job and the real calendar, built
    without Drive: the calendar stops it before any index file is read. Nothing is posted (judge 246)."""
    from fno.pipeline.index_closes import IndexCloseAppender
    from fno.research_data.warmup_closes import WARMUP_FILE
    from fno.storage.wiring import build_session_calendar

    (tmp_path / WARMUP_FILE).write_text(
        "date,session,underlying,vix,index_file,index_sha256\n2026-12-31,regular,1,1,f,s\n"
    )
    job = IndexCloseAppender(None, build_session_calendar(), tmp_path, sender, log=lambda line: None)
    monkeypatch.setattr("fno.pipeline.wiring.build_index_close_appender", lambda: job)
    assert main(["pipeline", "index-closes", "--to", "2027-01-04"]) == 1
    printed = capsys.readouterr().out
    assert printed.startswith("Omenix F&O `pipeline index-closes` stopped: 2027-01-01 is outside the calendar")
    assert "add every row of NSE's 2027 holiday circular" in printed and sender.sent == []


def test_a_command_that_handles_the_calendar_itself_is_not_posted_twice(sender, monkeypatch):
    def handles_it(args):
        try:
            raise GAP
        except CalendarError as error:
            sender.send(f"its own line: {error}")
            return 1

    monkeypatch.setattr("fno.pipeline.cli.cmd_pipeline_index_closes", handles_it)
    assert main(["pipeline", "index-closes"]) == 1 and sender.sent == [f"its own line: {GAP}"]


def test_any_other_error_is_not_turned_into_a_calendar_line(sender, monkeypatch):
    def breaks(args):
        raise ZeroDivisionError

    monkeypatch.setattr("fno.pipeline.cli.cmd_pipeline_index_closes", breaks)
    with pytest.raises(ZeroDivisionError):
        main(["pipeline", "index-closes", "--to", date(2026, 10, 16).isoformat()])
    assert sender.sent == []


def test_index_closes_names_no_single_cause_and_posts_one_line_per_failing_run():
    """panel-days.yml is frozen by protocol v3 (FREEZE_v3.md): left as it is; its Python step prints the named line."""
    text = (ROOT / ".github" / "workflows" / "index-closes.yml").read_text(encoding="utf-8")
    steps = yaml.safe_load(text)["jobs"]["closes"]["steps"]
    assert "the Drive archive step failed" not in text and "(Drive, NSE or the calendar: its log names it)" in text
    assert steps[-1]["if"] == ("${{ failure() && steps.librarian.outcome == 'success' && "
                               "steps.append.outputs.posted != 'true' }}")  # fmt: skip


def test_the_index_close_job_is_wired_with_a_sender_that_records_posted(monkeypatch):
    from fno.alerts.step_output import StepOutputAlerts
    from fno.pipeline import wiring

    monkeypatch.setattr(wiring, "_project_drive", lambda env: None)
    monkeypatch.setattr(wiring, "drive_files", lambda *args: None)
    monkeypatch.setattr(wiring, "AreaStore", lambda *args: None)
    assert isinstance(wiring.build_index_close_appender().alerts, StepOutputAlerts)
