"""The read-only `capture-gate` run and the quality composition root (story MS-P1b)."""

from datetime import date

from fno.school.quality import command
from fno.school.quality.capture_gate import CaptureGateReport
from fno.school.quality.gate import RoadQualityGate
from fno.school.quality.wiring import build_capture_gate_report, build_quality_gate


class Lines:
    def lines(self, through):
        return [f"line for {through}", "second line"]


def test_the_run_prints_one_line_per_road_and_exits_zero_even_when_roads_are_closed():
    printed = []
    assert command.run(date(2026, 10, 22), Lines(), printed.append) == 0
    assert printed == ["line for 2026-10-22", "second line"]


def test_the_command_takes_the_last_day_from_its_argument(monkeypatch):
    seen = []
    monkeypatch.setattr(command, "run", lambda through: seen.append(through) or 0)
    assert command.main(["--through", "2026-10-22"]) == 0 and seen == [date(2026, 10, 22)]


def test_the_default_day_is_today_once_the_captures_can_exist_else_yesterday():
    from datetime import datetime

    from tests.school.contracts.builders import IST

    assert command.default_through(datetime(2026, 10, 22, 15, 15, tzinfo=IST)) == date(2026, 10, 22)
    assert command.default_through(datetime(2026, 10, 22, 15, 14, tzinfo=IST)) == date(2026, 10, 21)
    assert command.default_through(datetime(2026, 10, 22, 9, 0, tzinfo=IST)) == date(2026, 10, 21)


def test_the_composition_root_builds_the_real_gate_and_a_report_over_the_real_roads(monkeypatch):
    from fno.school.roads import wiring as roads_wiring
    from fno.school.roads.catalogue import RecordedRoadCatalogue
    from fno.school.roads.snapshots import RecordedSnapshotSource
    from tests.school.roads.capture_builder import DictStore

    monkeypatch.setattr(roads_wiring, "build_raw_stores", lambda: [DictStore()])
    assert build_quality_gate(4).band_steps == 4 and isinstance(build_quality_gate(), RoadQualityGate)
    report = build_capture_gate_report(4)
    assert isinstance(report, CaptureGateReport) and report.gate.band_steps == 4
    assert isinstance(report.catalogue, RecordedRoadCatalogue) and isinstance(report.snapshots, RecordedSnapshotSource)
