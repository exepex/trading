"""Fakes for the same-day announcements poll (story A21 part 2): NSE's day list, a local folder for Drive, a clock."""

from datetime import date, datetime, timedelta

from fno.announcements_live.constants import ITEM_COLUMNS, ITEMS_TABLE, POLL_COLUMNS, POLLS_TABLE
from fno.announcements_live.day_state import DriveDayState
from fno.announcements_live.mark_parts import MarkParts
from fno.announcements_live.poller import AnnouncementsPoller
from fno.announcements_live.source import DayList
from fno.models import IST
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

DAY = date(2026, 10, 19)


def at(hhmm: str, seconds: int = 0) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return datetime(2026, 10, 19, hour, minute, tzinfo=IST) + timedelta(seconds=seconds)


def item(seq: str, nse_time: str = "19-Oct-2026 10:58:00", symbol: str = "ABC") -> dict:
    return {"seq_id": seq, "symbol": symbol, "sm_isin": "INE000000000", "desc": "Outcome of Board Meeting",
            "an_dt": nse_time, "exchdisstime": nse_time, "attchmntFile": f"https://nsearchives/{seq}.pdf"}  # fmt: skip


class Source:
    """Each call takes the next answer: a list of items, or an exception to raise."""

    def __init__(self, clock, *answers):
        self.clock, self.answers, self.calls = clock, list(answers), 0

    def day_list(self, day):
        self.calls += 1
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return DayList(answer, repr(answer).encode(), self.clock())


class Failures:
    def __init__(self):
        self.rows = []

    def record(self, day, step, kind, message):
        self.rows.append((day, step, kind, message))

    def has(self, day, kind):
        return any((d, k) == (day, kind) for d, _, k, _ in self.rows)

    def kinds(self):
        return [kind for _, _, kind, _ in self.rows]


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


class Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


def poller(tmp_path, source, clock, run_id, failures=None, alerts=None, session=True, days=None):
    drive, receipts = LocalFolderStore(tmp_path / "drive"), ReceiptFolder(tmp_path / "receipts")
    store = DataStore(drive, "data", receipts, "announcements-live", run_id, clock=clock)
    days = days or DriveDayState(DriveCache(drive, receipts, tmp_path / "cache"), "data", tmp_path / f"state-{run_id}")
    failures, alerts = failures or Failures(), alerts or Alerts()
    built = AnnouncementsPoller(source, days, store, MarkParts(store, ITEMS_TABLE, ITEM_COLUMNS),
                                MarkParts(store, POLLS_TABLE, POLL_COLUMNS), failures, alerts, lambda day: session,
                                clock, run_id)  # fmt: skip
    return built, failures, alerts
