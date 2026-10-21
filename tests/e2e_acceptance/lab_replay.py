"""Story O11, criterion 8 of FL1-1 (with FL1-1d's evening edition): G13b's `price_ranges` issue in the day run, and
FL1's `lab close` at 20:05 after it, on the recorded day, through their real classes: G13b's issuer on the day's
recorded chain, its own seal check and reader, FL1's adapter, report, records and run. The outside seams are replaced as
elsewhere in the replay: Drive is a local folder (the Drive cache's copy), GitHub's push time of the issue's receipt is
the replay clock at the issue, and #fno-forecast is a recording poster. NIFTY only: 16 Oct had no A4c capture, so
BANKNIFTY had no chain (as G13's replay step). The closes are a synthetic history ending the day before (G13b's
committed close table is not in the replay's repository)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fno.forecast_lab.composers import EveningComposer
from fno.forecast_lab.constants import EVENING, REPORT_AREAS
from fno.forecast_lab.delivery import Attachment, Delivery, ReportPoster
from fno.forecast_lab.edition_run import Edition, EditionRun
from fno.forecast_lab.g13b_adapter import G13bCloses, G13bRanges
from fno.forecast_lab.g13b_history import G13bHistory
from fno.forecast_lab.maker import ReportMaker
from fno.forecast_lab.match import MatchSection
from fno.forecast_lab.page.builder import PageBuilder
from fno.forecast_lab.page.camera import PageCamera
from fno.forecast_lab.page.facts import FactsSource
from fno.forecast_lab.page.reasons import Facts
from fno.forecast_lab.page.render import InterimRenderer
from fno.forecast_lab.records import DriveReportRecords
from fno.forecast_lab.report import CloseReport
from fno.forecast_lab.sessions import RegularSessions
from fno.price_distribution.sources import SnapshotChains
from fno.price_distribution.store import DriveDistributionStore
from fno.price_ranges.closes import CloseSeries, Outcomes
from fno.price_ranges.issuer import RangeIssuer
from fno.price_ranges.reader import RangeForecasts, RangeScores, receipt_file
from fno.price_ranges.sealing import SealCheck
from fno.price_ranges.seals import Seals
from fno.price_ranges.wiring import build_builder
from fno.storage.data_store import DataStore
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder
from tests.checks.builders import CALENDAR
from tests.price_ranges.builders import closes

from . import real_day as rd

UNDERLYINGS = ("NIFTY",)
EVENING_AT = rd.at(20, 5)


class ForecastChannel(ReportPoster):
    """#fno-forecast: every message recorded with its files' names, each accepted."""

    def __init__(self):
        self.posts: list[str] = []
        self.files: list[dict[str, bytes]] = []

    def post(self, text: str, attachments: list[Attachment]) -> Delivery:
        self.posts.append(text)
        self.files.append({a.name: a.data for a in attachments})
        return Delivery("posted to #fno-forecast", sent=True)


class FixedCamera(PageCamera):
    """Headless Chromium is an outside program: the replay takes a fixed picture (FL1-1c's own tests draw real ones)."""

    def picture(self, html: str, out: Path) -> Path:
        out.write_bytes(b"PNG replay")
        return out


class NoFacts(FactsSource):
    def facts(self, day):
        return Facts()


class NoCloses(CloseSeries):
    """NSE's official close of the day is archived in the evening: none exists at 15:45."""

    def closes(self, underlying):
        return []


class LabReplay:
    def __init__(self, root, cfg, clock, alerts):
        self.root, self.cfg, self.clock, self.alerts = root, cfg, clock, alerts
        self.drive = LocalFolderStore(root / "drive")  # the Drive cache's local copy: G13b's reader reads it
        self.channel, self.pushed = ForecastChannel(), {}

    def _store(self, writer: str) -> DataStore:
        return DataStore(self.drive, "data", ReceiptFolder(self.root / "receipts"), writer, "replay")

    def _seals(self, store) -> Seals:
        return Seals(SealCheck(self._pushed_at, CALENDAR), store, receipt_file, self.clock)

    def _pushed_at(self, receipt_path: str) -> datetime:
        return self.pushed[receipt_path]  # an unknown push raises: G13b's "late", never "sealed"

    def price_ranges(self, day) -> list[str]:
        """`fno pricerange issue --at 1545 --live` (O1's `price_ranges` step, G13b), its receipt pushed at once."""
        store = DriveDistributionStore(self.drive, self._store("pricerange"))
        issuer = RangeIssuer(SnapshotChains(rd.quote_store(self.root)), build_builder(self.cfg),
                             lambda underlying: closes(last=CALENDAR.previous_session(day)), store, CALENDAR,
                             UNDERLYINGS, day, self.clock)  # fmt: skip
        code, lines = issuer.issue(day)
        if code:
            raise RuntimeError(lines[-1])
        self.pushed.update({path: self.clock() for path in self._receipts()})
        return lines

    def _receipts(self) -> list[str]:
        folder = self.root / "receipts"
        return [p.relative_to(self.root).as_posix() for p in folder.rglob("*.sha256") if "price_ranges" in p.as_posix()]

    def _reader(self, store) -> tuple[RangeForecasts, RangeScores]:
        return RangeForecasts(self.drive.folder, self._seals(store)), RangeScores(self.drive.folder)

    def evening(self, day) -> list[str]:
        """`fno lab close` (the evening edition, FL1-1d) at 20:05, the lab and G13b live from the day."""
        self.clock.until(EVENING_AT)
        store = DriveDistributionStore(self.drive, self._store("pricerange"))
        ranges = G13bRanges(*self._reader(store))
        sessions = RegularSessions(CALENDAR)
        report = CloseReport(ranges, MatchSection(ranges, G13bCloses(Outcomes(NoCloses())), sessions, day), day,
                             underlyings=UNDERLYINGS)  # fmt: skip
        records = DriveReportRecords(self._store("forecast-lab"), ReceiptFolder(self.root / "receipts"),
                                     REPORT_AREAS[EVENING])  # fmt: skip
        pages = PageBuilder(ranges, G13bHistory(*self._reader(store)), NoFacts(), sessions, UNDERLYINGS)
        composer = EveningComposer(report, ReportMaker(pages, InterimRenderer(), FixedCamera()), records.report)
        result = EditionRun(Edition(EVENING, day), composer, records, self.channel, self.alerts, sessions.is_regular,
                            self.clock).run(day)  # fmt: skip
        if result.failed:
            raise RuntimeError(result.lines[-1])
        return result.lines
