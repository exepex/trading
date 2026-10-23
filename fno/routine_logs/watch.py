"""Finds the expected routine runs of a day that are missing, stuck or failed, from the logs in Drive alone (story
O13), and alerts each once: a marker in `<day>/_alerts/` records every sent alert, so the hourly watcher and the
run's own failure line never repeat each other."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, time, timedelta

from ..alerts.sender import SENT, AlertSender
from ..storage.raw_store import RawFileStore
from .findings import FAILED, MISSING, STUCK, Finding
from .layout import END, STEPS
from .schedule import GRACE_MINUTES, RoutineSpec

EARLY_MINUTES = 10  # a run that starts up to this long before its slot still belongs to it
ALERTS_FOLDER = "_alerts"
LINES_SHOWN = 12
STEP_BODY = "\n---\n"


def alert_marker(day: date, key: str) -> str:
    return f"{day.isoformat()}/{ALERTS_FOLDER}/{key}.txt"


def step_tail(store: RawFileStore, path: str, count: int = LINES_SHOWN) -> tuple[str, ...]:
    data = store.get(path)
    if data is None:
        return ()
    body = data.decode("utf-8", "replace").split(STEP_BODY, 1)[-1]
    return tuple(line for line in body.splitlines() if line.strip())[-count:]


class RoutineWatcher:
    def __init__(self, store: RawFileStore, specs: tuple[RoutineSpec, ...], is_session: Callable[[date], bool],
                 clock: Callable[[], datetime]):  # fmt: skip
        self.store, self.specs, self.is_session, self.clock = store, specs, is_session, clock

    def findings(self) -> list[Finding]:
        now = self.clock()
        day, session = now.date(), self.is_session(now.date())
        found: list[Finding] = []
        for spec in self.specs:
            if spec.due_on(day, session):
                found += self._spec_findings(spec, day, now)
        return found

    def _spec_findings(self, spec: RoutineSpec, day: date, now: datetime) -> list[Finding]:
        runs = sorted(self.store.folders(f"{day.isoformat()}/{spec.name}"))
        found = []
        for index, start in enumerate(spec.starts):
            if now < _at(now, start) + timedelta(minutes=GRACE_MINUTES):
                continue
            later = spec.starts[index + 1] if index + 1 < len(spec.starts) else None
            slot_runs = [run for run in runs if _in_slot(run, start, later)]
            finding = self._slot_finding(spec, day, now, start, slot_runs)
            if finding:
                found.append(finding)
        return found

    def _slot_finding(self, spec, day, now, start: time, runs: list[str]) -> Finding | None:
        if not runs:
            return Finding(spec.name, start, MISSING)
        run = runs[-1]
        path = f"{day.isoformat()}/{spec.name}/{run}"
        end = self.store.get(f"{path}/{END}")
        if end is not None:
            failed = json.loads(end).get("failed_steps") or []
            if not failed:
                return None
            step_path = self._step_path(path, failed[0])
            return Finding(spec.name, start, FAILED, path, failed[0], step_tail(self.store, step_path))
        if now < _at(now, _run_time(run)) + timedelta(minutes=spec.max_minutes):
            return None
        steps = sorted(self.store.checksums(f"{path}/{STEPS}"))
        last = steps[-1] if steps else ""
        lines = step_tail(self.store, f"{path}/{STEPS}/{last}") if last else ()
        return Finding(spec.name, start, STUCK, path, last.removesuffix(".log"), lines)

    def _step_path(self, path: str, label: str) -> str:
        names = [name for name in sorted(self.store.checksums(f"{path}/{STEPS}")) if name.endswith(f"-{label}.log")]
        return f"{path}/{STEPS}/{names[0]}" if names else ""

    def alert_new(self, sender: AlertSender, out: Callable[[str], None] = print) -> int:
        """Sends every finding not alerted yet and marks it; returns how many could not be sent."""
        unsent = 0
        for finding in self.findings():
            marker = alert_marker(self.clock().date(), finding.key)
            if self.store.get(marker) is not None:
                continue
            outcome = sender.send(finding.alert_text())
            out(f"{finding.key}: {outcome}")
            if outcome == SENT:
                self.store.put(marker, outcome.encode())
            else:
                unsent += 1
        return unsent


def _at(now: datetime, moment: time) -> datetime:
    return now.replace(hour=moment.hour, minute=moment.minute, second=moment.second, microsecond=0)


def _run_time(run: str) -> time:
    return time(int(run[:2]), int(run[2:4]), int(run[4:6]))


def _minutes(moment: time) -> int:
    return moment.hour * 60 + moment.minute


def _in_slot(run: str, start: time, later: time | None) -> bool:
    at = _minutes(_run_time(run))
    return _minutes(start) - EARLY_MINUTES <= at < (_minutes(later) - EARLY_MINUTES if later else 24 * 60)
