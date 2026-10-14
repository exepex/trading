"""Composition root of the data checks (story C3): the checks in the order they report, the quote store the snapshot
is read from, the shock flag source, the NSE file stores and the alert sender. Swapping any changes this file only."""

from __future__ import annotations

from pathlib import Path

from .data_checks import DataChecks
from .gate import DataGate
from .leg_checks import LegQuotesValid
from .market_checks import PreviousSessionFile, SpotNearPreviousClose
from .schedule import ExecutionSchedule, PackSnapshotSchedule
from .shock import NoShockFlags
from .snapshot_checks import SnapshotInWindow, SnapshotMatchesRecord, SnapshotReadable


def build_data_checks(stores, calendar, shocks=None) -> DataChecks:
    from ..storage.raw_source import NseDailyFoSource

    return DataChecks(
        (
            SnapshotReadable(),
            SnapshotInWindow(),
            SnapshotMatchesRecord(),
            SpotNearPreviousClose(calendar, shocks or NoShockFlags()),
            LegQuotesValid(),
            PreviousSessionFile(stores, NseDailyFoSource, calendar),
        )
    )


def build_data_gate(quote_folder: Path | None = None, schedule: ExecutionSchedule | None = None) -> DataGate:
    """The gate the desk runs before each decision; E3 passes its own execution schedule."""
    from ..composition import build_alert_sender, build_session_calendar
    from ..desk.wiring import build_execution_snapshots
    from ..storage.wiring import build_raw_stores

    checks = build_data_checks(build_raw_stores(), build_session_calendar())
    snapshots = build_execution_snapshots(quote_folder)
    return DataGate(checks, snapshots, schedule or PackSnapshotSchedule(), build_alert_sender())
