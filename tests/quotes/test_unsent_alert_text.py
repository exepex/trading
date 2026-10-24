"""O2's outage days: when Slack is down, a 3 pm quote command prints every alert it could not send with its text
("alert NOT sent: <reason> | <text>"), so the routine can post it; never a bare "alert NOT sent" line (A4, A4c)."""

from argparse import Namespace

import pytest

from fno.alerts.sender import SENT, NoAlertSender
from fno.quotes.cli import RAW_FILE_ALERT, cmd_quotes
from fno.quotes.recorder import RecordResult
from fno.research_data.calendar import CalendarError

DOWN = "Slack answered HTTP 503"
INDEX_TEXT = (
    "3 pm index recorder: not recorded today: FINNIFTY (incomplete, canonical none). Data only; NIFTY is separate; "
    "the sidecars in research/data/quotes/groww/ say why for FINNIFTY."
)  # A4c-2: the attempted index keeps its sidecar pointer, word for word
RAW = RecordResult("recorded", "nifty_20261019_145500", False, 0, raw_file_error="raw quote file not saved: DriveDown",
                   raw_file_detail="HTTP 503 from Drive")  # fmt: skip


class Recorder:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def record(self, outside_window=False):
        if self.error:
            raise self.error
        return self.result


class Indices:
    def __init__(self, recorders, now, sleep):
        pass

    def run(self):
        return {"FINNIFTY": RecordResult("recorded", "finnifty_20261019_150130", False, 0)}


class SlackUp:
    def send(self, text):
        return SENT


def _run(monkeypatch, capsys, sender, quotes_cmd="record", recorder=None):
    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: sender)
    monkeypatch.setattr("fno.composition.build_quote_recorder", lambda cfg: recorder)
    monkeypatch.setattr("fno.quotes.index_wiring.build_index_quote_recorders", lambda cfg: {})
    monkeypatch.setattr("fno.quotes.indices_cli.IndexRecording", Indices)
    args = Namespace(quotes_cmd=quotes_cmd, config=None, source="configured", window=None, outside_window=False)
    code = cmd_quotes(args)
    return code, capsys.readouterr().out.splitlines()


def _unsent(lines):
    return [line for line in lines if line.startswith("alert NOT sent")]


def test_a_raw_file_alert_slack_did_not_take_is_printed_with_its_text(monkeypatch, capsys):
    code, lines = _run(monkeypatch, capsys, NoAlertSender(DOWN), recorder=Recorder(RAW))
    [line] = _unsent(lines)
    assert code == 1 and line.startswith(f"alert NOT sent: {DOWN} | ")
    assert line.endswith(RAW_FILE_ALERT.format(reason="DriveDown: HTTP 503 from Drive", snapshot_id=RAW.snapshot_id))


def test_a_calendar_stop_slack_did_not_take_is_printed_with_its_text(monkeypatch, capsys):
    error = CalendarError("no rows for 2027")
    code, lines = _run(monkeypatch, capsys, NoAlertSender(DOWN), recorder=Recorder(error=error))
    [line] = _unsent(lines)
    assert code == 1 and "3 pm quote recorder stopped, nothing recorded: no rows for 2027" in line.split(" | ", 1)[1]


def test_the_index_alert_slack_did_not_take_is_printed_with_its_text(monkeypatch, capsys):
    code, lines = _run(monkeypatch, capsys, NoAlertSender(DOWN), quotes_cmd="record-indices")
    [line] = _unsent(lines)
    assert code == 1 and line == f"alert NOT sent: {DOWN} | " + INDEX_TEXT


@pytest.mark.parametrize("quotes_cmd", ["record", "record-indices"])
def test_a_sent_alert_prints_its_outcome_once_and_no_unsent_line(monkeypatch, capsys, quotes_cmd):
    _, lines = _run(monkeypatch, capsys, SlackUp(), quotes_cmd=quotes_cmd, recorder=Recorder(RAW))
    assert lines.count(SENT) == 1 and not _unsent(lines)
