"""Part c's composition root (self-review): `build_classifier` builds with the real cards, A6's events, the frozen
rules card and the not-yet-replayable card replay; the Drive-backed services are replaced by fakes here."""

from fno.school.fakes import FakeFills, FakeRoadCatalogue, FakeSnapshotSource
from fno.school.instructor import wiring
from fno.school.instructor.adapters import NotYetReplayable
from fno.school.roads.wiring import RoadServices


def test_build_classifier_wires_the_recorded_inputs(monkeypatch):
    services = RoadServices(None, FakeRoadCatalogue(), FakeSnapshotSource(), None)
    monkeypatch.setattr(wiring, "build_road_services", lambda: services)
    monkeypatch.setattr(wiring, "build_fill_port", lambda cfg: FakeFills())
    classifier = wiring.build_classifier({"risk_free_rate": 0.065})
    assert classifier.rules_sha256 == wiring.rules_sha256()
    assert isinstance(classifier.evidence.replay, NotYetReplayable) and classifier.evidence.rate == 0.065
    assert classifier.evidence.stops.loss_multiple("CS1@1") == 2.0
