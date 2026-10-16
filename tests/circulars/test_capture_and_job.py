"""A20b: new circulars become one part of `circulars/list` with their first-seen time; relevant files are saved first
and a failed file leaves its circular for the next run; a second run with the same list writes nothing; a failed
feed, a possible gap on SEBI's latest page or unread earlier parts give one alert and exit 1."""

from datetime import UTC, date, datetime

from fno.alerts.dry_run import DryRunAlertSender
from fno.circulars.capture import LIST_TABLE, CircularCapture, file_path
from fno.circulars.job import CircularsJob
from fno.circulars.model import COLUMNS, NSE, SEBI, Circular, FeedFailed
from fno.storage.data_store import DataStore
from fno.storage.manifest_commit import ManifestRecorder
from fno.storage.part_table import read_parts
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

D16 = date(2026, 10, 16)
NOW = datetime(2026, 10, 16, 11, 5, tzinfo=UTC)
FNO = Circular(NSE, "NSE/FAOP/76921", D16, "Futures & Options", "Trading", "Mock trading", "https://x/FAOP76921.pdf")
MF = Circular(NSE, "NSE/NMF/76970", D16, "Mutual Fund", "Trading", "Suspension", "https://x/NMF76970.zip")
SEBI_C = Circular(
    SEBI, "105293", D16, "", "", "derivatives contracts", "https://www.sebi.gov.in/legal/circulars/a_105293.html"
)


class Feed:
    def __init__(self, listed=(), error=None, latest_page_only=False, broken_files=()):
        self.listed, self.error, self.broken = list(listed), error, set(broken_files)
        self.LATEST_PAGE_ONLY = latest_page_only

    def fetch(self, since, until):
        if self.error:
            raise self.error
        return self.listed

    def download(self, circular):
        if circular.link in self.broken:
            raise FeedFailed(f"{circular.link}: HTTP 403")
        return f"file of {circular.number}".encode()


def store(tmp_path, run_id="20261016T110500Z-aaaaaa"):
    drive = LocalFolderStore(tmp_path / "drive")
    return drive, DataStore(drive, "data", ReceiptFolder(tmp_path / "receipts"), "circulars", run_id)


def parts(drive_root):
    return read_parts(drive_root / "data" / LIST_TABLE, COLUMNS)


def test_new_circulars_are_listed_with_first_seen_time_and_relevant_files_saved(tmp_path):
    drive, data = store(tmp_path)
    capture = CircularCapture({NSE: Feed([FNO, MF])}, lambda c: c is FNO, data, clock=lambda: NOW, out=[].append)
    assert capture.run(D16, {}) == []
    rows = parts(tmp_path / "drive")
    assert [(r["number"], r["fno_relevant"], r["first_seen_at"]) for r in rows] == [
        ("NSE/FAOP/76921", "yes", "2026-10-16T11:05:00+00:00"), ("NSE/NMF/76970", "no", "2026-10-16T11:05:00+00:00"),
    ]  # fmt: skip
    assert drive.get(f"data/{file_path(FNO)}") == b"file of NSE/FAOP/76921"
    assert file_path(FNO) == "circulars/files/nse/2026/10/FAOP76921.pdf"
    assert drive.get(f"data/{file_path(MF)}") is None  # not relevant: listed, file not kept


def test_a_second_run_with_the_same_list_writes_no_part(tmp_path):
    drive, data = store(tmp_path)
    seen = {FNO.link: NSE, MF.link: NSE}
    assert CircularCapture({NSE: Feed([FNO, MF])}, lambda c: True, data, out=[].append).run(D16, seen) == []
    assert not (tmp_path / "drive" / "data" / LIST_TABLE).exists()


def test_a_relevant_file_that_fails_leaves_its_circular_for_the_next_run(tmp_path):
    drive, data = store(tmp_path)
    feed = Feed([FNO, MF], broken_files=[FNO.link])
    problems = CircularCapture({NSE: feed}, lambda c: c is FNO, data, out=[].append).run(D16, {})
    assert len(problems) == 1 and "NSE/FAOP/76921: file NOT saved" in problems[0]
    assert [r["number"] for r in parts(tmp_path / "drive")] == ["NSE/NMF/76970"]


def test_a_failed_feed_is_a_problem_and_the_other_feed_still_runs(tmp_path):
    drive, data = store(tmp_path)
    feeds = {NSE: Feed(error=FeedFailed("HTTP 403")), SEBI: Feed([SEBI_C], latest_page_only=True)}
    problems = CircularCapture(feeds, lambda c: True, data, out=[].append).run(D16, {})
    assert problems == ["nse: list NOT read: HTTP 403"]
    assert [r["source"] for r in parts(tmp_path / "drive")] == [SEBI]


def test_a_latest_page_with_nothing_seen_before_is_a_possible_gap(tmp_path):
    drive, data = store(tmp_path)
    feeds = {SEBI: Feed([SEBI_C], latest_page_only=True)}
    problems = CircularCapture(feeds, lambda c: True, data, out=[].append).run(D16, {"https://old": SEBI})
    assert len(problems) == 1 and "some may have been missed" in problems[0]
    assert [r["number"] for r in parts(tmp_path / "drive")] == ["105293"]  # still listed


class Recorder(ManifestRecorder):
    def __init__(self, outcome="receipts committed and pushed (1 file(s))"):
        self.outcome = outcome

    def pending(self):
        return []

    def commit(self, what):
        return self.outcome


def test_the_job_alerts_once_naming_every_problem(tmp_path):
    _, data = store(tmp_path)
    alerts = DryRunAlertSender()
    capture = CircularCapture({NSE: Feed(error=FeedFailed("HTTP 403"))}, lambda c: True, data, out=[].append)
    recorder = Recorder("receipts NOT committed: push failed: rejected. Commit receipts/ by hand")
    assert CircularsJob(dict, capture, recorder, alerts, "RUN", [].append).run(D16) == 1
    assert (
        len(alerts.would_send) == 1 and "HTTP 403" in alerts.would_send[0] and "NOT committed" in alerts.would_send[0]
    )


def test_unread_earlier_parts_stop_the_capture(tmp_path):
    drive, data = store(tmp_path)
    alerts = DryRunAlertSender()

    def unreadable():
        raise RuntimeError("data/circulars/list/2026/10/x.csv: damaged")

    capture = CircularCapture({NSE: Feed([FNO])}, lambda c: True, data, out=[].append)
    assert CircularsJob(unreadable, capture, Recorder(), alerts, "RUN", [].append).run(D16) == 1
    assert "earlier circulars NOT read" in alerts.would_send[0]
    assert not (tmp_path / "drive" / "data" / LIST_TABLE).exists()  # nothing captured, so nothing listed twice


def test_a_clean_run_sends_nothing(tmp_path):
    _, data = store(tmp_path)
    alerts = DryRunAlertSender()
    capture = CircularCapture({NSE: Feed([MF])}, lambda c: False, data, out=[].append)
    assert CircularsJob(dict, capture, Recorder(), alerts, "RUN", [].append).run(D16) == 0 and alerts.would_send == []
