"""Story A9b, criterion 3 as commands: each command run end to end on a fake NSE (every NSE source is built by
`build_nse_source`, replaced here), with its exit code and its named line; a paused host stops a long pass with one
line. No network, no Drive, no Slack."""

from datetime import date
from types import SimpleNamespace

import pytest

import fno.composition
from fno.cli import main
from fno.http_pacing import SourceCoolingOff
from fno.storage import wiring
from fno.storage.manifest_folder import Fingerprint
from fno.storage.raw_source import NseIndexCloseSource
from fno.storage.raw_store import LocalFolderStore
from tests.nse_retry.fake_nse import answer

DAY = date(2026, 10, 14)
PAUSED = "nsearchives.nseindia.com refused requests (HTTP 403); not calling it for 15 minutes"


class Always:
    """NSE answering every request the same way (a status, or an exception raised)."""

    def __init__(self, status=None, error=None):
        self.status, self.error, self.asked = status, error, 0

    def _answer(self, url, **kwargs):
        self.asked += 1
        if self.error:
            raise self.error
        return answer(self.status)

    get = head = _answer


@pytest.fixture
def nse(monkeypatch):
    """Sets how the fake NSE answers; every source the commands build uses it, with no real waits."""

    def answering(session):
        def build(source_type):
            return source_type(session, sleep=lambda s: None)

        monkeypatch.setattr(wiring, "build_nse_source", build)
        monkeypatch.setattr(fno.composition, "build_nse_source", build)  # imported by name there
        return session

    return answering


class Recorder:
    def commit(self, what):
        return f"committed {what}"


class Archive:
    stored, not_archived = [], []

    def capture(self, path, found):
        return None


@pytest.fixture
def no_drive(monkeypatch):
    monkeypatch.setattr(wiring, "build_manifest_recorder", Recorder)
    monkeypatch.setattr(wiring, "build_revision_archive", Archive)


def test_data_revisions_sweep_exits_1_naming_the_reason(nse, no_drive, capsys):
    nse(Always(503))
    assert main(["data-revisions", "sweep", "index-close", "--from", "2026-10-14", "--to", "2026-10-14"]) == 1
    out = capsys.readouterr().out
    assert "no answer: nse/indices/index-close/2026/10/ind_close_all_14102026.csv: NSE archive: " in out
    assert "HTTP 503 after 4 tries (check again next sweep)" in out and "1 unanswered" in out


def test_a_paused_host_stops_the_revision_sweep_with_one_line(nse, no_drive, capsys):
    session = nse(Always(error=SourceCoolingOff(PAUSED)))
    assert main(["data-revisions", "sweep", "index-close", "--from", "2026-10-12", "--to", "2026-10-14"]) == 1
    out = capsys.readouterr().out
    assert (
        "STOPPED: NSE archive: nse/indices/index-close/" in out
        and "nsearchives.nseindia.com refused" in out
        and "3 file(s) not read: run again after the pause" in out
    )
    assert session.asked == 1 and "no answer:" not in out  # never one line per file, never a request into the pause


def test_the_fingerprint_spot_check_exits_1_naming_each_file(nse, monkeypatch, capsys):
    from fno.storage import fingerprints

    days = (date(2026, 10, 13), DAY)
    prints = [Fingerprint(d, NseIndexCloseSource.url_for(NseIndexCloseSource.path_for(d)), "0" * 64, 1) for d in days]
    monkeypatch.setattr(wiring, "build_drive_reader", lambda: None)
    monkeypatch.setattr(fingerprints, "fingerprint_store", lambda *a: prints)
    nse(Always(403))
    assert main(["data-fingerprints", "index-close", "--spot-check", "2"]) == 1
    out = capsys.readouterr().out
    assert out.count("NO ANSWER: NSE archive: ") == 2 and "HTTP 403 after 1 try" in out


def test_vix_history_fill_stops_with_its_named_line(nse, monkeypatch, tmp_path, capsys):
    from fno.vix_history import wiring as vix

    monkeypatch.setattr(vix, "build_vix_raw_area", lambda: LocalFolderStore(tmp_path / "raw"))
    monkeypatch.setattr(vix, "_fingerprints", lambda manifests: {})
    nse(Always(503))
    assert main(["vix-history", "fill", "--from", "2026-08", "--to", "2026-08"]) == 1
    out = capsys.readouterr().out
    assert "HTTP 503 after 4 tries" in out and "Traceback" not in out and not (tmp_path / "raw").exists()


def test_vix_history_sweep_stops_on_a_paused_host(nse, monkeypatch, tmp_path, capsys):
    from fno.vix_history import wiring as vix

    monkeypatch.setattr(vix, "_fingerprints", lambda manifests: {})
    monkeypatch.setattr(vix, "_owner_drive", lambda env=None: None)
    monkeypatch.setattr(vix, "AreaStore", lambda drive, area: LocalFolderStore(tmp_path / area))
    session = nse(Always(error=SourceCoolingOff(PAUSED)))
    assert main(["vix-history", "sweep", "--from", "2026-07", "--to", "2026-09"]) == 1
    out = capsys.readouterr().out
    assert "STOPPED: NSE archive: " in out and "3 file(s) not read" in out and session.asked == 1


def test_participant_oi_watch_logs_unreachable_and_exits_1(nse, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(wiring, "PARTICIPANT_OI_RELEASE_LOG", tmp_path / "release_checks_v2.csv")
    nse(Always(503))
    assert main(["participant-oi", "watch", "--day", "2026-10-12", "--until", "00:01", "--every", "5"]) == 1
    assert "2026-10-12: unreachable at" in capsys.readouterr().out
    assert (tmp_path / "release_checks_v2.csv").read_text().count("unreachable") == 1


@pytest.mark.parametrize(
    ("session", "said", "asked"),
    [(Always(403), "no answer 2026-10-12: NSE archive: ", 2), (Always(error=SourceCoolingOff(PAUSED)), "STOPPED: ", 1)],
    ids=["refused", "paused"],
)
def test_participant_oi_sweep_names_why_or_stops(nse, no_drive, monkeypatch, tmp_path, capsys, session, said, asked):
    recorded = {date(2026, 10, 12): None, date(2026, 10, 13): None}
    monkeypatch.setattr(fno.composition, "participant_oi_last_writes", lambda: recorded)
    nse(session)
    assert main(["participant-oi", "sweep", "--evidence-folder", str(tmp_path)]) == 1
    assert said in capsys.readouterr().out and session.asked == asked


def test_market_archive_reports_every_problem_and_still_takes_the_other_lists(monkeypatch, capsys):
    from fno.market_read_models import cli as market
    from fno.storage.raw_source import RawFileRefused, RawSourceUnavailable

    complete = SimpleNamespace(fill=lambda start, end: SimpleNamespace(complete=True))
    taken = []

    class Taker:
        def __init__(self, name):
            self.name = name

        def take(self, day):
            taken.append(self.name)
            if len(taken) == 1:
                raise RawFileRefused(f"NSE archive: {self.name}: HTTP 403 after 1 try", 403, 1)
            return f"{self.name}: archived"

    def lists_down(day):
        raise RawSourceUnavailable("NSE archive: own list: HTTP 503 after 4 tries", 503, 4)

    monkeypatch.setattr(wiring, "build_librarian", lambda name, log=print: complete)
    monkeypatch.setattr(wiring, "build_manifest_recorder", Recorder)
    monkeypatch.setattr(wiring, "build_snapshot_taker", Taker)
    monkeypatch.setattr(
        market, "_archive_revisions", lambda day: "NSE did not answer the revision re-read of 1 file(s)"
    )
    monkeypatch.setattr(market, "_archive_own_lists", lists_down)
    problem = market._archive_session(DAY)
    assert problem.split("; ")[0] == "NSE did not answer the revision re-read of 1 file(s)"
    assert "HTTP 403 after 1 try" in problem and "own corporate-action lists: NSE archive: own list" in problem
    assert taken == list(market.DAILY_SNAPSHOTS)  # a refused list never stops the others
