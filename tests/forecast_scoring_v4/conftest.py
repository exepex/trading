"""The v4 tests' one stand-in for the Drive-stored day and deadline records (G10's `_drive_records` seam). From the
pack's first live day (Mon 26 Oct 2026) a receipt under `receipts/data/v4/` makes the real records read Drive, which
the tests have no settings for. Tests whose point is not those records (no implied vol) use this fixture: no records,
as before the first receipt. G7b renames the seam to `build_drive_records` and updates this fixture; never copy it."""

import pytest

SEAM = "fno.forecast_scoring.v4.wiring._drive_records"


class NoDriveRecords:
    def files(self) -> dict[str, bytes]:
        return {}


@pytest.fixture
def no_v4_drive_records(monkeypatch):
    monkeypatch.setattr(SEAM, lambda folder: NoDriveRecords())
