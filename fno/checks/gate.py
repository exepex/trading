"""The data gate before every decision (story C3): reads the scheduled capture, runs every data check on it and the
common pack, and alerts #fno-desk when any fails. Entries are refused on any failure; exits use the report to wait for
valid quotes when the prices are unverified (E4's exit path)."""

from __future__ import annotations

from collections.abc import Sequence

from ..alerts.sender import AlertSender
from ..desk.common_pack import CommonPack
from ..desk.snapshot import ContractKey, ExecutionSnapshot, ExecutionSnapshotSource, SnapshotError
from .data_checks import CheckReport, CheckSubject, DataChecks
from .schedule import ExecutionSchedule

ALERT = "F&O paper desk {day} ({snapshot}): {reason}"


class DataGate:
    def __init__(
        self, checks: DataChecks, snapshots: ExecutionSnapshotSource, schedule: ExecutionSchedule, alerts: AlertSender
    ):
        self.checks, self.snapshots, self.schedule, self.alerts = checks, snapshots, schedule, alerts

    def check(self, pack: CommonPack, legs: Sequence[ContractKey] = ()) -> tuple[ExecutionSnapshot | None, CheckReport]:
        """The day's execution snapshot (None when it cannot be read) and the checks' report on it, for these legs."""
        capture = self.schedule.capture(pack)
        snapshot, unreadable = None, ""
        if capture is not None:
            try:
                snapshot = self.snapshots.snapshot(pack.day, capture.snapshot_id)
            except SnapshotError as problem:
                unreadable = str(problem)
        report = self.checks.run(CheckSubject(pack, capture, snapshot, unreadable, tuple(legs)))
        if not report.ok:
            name = capture.snapshot_id if capture else "no capture"
            self.alerts.send(ALERT.format(day=pack.day, snapshot=name, reason=report.reason()))
        return snapshot, report
