"""Story E4 fixtures: started paper accounts in a temporary journal, a quote store, and the desks on a fixed clock."""

import pytest

from fno.composition import open_account_writer
from fno.constants import BOOKS
from fno.desk.entries import EntryDesk
from fno.desk.exits import ExitDesk
from fno.desk.settlement import FinalSettlement
from fno.desk.snapshot import RecordedExecutionSnapshots

from .builders import CHARGES, DAY, DictStore, at


class FakeSettlements:
    """Final settlement prices by expiry; an expiry not set has no published file yet (None)."""

    def __init__(self):
        self.prices: dict = {}
        self.asked: list = []

    def final_settlement(self, underlying, expiry):
        self.asked.append((underlying, expiry))
        price = self.prices.get(expiry)
        if price is None:
            return None
        return FinalSettlement(underlying, expiry, price, f"fixture/{expiry}.csv.zip", "a" * 64)


class RecordingAlerts:
    def __init__(self):
        self.sent: list[str] = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


@pytest.fixture
def root(tmp_path):
    for book in BOOKS:
        with open_account_writer(book, tmp_path) as writer:
            writer.start(DAY)
    return tmp_path


@pytest.fixture
def store():
    return DictStore()


@pytest.fixture
def snapshots(store):
    return RecordedExecutionSnapshots(store)


@pytest.fixture
def alerts():
    return RecordingAlerts()


@pytest.fixture
def clock():
    """A settable clock: the desks run at 15:20 unless a test moves it."""
    now = {"t": at(15, 20)}

    class Clock:
        def __call__(self):
            return now["t"]

        def set(self, moment):
            now["t"] = moment

    return Clock()


@pytest.fixture
def entry_desk(clock):
    return EntryDesk(CHARGES, clock)


@pytest.fixture
def settlements():
    return FakeSettlements()


@pytest.fixture
def exit_desk(clock, alerts, settlements):
    return ExitDesk(CHARGES, alerts, settlements, clock)


@pytest.fixture
def check_passed(monkeypatch):
    """Story E4c's guard: a test double for the entry check that passes, so a leg that then does not fill is a fill
    failing after the check (a defect) and E4's unwind runs as built (decision 43)."""
    monkeypatch.setattr("fno.desk.entries.entry_problems", lambda snapshot, legs, units, taken=None: [])
