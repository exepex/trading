"""O2's outage days, beyond the 3 pm quotes: A16's recorder and A12's archive print an alert Slack did not take with its
text ("alert NOT sent: <reason> | <text>"), never a bare "alert NOT sent" line; a sent alert prints its outcome once."""

from argparse import Namespace

from fno.alerts.output import announce
from fno.alerts.sender import SENT, NoAlertSender
from fno.daily.alerts import ReportedAlerts
from fno.filings.runs_cli import cmd_filings_archive
from fno.intraday.cli import cmd_intraday
from fno.research_data.calendar import CalendarError
from fno.storage.owner_token import DriveSignInRefused

DOWN = "Slack answered HTTP 503"


class SlackUp:
    def send(self, text):
        return SENT


class NoYears:
    def session_kind(self, day):
        raise CalendarError("no rows for 2027")


def _unsent(out):
    return [line for line in out.splitlines() if line.startswith("alert NOT sent")]


def test_announce_prints_a_sent_outcome_once_and_lets_the_reporter_print_an_unsent_one(capsys):
    announce(ReportedAlerts(SlackUp()), "x")
    announce(ReportedAlerts(NoAlertSender(DOWN)), "the alert text")
    assert capsys.readouterr().out.splitlines() == [SENT, f"alert NOT sent: {DOWN} | the alert text"]


def test_a16_calendar_stop_slack_did_not_take_is_printed_with_its_text(monkeypatch, capsys):
    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: NoAlertSender(DOWN))
    monkeypatch.setattr("fno.storage.wiring.build_session_calendar", lambda: NoYears())
    monkeypatch.setattr("fno.intraday.wiring.build_heartbeat", lambda: None)
    assert cmd_intraday(Namespace(intraday_cmd="heartbeat-check")) == 1
    [line] = _unsent(capsys.readouterr().out)
    assert line.startswith(f"alert NOT sent: {DOWN} | ") and "no rows for 2027" in line


def test_a12_sign_in_refusal_slack_did_not_take_is_printed_with_its_text(monkeypatch, capsys):
    def refused():
        raise DriveSignInRefused("invalid_grant")

    class Recorder:
        def commit(self, what):
            return "nothing to commit"

    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: NoAlertSender(DOWN))
    monkeypatch.setattr("fno.storage.wiring.build_manifest_recorder", lambda: Recorder())
    monkeypatch.setattr("fno.filings.wiring.build_companies", refused)
    assert cmd_filings_archive(Namespace(symbols=None, max_minutes=10)) == 1
    [line] = _unsent(capsys.readouterr().out)
    assert line.startswith(f"alert NOT sent: {DOWN} | ") and "invalid_grant" in line
