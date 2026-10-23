from datetime import date, datetime

import pytest

from fno.alerts.sender import SENT, AlertSender
from fno.models import IST
from fno.routine_logs.run_log import RoutineRunLog
from fno.routine_logs.run_state import RunStateFolder
from fno.routine_logs.schedule import ROUTINES
from fno.storage.raw_store import LocalFolderStore

LIVE = {spec.name: date(2026, 10, 1) for spec in ROUTINES}  # every routine watched in the tests


class Clock:
    def __init__(self, moment: datetime):
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


class Sent(AlertSender):
    def __init__(self, outcome: str = SENT):
        self.texts: list[str] = []
        self.outcome = outcome

    def send(self, text: str) -> str:
        self.texts.append(text)
        return self.outcome


def ist(hour: int, minute: int, day: int = 23) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=IST)


@pytest.fixture
def store(tmp_path):
    return LocalFolderStore(tmp_path / "drive")


@pytest.fixture
def clock():
    return Clock(ist(14, 5))


@pytest.fixture
def run_log(store, clock, tmp_path):
    return RoutineRunLog(store, RunStateFolder(tmp_path / "state"), clock)
