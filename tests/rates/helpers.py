"""Fakes for the rates capture (story A21): RBI's saved pages of 16 Oct 2026, a local folder for Drive, a clock."""

from datetime import datetime, timedelta
from pathlib import Path

from fno.models import IST
from fno.rates.capture import RatesCapture
from fno.rates.constants import COLUMNS, RBI_HOME, RBI_RELEASE, RBI_RELEASES, TABLE
from fno.rates.fetch import RateFetchError
from fno.rates.history import DriveRatesHistory
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.part_table import PartTable
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

FIXTURES = Path(__file__).parent / "fixtures"
HOME = (FIXTURES / "rbi_home_20261016.html").read_bytes()
LIST = (FIXTURES / "rbi_releases_20261016.html").read_bytes()
RELEASE = (FIXTURES / "rbi_release_63803.html").read_bytes()
T0 = datetime(2026, 10, 16, 18, 40, tzinfo=IST)


def pages(**changes):
    """URL -> bytes or an exception; keyword overrides: home, releases, release."""
    found = {RBI_HOME: HOME, RBI_RELEASES: LIST, RBI_RELEASE.format(prid=63803): RELEASE}
    for name, url in (("home", RBI_HOME), ("releases", RBI_RELEASES), ("release", RBI_RELEASE.format(prid=63803))):
        if name in changes:
            found[url] = changes[name]
    return found


class Pages:
    def __init__(self, found):
        self.found, self.asked = found, []

    def get(self, url):
        self.asked.append(url)
        value = self.found.get(url, RateFetchError("refused", f"{url}: HTTP 404"))
        if isinstance(value, Exception):
            raise value
        return value


class Failures:
    def __init__(self):
        self.rows = []

    def record(self, day, step, kind, message):
        self.rows.append((day, step, kind, message))


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


class Clock:
    def __init__(self, start=T0):
        self.now = start

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def capture(tmp_path, found, clock=None, run="20261016T131000Z-aaaaaa", history=None):
    drive, receipts = LocalFolderStore(tmp_path / "drive"), ReceiptFolder(tmp_path / "receipts")
    clock = clock or Clock()
    store = DataStore(drive, "data", receipts, "rates-capture", run, clock=clock)
    history = history or DriveRatesHistory(DriveCache(drive, receipts, tmp_path / "cache"), receipts, "data",
                                           tmp_path / f"table-{run}")  # fmt: skip
    failures, alerts, fetch = Failures(), Alerts(), Pages(found)
    run_ = RatesCapture(fetch, store, PartTable(store, TABLE, COLUMNS), history, failures, alerts, clock)
    return run_, failures, alerts, fetch
