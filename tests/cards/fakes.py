"""Fakes for the card tests (story T1): committed records from a dict, Slack, Drive and server clocks. The planted
records are copies of the repository's real committed files, so the card is tested on real shapes."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fno.cards.card import CardBuilder
from fno.cards.committed import CommittedRecords
from fno.cards.daily import DailyCard
from fno.cards.deliveries import RepoDeliveryFiles
from fno.cards.forecasts import LiveCaptureForecasts
from fno.cards.recorded_weather import RecordedWeather
from fno.cards.render import SlackTextRenderer
from fno.cards.session import CALENDAR_PATH, SessionCheck
from fno.cards.status import REGISTRY_PATH, RegistryStatus
from fno.constants import BOOKS
from fno.server_clock import ServerClock, ServerTimeUnknown
from fno.storage.raw_store import RawFileConflict, RawFileStore

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = "research/forecasts/live_v2/2026/2026-10-14_forecasts.csv"
REPORT = "research/forecasts/scores/2026-10-13.json"
REGISTRY_HEADER = b"name,version,sha256,status,changed_on,approved_by,evidence_commit\n"
PAPER_ROW = (
    "sc-iv-rich,1," + "a" * 64 + ",research,2026-10-13,desk,\n"
    "sc-iv-rich,1," + "a" * 64 + ",paper,2026-10-14,owner," + "b" * 40 + "\n"
)
WEATHER = "research/forecasts/v4/weather/{day:%Y}/{day}.json"  # M1's record path (WeatherRecords.path)
TOKEN = "test-token-not-real"
HOST = datetime(2026, 10, 15, 9, 38, 0, tzinfo=UTC)  # 15:08 IST


def account(open_trades: int = 0, closed: int = 0) -> bytes:
    return json.dumps({"open_trades": [{}] * open_trades, "closed_trades": [{}] * closed}).encode()


def planted() -> dict[str, bytes]:
    files = {
        CALENDAR_PATH: (ROOT / CALENDAR_PATH).read_bytes(),
        REGISTRY_PATH: REGISTRY_HEADER,
        CAPTURE: (ROOT / CAPTURE).read_bytes(),
        REPORT: (ROOT / REPORT).read_bytes(),
    }
    files.update({f"journal/{book}/account/positions.json": account() for book in BOOKS})
    return files


class FakeRecords(CommittedRecords):
    def __init__(self, files: dict[str, bytes] | None = None):
        self.files = planted() if files is None else files

    def read(self, path: str) -> bytes | None:
        return self.files.get(path)

    def names(self, folder: str) -> list[str]:
        prefix = folder.rstrip("/") + "/"
        return sorted({p[len(prefix) :].split("/")[0] for p in self.files if p.startswith(prefix)})


def weather_of(records: CommittedRecords) -> RecordedWeather:
    return RecordedWeather(records, lambda day: WEATHER.format(day=day))


def daily_card(records: FakeRecords, root: Path) -> DailyCard:
    builder = CardBuilder(RegistryStatus(records, records), weather_of(records), LiveCaptureForecasts(records))
    return DailyCard(SessionCheck(records), builder, SlackTextRenderer(), RepoDeliveryFiles(root, records))


class FakeResponse:
    def __init__(self, body):
        self._body, self.status_code = body, 200

    def json(self):
        return self._body


class FakeSlack:
    """A requests session for chat.postMessage: answers in turn from `bodies` (an exception is raised)."""

    def __init__(self, *bodies):
        self.bodies, self.calls = list(bodies), []

    def post(self, url, **kwargs):
        self.calls.append(kwargs)
        body = self.bodies.pop(0) if len(self.bodies) > 1 else self.bodies[0]
        if isinstance(body, Exception):
            raise body
        return FakeResponse(body)


def slack_ok(at: datetime = HOST) -> dict:
    return {"ok": True, "ts": f"{at.timestamp():.6f}", "channel": "C0C89E8QCCD"}


class FakeDrive(RawFileStore):
    name = "fake drive"

    def __init__(self, error: Exception | None = None):
        self.files, self.error = {}, error

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        if self.error:
            raise self.error
        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data


class FixedClock(ServerClock):
    def __init__(self, name: str, moment: datetime | None):
        self.name, self.moment = name, moment

    def now(self):
        if self.moment is None:
            raise ServerTimeUnknown("ConnectionError")
        return self.moment


class Ticking:
    """The host clock: HOST, then a millisecond later on each call."""

    def __init__(self, start: datetime = HOST):
        self.moment = start

    def __call__(self) -> datetime:
        self.moment += timedelta(milliseconds=1)
        return self.moment
