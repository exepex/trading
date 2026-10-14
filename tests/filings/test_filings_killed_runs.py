"""Story A12: a run that is stopped (its time budget) or killed (GitHub's 6-hour limit) before it commits resumes
without duplicate files, half-written files or lost manifest rows."""

from datetime import date, datetime, timedelta

from fno.constants import FILING_RESULTS
from fno.filings.day_lists import EveryDayCalendar, TimeBudgetedFill, check_day_list
from fno.filings.librarian import FilingsLibrarian
from fno.filings.manifest import FilingManifest
from fno.filings.runs_cli import first_unarchived_day
from fno.filings.sources import NseAnnouncementsSource
from fno.models import IST
from fno.storage.coverage import CoverageDataset
from fno.storage.librarian import RawDataLibrarian
from fno.storage.manifest_folder import FingerprintingStore, ManifestFolder
from fno.storage.raw_store import LocalFolderStore
from tests.filings.fakes import SINCE, FakeIndex, FakeXbrlHost, StepClock, archive, at, filing
from tests.filings.xbrl_fixtures import results_xbrl

SOURCE = NseAnnouncementsSource
FIRST = date(2023, 10, 13)


class DayListHost(SOURCE):
    def __init__(self):
        super().__init__(session=None)
        self.fetched = []

    def fetch(self, path):
        self.fetched.append(path)
        return b'[{"symbol": "TCS"}]'


def day_list_librarian(tmp_path, host):
    manifests = ManifestFolder(tmp_path / "manifests")
    store = FingerprintingStore(LocalFolderStore(tmp_path / "drive"), manifests, [SOURCE])
    dataset = CoverageDataset(SOURCE, check_day_list, manifests.fingerprints(SOURCE))
    return RawDataLibrarian(store, host, dataset, EveryDayCalendar(), {}, log=lambda line: None), manifests


def test_day_lists_stop_cleanly_at_their_budget_and_the_next_run_resumes(tmp_path):
    now = [datetime(2026, 10, 13, 22, tzinfo=IST)]

    def clock():
        now[0] += timedelta(minutes=10)  # each chunk of days "takes" ten minutes
        return now[0]

    end = FIRST + timedelta(days=89)
    librarian, manifests = day_list_librarian(tmp_path, DayListHost())
    first = TimeBudgetedFill(librarian, clock, now[0] + timedelta(minutes=25), chunk_days=30).fill(FIRST, end)
    assert first.complete and len(first.uploaded) == 60 and first.end == FIRST + timedelta(days=59)
    resume = first_unarchived_day(SOURCE, end, manifests, FIRST)
    assert resume == FIRST + timedelta(days=60)  # the next run starts at the first day still missing
    host = DayListHost()
    librarian, _ = day_list_librarian(tmp_path, host)
    second = TimeBudgetedFill(librarian, clock, now[0] + timedelta(hours=1), chunk_days=30).fill(resume, end)
    assert len(second.uploaded) == 30 and len(host.fetched) == 30  # nothing already archived is fetched again


def test_a_day_list_run_killed_before_its_commit_rewrites_the_missing_rows(tmp_path):
    librarian, manifests = day_list_librarian(tmp_path, DayListHost())
    librarian.fill(FIRST, FIRST + timedelta(days=2))
    (tmp_path / "manifests" / "announcements.csv").unlink()  # the kill: the rows never reached the repository
    host = DayListHost()
    librarian, manifests = day_list_librarian(tmp_path, host)
    report = librarian.fill(FIRST, FIRST + timedelta(days=2))
    assert report.present == 3 and host.fetched == []  # Drive's copies are kept, nothing fetched from NSE
    assert len(manifests.read(SOURCE)) == 3  # and their rows are written again
    assert sorted(p.name for p in (tmp_path / "drive").rglob("*.json")) == [
        "announcements_20231013.json", "announcements_20231014.json", "announcements_20231015.json"
    ]  # fmt: skip


def test_an_xbrl_run_killed_before_its_commit_fetches_again_without_duplicates(tmp_path):
    """The rows are lost, so the files are fetched from NSE again (the cost of a kill), but Drive keeps one copy
    each (the same bytes again change nothing) and every row comes back."""
    index = FakeIndex({"TCS": [filing("TCS", "A.xml", at(9)), filing("TCS", "B.xml", at(10))]})
    host = FakeXbrlHost({"A.xml": results_xbrl(), "B.xml": results_xbrl(half_year=False)})
    clock = StepClock()
    FilingsLibrarian([index], host, archive(tmp_path, clock), clock, log=lambda line: None).run(
        ["TCS"], SINCE, clock.now + timedelta(days=1)
    )
    (tmp_path / "manifests" / "results-xbrl.csv").unlink()  # the kill
    report = FilingsLibrarian([index], host, archive(tmp_path, clock), clock, log=lambda line: None).run(
        ["TCS"], SINCE, clock.now + timedelta(days=1)
    )
    assert report.complete and report.saved == 2
    assert len(FilingManifest(tmp_path / "manifests").rows(FILING_RESULTS)) == 2
    assert sorted(p.name for p in (tmp_path / "drive").rglob("*.xml")) == ["A.xml", "B.xml"]
    assert not list((tmp_path / "drive").rglob(".*.part"))  # no half-written file left behind


class FailingDrive:
    """A store whose third save times out for good (Drive's own retries exhausted)."""

    def __init__(self, store):
        self.store, self.saves = store, 0

    def get(self, path):
        return self.store.get(path)

    def put(self, path, data):
        self.saves += 1
        if self.saves == 3:
            import requests

            raise requests.ReadTimeout("www.googleapis.com: read timed out")
        self.store.put(path, data)


def test_a_drive_failure_stops_the_run_cleanly_and_keeps_the_rows_saved_so_far(tmp_path):
    """Run 38479538255 (14 Oct 2026): one Drive read timeout crashed the job and lost 74 minutes of rows."""
    from fno.filings.archive import FilingArchive
    from fno.storage.raw_store import LocalFolderStore

    index = FakeIndex({s: [filing(s, f"{s}.xml", at(9))] for s in ("A", "B", "C", "D")})
    host = FakeXbrlHost({f"{s}.xml": results_xbrl() for s in ("A", "B", "C", "D")})
    clock = StepClock()
    store = FailingDrive(LocalFolderStore(tmp_path / "drive"))
    archive_ = FilingArchive(store, FilingManifest(tmp_path / "manifests"), clock)
    report = FilingsLibrarian([index], host, archive_, clock, log=lambda line: None).run(
        ["A", "B", "C", "D"], SINCE, clock.now + timedelta(days=1)
    )
    assert report.stopped.startswith("the archive store stopped answering at C")
    assert report.checked == ["A", "B"] and report.saved == 2  # returned normally: the caller commits and saves
    assert len(FilingManifest(tmp_path / "manifests").rows(FILING_RESULTS)) == 2


def test_each_day_list_gets_its_share_of_the_budget():
    from fno.filings.runs_cli import list_deadlines

    start = datetime(2026, 10, 14, 3, tzinfo=IST)
    assert list_deadlines(["announcements", "board-meetings"], start, 50) == [
        ("announcements", start + timedelta(minutes=25)),
        ("board-meetings", start + timedelta(minutes=50)),
    ]
