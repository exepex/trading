"""One planted pre-open morning for the end-to-end tests (story A22, criteria 4-6; A22d's open check): the real
adapters over a fake NSE session and fake Groww candles, O9's data store over a folder, O10's error log, A22d's open
check over the same folder and planted index-close files, fake committers and alerts."""

from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime, timedelta

from fno.alerts.sender import SENT
from fno.health.capture_errors import CaptureErrorLog
from fno.intraday.candle_source import CandleAnswer
from fno.preopen.check_files import PreopenFiles
from fno.preopen.open_check import OpenCheck
from fno.preopen.parts import FO_PREOPEN_URL, GIFT_URL, GrowwIndexPreopen, NseGiftNifty, NsePreopenList
from fno.preopen.record import PreopenRecorder
from fno.preopen.run import PreopenRun
from fno.storage.data_store import DataStore
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

from .fakes import FakeClock
from .fixtures import candles, fo_list, gift, ist

ROUTINE_START = ist(8, 36)
VALUES = ("1234.5", "4321", "5555.5", "101.5")


class Response:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content, self.status_code = content, status_code


class NseSession:
    def __init__(self, answers: dict):
        self.answers = answers  # url -> bytes, or a callable of the clock's time

    def get(self, url, timeout):
        answer = self.answers[url]
        if isinstance(answer, Exception):
            raise answer
        return Response(answer) if isinstance(answer, bytes) else answer


class Candles:
    def __init__(self, clock, raw: bytes | Exception):
        self.clock, self.raw = clock, raw

    def minute_candles(self, day: date) -> CandleAnswer:
        if isinstance(self.raw, Exception):
            raise self.raw
        return CandleAnswer("1m", day, day, self.raw, [], self.clock.now(), self.clock.now())


class Committer:
    def __init__(self, outcome="committed"):
        self.outcome, self.calls = outcome, []

    def commit(self, what):
        self.calls.append(what)
        return self.outcome


class EarlyCommitter(Committer):
    def __init__(self, clock, outcome="receipts committed and pushed (2 file(s))"):
        super().__init__(outcome)
        self.clock, self.at = clock, []

    def commit(self, what):
        self.at.append(self.clock.now())
        return super().commit(what)


class Sender:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return SENT


class StoreFiles(PreopenFiles):
    """A22's files as the open check sees them, over the test's Drive folder and receipts; `on_read` runs per read."""

    def __init__(self, drive, receipts: ReceiptFolder, on_read=lambda path: None):
        self.drive, self.receipts, self.on_read, self.read_paths = drive, receipts, on_read, []

    def has(self, path: str) -> bool:
        return self.receipts.read(f"data/{path}") is not None

    def read(self, path: str) -> bytes:
        self.read_paths.append(path)
        self.on_read(path)
        return self.drive.get(f"data/{path}")


def previous_weekday(day: date) -> date:
    day -= timedelta(1)
    while day.weekday() >= 5:
        day -= timedelta(1)
    return day


class Desk:
    """One planted morning: a repository folder, a Drive folder, the parts' answers and NSE's index-close files."""

    def __init__(self, tmp_path, start=ROUTINE_START, nse=None, nifty=None, trading=True, clock_warning="",
                 official=None, on_read=lambda path: None):  # fmt: skip
        self.root, self.clock = tmp_path / "repo", FakeClock(start)
        self.drive = LocalFolderStore(tmp_path / "drive")
        answers = {GIFT_URL: gift(), FO_PREOPEN_URL: fo_list()} | (nse or {})
        session = NseSession(answers)
        self.parts = [NseGiftNifty(session, self.clock.now), NsePreopenList(session, self.clock.now),
                      GrowwIndexPreopen("nifty", Candles(self.clock, candles() if nifty is None else nifty)),
                      GrowwIndexPreopen("banknifty", Candles(self.clock, candles(close_0909=6666.5)))]  # fmt: skip
        self.errors = CaptureErrorLog(self.root / "research/ops/capture_errors.csv")
        self.committers, self.sender, self.out = [Committer(), Committer()], Sender(), []
        self.early = EarlyCommitter(self.clock)
        self.trading, self.clock_warning = trading, clock_warning
        self.official, self.on_read, self.files = official or {}, on_read, None

    def store(self) -> DataStore:
        return DataStore(self.drive, "data", ReceiptFolder(self.root / "receipts"), "preopen", "run-1",
                         clock=lambda: datetime(2026, 10, 22, 3, 41, tzinfo=UTC))  # fmt: skip

    def open_check(self) -> OpenCheck:
        self.files = StoreFiles(self.drive, ReceiptFolder(self.root / "receipts"), self.on_read)
        return OpenCheck(previous_weekday, self.files, self.official.get, self.store())

    def recorder(self, **label_read) -> PreopenRecorder:
        """`label_read`: the recorder's label reader when a test must not race the real background one."""

        def run(done):
            return PreopenRun(self.parts, self.clock.now, self.clock.sleep, done)

        return PreopenRecorder(self._trading, run, self.store(), self.errors, self.committers, self.sender,
                               lambda: self.clock_warning, self.early, self.open_check(), self.out.append,
                               **label_read)  # fmt: skip

    def plant_day_row(self, day: date, nifty: str = "", banknifty: str = "", basis: str = "flat_0915_unverified",
                      old_header: bool = False) -> None:  # fmt: skip
        """An earlier session's day row in Drive with its receipt (values only, the other cells left empty)."""
        names = ["date", "nifty_preopen", "banknifty_preopen"]
        cells = [day.isoformat(), nifty, banknifty]
        if not old_header:
            names += ["nifty_preopen_basis", "banknifty_preopen_basis"]
            cells += [basis if nifty else "", basis if banknifty else ""]
        self.store().put(f"preopen/day/{day:%Y}/{day:%m}/{day:%Y-%m-%d}.csv",
                         (",".join(names) + "\n" + ",".join(cells) + "\n").encode())  # fmt: skip

    def check_rows(self, day: date) -> list[dict]:
        data = self.drive.get(f"data/preopen/check/{day:%Y}/{day:%m}/{day:%Y-%m-%d}.csv")
        return list(csv.DictReader(io.StringIO(data.decode()))) if data else []

    def _trading(self, day):
        if isinstance(self.trading, Exception):
            raise self.trading
        return self.trading

    def day_row(self) -> dict:
        data = self.drive.get("data/preopen/day/2026/10/2026-10-22.csv")
        return next(csv.DictReader(io.StringIO(data.decode())))

    def gift_row(self) -> dict:
        data = self.drive.get("data/preopen/gift/2026/10/2026-10-22.csv")
        return next(csv.DictReader(io.StringIO(data.decode())))

    def committed_text(self) -> str:
        return "\n".join(p.read_text() for p in self.root.rglob("*") if p.is_file())
