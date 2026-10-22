"""Composition root of `fno/school/quality/` (story MS-P1b): the quality gate and the capture-gate report over the
recorded captures of `fno/school/roads/wiring.py`."""

from ..roads.wiring import build_road_services
from .band import DEFAULT_BAND_STEPS
from .capture_gate import CaptureGateReport
from .gate import RoadQualityGate


def build_quality_gate(band_steps: int = DEFAULT_BAND_STEPS) -> RoadQualityGate:
    return RoadQualityGate(band_steps)


def build_capture_gate_report(band_steps: int = DEFAULT_BAND_STEPS) -> CaptureGateReport:
    services = build_road_services()
    return CaptureGateReport(services.calendar, services.catalogue, services.snapshots, build_quality_gate(band_steps))
