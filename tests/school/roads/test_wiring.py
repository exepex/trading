"""The roads composition root builds the real classes from stored places only (story MS-P1b)."""

import pytest

from fno.school.contracts.roads import RoadCatalogue
from fno.school.contracts.snapshot import SnapshotSource
from fno.school.roads import wiring
from fno.school.roads.catalogue import RecordedRoadCatalogue
from fno.school.roads.snapshots import RecordedSnapshotSource
from fno.school.roads.stored_files import StoredFilesOnly
from fno.school.roads.wiring import RawFilesNotConfigured, build_road_services
from tests.school.roads.capture_builder import CALENDAR, DictStore


def test_the_services_are_the_recorded_ones_and_one_reader_serves_both(monkeypatch, tmp_path):
    archive = DictStore()
    monkeypatch.setattr(wiring, "build_raw_stores", lambda: [archive])
    services = build_road_services(tmp_path, CALENDAR)
    assert isinstance(services.catalogue, RecordedRoadCatalogue) and isinstance(services.catalogue, RoadCatalogue)
    assert isinstance(services.snapshots, RecordedSnapshotSource) and isinstance(services.snapshots, SnapshotSource)
    assert services.snapshots.captures is services.catalogue.captures
    assert services.calendar is CALENDAR


def test_the_archive_is_read_from_stored_files_only_and_never_fetched_from_nse(monkeypatch, tmp_path):
    archive = DictStore()
    monkeypatch.setattr(wiring, "build_raw_stores", lambda: [archive])
    library = build_road_services(tmp_path, CALENDAR).catalogue.lots.library
    assert library.stores == [archive] and isinstance(library.source, StoredFilesOnly) and library.archive is None


def test_no_archive_setting_is_an_error_not_five_closed_roads(monkeypatch, tmp_path):
    monkeypatch.setattr(wiring, "build_raw_stores", lambda: [])
    monkeypatch.setattr(wiring, "build_owner_drive", lambda: None)
    with pytest.raises(RawFilesNotConfigured):
        build_road_services(tmp_path, CALENDAR)
