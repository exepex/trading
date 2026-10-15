"""Story A17b, criterion 4: Drive's own creation time of a copy, read through the store's metadata (no network)."""

from datetime import UTC, datetime

import pytest

from fno.global_cues.us_index_sources import CboeSp500Source, NasdaqNdxSource
from fno.storage.creation_times import CREATED_FIELD, GoogleDriveCreationTimes
from tests.global_cues.fakes import cboe, nasdaq


class FakeDriveStore:
    def __init__(self, found):
        self.found, self.asked = found, []

    def metadata(self, path, fields):
        self.asked.append((path, fields))
        return self.found


def test_drives_created_time_is_read_under_the_area_and_parsed_as_utc():
    drive = FakeDriveStore({CREATED_FIELD: "2026-10-15T00:44:53.452Z"})
    created = GoogleDriveCreationTimes(drive, "raw").created_at("cboe/x.json")
    assert created == datetime(2026, 10, 15, 0, 44, 53, 452000, tzinfo=UTC)
    assert drive.asked == [("raw/cboe/x.json", "createdTime")]


@pytest.mark.parametrize("found", [None, {}, {CREATED_FIELD: ""}])
def test_an_absent_file_or_time_is_unknown(found):
    assert GoogleDriveCreationTimes(FakeDriveStore(found), "raw").created_at("cboe/x.json") is None


def test_a_malformed_private_close_is_named_without_its_text():
    with pytest.raises(ValueError) as cboe_error:
        CboeSp500Source().parse(cboe(("2026-10-14", -4321.5)))
    with pytest.raises(ValueError) as nasdaq_error:
        NasdaqNdxSource().parse(nasdaq([("10/14/2026", "x4321.5")]))
    for error in (cboe_error, nasdaq_error):
        assert "4321" not in str(error.value) and "the value" in str(error.value)
