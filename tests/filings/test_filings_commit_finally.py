"""Story A12, judge 51 addendum 3 should-fixes: rows are committed whatever stops a run; a Drive create whose answer
is lost stays one copy; a damaged stored copy is a per-file failure, never a crash."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
import requests

from fno.constants import FILING_RESULTS
from fno.filings import runs_cli, wiring
from fno.filings.archive import FilingArchive
from fno.filings.librarian import FilingsLibrarian
from fno.filings.manifest import FilingManifest
from fno.storage.raw_store import LocalFolderStore, StoredCopyDamaged
from tests.filings.fakes import SINCE, FakeIndex, FakeXbrlHost, StepClock, at, filing
from tests.filings.xbrl_fixtures import results_xbrl
from tests.test_drive_upload import PATH, InMemoryDrive, store_on


class Recorder:
    def __init__(self):
        self.commits = []

    def commit(self, what):
        self.commits.append(what)
        return "manifest rows committed and pushed (1 file(s))"


def test_a_crash_in_the_archive_run_still_commits_the_rows(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr("fno.storage.wiring.build_manifest_recorder", lambda: recorder)
    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: SimpleNamespace(send=lambda text: "sent"))
    monkeypatch.setattr(wiring, "build_companies", lambda: ["A"])

    def crash():
        raise RuntimeError("a bug after some files were saved")

    monkeypatch.setattr(wiring, "build_progress", crash)
    with pytest.raises(RuntimeError):
        runs_cli.cmd_filings_archive(SimpleNamespace(symbols=None, max_minutes=1))
    assert recorder.commits == ["filings archive (stopped early)"]


def test_a_normal_run_commits_once():
    recorder = Recorder()
    once = runs_cli.CommitOnce(recorder)
    assert once.commit("filings archive") == once.commit("again")
    assert recorder.commits == ["filings archive"]


def test_a_create_whose_answer_is_lost_to_a_timeout_stays_one_copy():
    """The judge's probe: Drive makes the file, the answer is lost to a read timeout, the retry under the same
    reserved ID gets 409, the copy is read back: one create, the same bytes."""

    class LostAnswerDrive(InMemoryDrive):
        lost = False

        def post(self, url, json=None, files=None, params=None, timeout=None):
            answer = super().post(url, json=json, files=files, params=params, timeout=timeout)
            if files is not None and not self.lost:
                self.lost = True
                raise requests.ReadTimeout("the answer to a create that got through")
            return answer

    drive = LostAnswerDrive()
    store = store_on(drive)
    store.put(PATH, b"bytes")
    name = PATH.rsplit("/", 1)[-1]
    assert drive.creates.count(name) == 1 and store.get(PATH) == b"bytes"


def test_a_damaged_stored_copy_fails_that_file_only(tmp_path):
    class DamagingStore(LocalFolderStore):
        def put(self, path, data):
            if path.endswith("A.xml"):
                raise StoredCopyDamaged("A.xml: Drive holds different bytes than were sent")
            super().put(path, data)

    index = FakeIndex({"A": [filing("A", "A.xml", at(9))], "B": [filing("B", "B.xml", at(9))]})
    host = FakeXbrlHost({"A.xml": results_xbrl(), "B.xml": results_xbrl()})
    clock = StepClock()
    archive = FilingArchive(DamagingStore(tmp_path / "drive"), FilingManifest(tmp_path / "manifests"), clock)
    report = FilingsLibrarian([index], host, archive, clock, log=lambda line: None).run(
        ["A", "B"], SINCE, clock.now + timedelta(days=1)
    )
    assert report.saved == 1 and report.failed == {"A"} and report.checked == ["A", "B"]
    assert "Drive holds different bytes" in report.failures[0]
    assert list(FilingManifest(tmp_path / "manifests").rows(FILING_RESULTS)) == [
        "https://nsearchives.nseindia.com/corporate/xbrl/B.xml"
    ]
