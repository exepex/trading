"""Story A9b, criterion 3: every command names an NSE source's final failure (503 four times, or a 403): a named
line and exit 1, a recorded failure or an alert; never a traceback, never a silent skip, nothing saved for the file.
Alerts go to a fake sender: no test posts to Slack (judge 119 minor 1)."""

from datetime import date
from types import SimpleNamespace

import pytest

import fno.composition
from fno.cli import main
from fno.filings.librarian import FilingsLibrarian
from fno.filings.sources import NseFilingFileSource
from fno.research_data.release_check_once import ReleaseCheckOnce
from fno.research_data.release_times import ReleaseLog, ReleaseTimeRecorder
from fno.research_data.reread_log import RereadLog
from fno.storage.fingerprints import compare_with_source
from fno.storage.librarian_cli import run_librarian
from fno.storage.manifest_folder import Fingerprint
from fno.storage.raw_source import NseIndexCloseSource, ParticipantOiSource
from fno.storage.raw_store import LocalFolderStore
from fno.storage.revision_source import sweep_revisions
from fno.storage.revisions_cli import UNANSWERED
from fno.storage.snapshot_source import EquityListSource
from fno.storage.snapshot_taker import SnapshotTaker
from tests.filings.fakes import FakeIndex, at, filing
from tests.filings.test_filings_librarian import FAR, SINCE, StepClock, archive
from tests.filings.xbrl_fixtures import results_xbrl
from tests.nse_retry.fake_nse import ScriptedNse, answer
from tests.research_data.test_release_check_once import CALENDAR, MONDAY, Clock, FakeSender
from tests.research_data.test_release_check_once import at as ist

DAY = date(2026, 10, 14)
DOWN = [answer(503)] * 4
FAILURES = {"503 x4": (DOWN, "HTTP 503 after 4 tries"), "403": ([answer(403)], "HTTP 403 after 1 try")}


class Recorder:
    def commit(self, what):
        return f"committed {what}"


@pytest.fixture(params=sorted(FAILURES))
def failure(request):
    answers, said = FAILURES[request.param]
    return list(answers), said


def index_close(answers):
    return NseIndexCloseSource(ScriptedNse(*answers), sleep=lambda s: None)


def test_data_librarian_stops_with_a_named_line_and_commits_its_rows(failure):
    answers, said = failure
    source, out = index_close(answers), []

    class Fill:
        def fill(self, start, end):
            source.fetch(NseIndexCloseSource.path_for(DAY))

    assert run_librarian(Fill, None, Recorder(), "test", None, DAY, out=out.append) == 1
    assert out[0].startswith("stopped: NSE archive: ") and said in out[0] and out[-1] == "committed test"


def test_data_snapshot_names_the_failure_and_saves_nothing(tmp_path, monkeypatch, capsys, failure):
    answers, said = failure
    store = LocalFolderStore(tmp_path / "raw")
    source = EquityListSource(ScriptedNse(*answers), sleep=lambda s: None)
    from fno.storage import wiring

    monkeypatch.setattr(wiring, "build_snapshot_taker", lambda name: SnapshotTaker(store, source, lambda d: None))
    monkeypatch.setattr(wiring, "build_manifest_recorder", Recorder)
    assert main(["data-snapshot", "equity-list", "--day", "2026-10-14"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("NOT archived: NSE archive: ") and said in out and not (tmp_path / "raw").exists()


def test_the_revision_sweep_names_why_each_file_had_no_answer(failure):
    answers, said = failure
    path = NseIndexCloseSource.path_for(DAY)
    result = sweep_revisions(index_close(answers), [path])
    (line,) = [UNANSWERED.format(path=p, reason=why) for p, why in result.unanswered.items()]
    assert line.startswith(f"no answer: {path}: NSE archive: ") and said in line


def test_the_fingerprint_spot_check_names_each_file_and_goes_on(failure):
    answers, said = failure
    days = (date(2026, 10, 13), DAY)
    prints = [Fingerprint(d, NseIndexCloseSource.url_for(NseIndexCloseSource.path_for(d)), "0" * 64, 1) for d in days]
    lines = compare_with_source(index_close([*answers, answer(404)]), prints)
    assert "NO ANSWER: NSE archive: " in lines[0] and said in lines[0]
    assert lines[1].endswith("the source no longer serves it (archive copy kept)")  # the next file still compared


def test_participant_oi_check_once_alerts_when_nse_is_down(tmp_path, monkeypatch, capsys):
    source = ParticipantOiSource(ScriptedNse(*DOWN), sleep=lambda s: None)
    log = ReleaseLog(tmp_path / "release_checks_v2.csv")
    recorder = ReleaseTimeRecorder(source, ParticipantOiSource.path_for, CALENDAR, log, Clock(ist(MONDAY, 18)))
    sender = FakeSender()
    monkeypatch.setattr(
        fno.composition, "build_release_check_once", lambda: ReleaseCheckOnce(recorder, RereadLog(tmp_path / "r.csv"))
    )
    monkeypatch.setattr(fno.composition, "build_alert_sender", lambda: sender)
    assert main(["participant-oi", "check-once", "--day", "2026-10-12"]) == 1
    assert len(sender.sent) == 1 and "unreachable" in sender.sent[0].lower()
    assert [c.outcome for c in log.checks()] == ["unreachable"]


def filings_run(tmp_path, answers):
    clock = StepClock()
    host = NseFilingFileSource(ScriptedNse(*answers), sleep=lambda s: None)
    index = FakeIndex({"TCS": [filing("TCS", "A.xml", at(9))], "INFY": [filing("INFY", "B.xml", at(9))]})
    librarian = FilingsLibrarian([index], host, archive(tmp_path, clock), clock, log=lambda line: None)
    return librarian.run(["TCS", "INFY"], SINCE, clock.now + FAR)


def test_filings_go_on_after_a_refused_file_and_stop_when_nse_is_down(tmp_path):
    refused = filings_run(tmp_path / "a", [answer(403), answer(200, results_xbrl())])
    assert refused.failed == {"TCS"} and "HTTP 403 after 1 try" in refused.failures[0] and refused.saved == 1
    assert not refused.stopped
    down = filings_run(tmp_path / "b", DOWN)
    assert down.stopped.startswith("NSE stopped answering at TCS") and "HTTP 503 after 4 tries" in down.stopped
    assert down.saved == 0


def test_market_names_every_file_its_revision_re_read_could_not_get(monkeypatch, capsys):
    from fno.market_read_models import cli as market
    from fno.storage import wiring

    monkeypatch.setattr(wiring, "build_revision_archive", lambda: SimpleNamespace(stored=[], not_archived=[]))
    monkeypatch.setattr(wiring, "build_revision_capturing_source", lambda source_type, archive: index_close(DOWN * 4))
    problem = market._archive_revisions(DAY)
    assert problem.startswith("NSE did not answer the revision re-read of 4 file(s): ") and "HTTP 503" in problem


def test_market_look_up_names_the_failure_and_exits_1(monkeypatch, capsys):
    from fno.market_read_models import cli as market
    from fno.storage import wiring
    from fno.storage.raw_source import RawSourceUnavailable

    def down(day):
        raise RawSourceUnavailable("NSE archive: x: HTTP 503 after 4 tries", 503, 4)

    monkeypatch.setattr(market, "_archive_own_lists", down)
    monkeypatch.setattr(wiring, "build_manifest_recorder", Recorder)
    assert market._look_up(SimpleNamespace(day=DAY)) == 1
    out = capsys.readouterr().out.splitlines()
    assert out == [
        "look-up stopped, NSE did not answer: NSE archive: x: HTTP 503 after 4 tries",
        f"committed market look-up {DAY}",
    ]


def test_filings_day_lists_run_the_next_list_after_one_stops(monkeypatch, capsys):
    from fno.filings import runs_cli
    from fno.filings import wiring as filings_wiring
    from fno.storage import wiring

    ran = []

    class Fill:
        def __init__(self, name):
            self.name = name

        def fill(self, start, end):
            ran.append(self.name)
            index_close(DOWN).fetch(NseIndexCloseSource.path_for(DAY))

    monkeypatch.setattr(runs_cli, "_budgeted_day_list", lambda name, deadline: Fill(name))
    monkeypatch.setattr(runs_cli, "first_unarchived_day", lambda *a: DAY)
    monkeypatch.setattr(filings_wiring, "build_progress", lambda: SimpleNamespace(step=lambda: None))
    monkeypatch.setattr(wiring, "build_manifest_folder", lambda: None)
    monkeypatch.setattr(wiring, "build_manifest_recorder", Recorder)
    monkeypatch.setattr(fno.composition, "build_alert_sender", lambda: FakeSender())
    names = sorted(filings_wiring.DAY_LISTS)
    assert runs_cli.cmd_filings_day_lists(SimpleNamespace(end=DAY, name=None, max_minutes=10)) == 1
    assert ran == names and len(names) == 2
    assert capsys.readouterr().out.count("stopped: NSE archive: ") == 2  # each list names its own stop
