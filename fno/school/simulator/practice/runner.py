"""The practice runner (story MS-SIM-d3): one fleet per session and scenario over a window, collected into a report.

The window is checked against DATA_SPEND before any session is read. Each scenario (median, p75, p95) has its own home
folder and accounts, because a fill's price depends on the scenario's spread; the sessions run in date order so the
accounts carry across them. Coverage (what the snapshot could not price) is read once, from the first scenario, as it
does not depend on the spread chosen."""

import csv
from datetime import date
from pathlib import Path

from ...constants import SLOT_1500, Outcome, RecordKind, RefusalReason
from ...contracts.fleet import RunMode, SessionRun
from ...contracts.records import OutcomeRecord
from ...contracts.roads import ROADS_BY_CODE
from ...fleet.counts_file import opportunity_path
from ...fleet.runner import SchoolFleet
from ...tickets.rupees import account_net
from ..source.catalogue import HistoricalRoadCatalogue
from ..source.snapshots import HistoricalRoadSource
from ..spreads.model import Scenario
from .fleet import MarginFor, PracticeParts, build_practice_fleet
from .report import PracticeReport, RoadDayCoverage, ScenarioResult
from .window import RunWindow


class PracticeRunner:
    def __init__(self, parts: PracticeParts, home: Path, margin_for: MarginFor | None = None,
                 scenarios: tuple[Scenario, ...] = tuple(Scenario)):  # fmt: skip
        self.parts, self.home, self.margin_for, self.scenarios = parts, Path(home), margin_for, scenarios

    def run(self, window: RunWindow) -> PracticeReport:
        window.check(self.parts.windows)
        sessions = window.sessions(self.parts.calendar)
        roads = tuple(ROADS_BY_CODE[code] for code in window.roads)
        report = PracticeReport(window.first, window.last, window.roads)
        for position, scenario in enumerate(self.scenarios):
            result = report.scenarios.setdefault(scenario, ScenarioResult())
            for session in sessions:
                fleet = build_practice_fleet(self.parts, session, scenario, self.home / scenario.value,
                                             self.margin_for, roads)  # fmt: skip
                self._collect(result, fleet, session, fleet.run(session, RunMode.REPLAY), self.home / scenario.value)
                if position == 0:
                    self._coverage(report, scenario, session, roads)
        return report

    def _collect(self, result: ScenarioResult, fleet: SchoolFleet, session: date, run: SessionRun, home: Path) -> None:
        if run.status or not run.decisions:
            return
        result.sessions_run += 1
        for record in run.decisions:
            driver = result.driver(record.decision.driver_id)
            driver.scheduled += 1
            driver.outcomes[str(record.decision.outcome)] += 1
            if record.decision.outcome == Outcome.REFUSED and record.decision.reason == RefusalReason.MARGIN_ROOM:
                result.refused_for_margin += 1
        self._counts(result, home / opportunity_path(session, SLOT_1500))
        self._outcomes(result, fleet, session)

    @staticmethod
    def _counts(result: ScenarioResult, path: Path) -> None:
        if not path.is_file():
            return
        for row in csv.DictReader(path.read_text(encoding="utf-8").splitlines()):
            driver = result.driver(row["driver"])
            driver.eligible += int(row["eligible"])
            driver.fillable += int(row["fillable"])
            driver.executed += int(row["executed"])

    @staticmethod
    def _outcomes(result: ScenarioResult, fleet: SchoolFleet, session: date) -> None:
        seal = fleet.dashcam.find(session, SLOT_1500, RecordKind.OUTCOMES)
        closed = [r for r in fleet.dashcam.read(seal) if isinstance(r, OutcomeRecord)] if seal else []
        for driver_id in {r.driver_id for r in closed}:
            mine = [r for r in closed if r.driver_id == driver_id]
            driver = result.driver(driver_id)
            driver.closed_trades += sum(1 for r in mine if not r.is_ticket)
            driver.net += account_net(mine).net

    def _coverage(self, report: PracticeReport, scenario: Scenario, session: date, roads) -> None:
        parts = self.parts
        catalogue = HistoricalRoadCatalogue(parts.calendar, parts.chain, parts.terms, parts.windows, roads)
        source = HistoricalRoadSource(parts.chain, parts.spreads, scenario, parts.windows)
        days = [d for d in catalogue.day(session) if d.status.open]
        report.sessions_without_roads += 0 if days else 1
        for road_day in days:
            _, found = source.build(road_day)
            report.coverage.append(RoadDayCoverage.of(session, road_day.road.code, found))
            report.insufficient_buckets.update(found.insufficient)
