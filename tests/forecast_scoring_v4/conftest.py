"""The v4 tests' one stand-in for the Drive-stored v4 records (G8's `build_drive_records` seam, G10's day and deadline
records and G7b's rows, terms, outcomes and diagnostics all read through it). From the
pack's first live day (Mon 26 Oct 2026) a receipt under `receipts/data/v4/` makes the real records read Drive, which
the tests have no settings for. Tests whose point is not those records (no implied vol) use this fixture: no records,
as before the first receipt. Never copy it."""

import pytest

SEAM = "fno.forecast_scoring.v4.wiring.build_drive_records"


class NoDriveRecords:
    def files(self) -> dict[str, bytes]:
        return {}

    def paths(self) -> list[str]:
        return []


@pytest.fixture
def no_v4_drive_records(monkeypatch):
    monkeypatch.setattr(SEAM, lambda folder: NoDriveRecords())
