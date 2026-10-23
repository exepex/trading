"""A routine run's log in Drive (story O13): `begin`, one file per command, `end`. Each file is written the moment it
is known, so a run that dies midway still shows how far it got. A Drive failure never stops the routine: the call
returns the line to print and the routine carries on."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..storage.raw_store import RawFileStore
from .layout import BEGIN, END, RunFolder
from .run_state import OpenRun, RunStateFolder
from .scrub import scrub

NOT_SAVED = "routine log NOT saved to Drive ({what}): {error}"
SAVED = "routine log: {path}"
ERROR_CHARS = 160
STATUS_OK, STATUS_FAILED, STATUS_NONE = "ok", "failed", "no open run"
NO_RUN = "routine log: {routine} has no open run, nothing closed"
ORPHAN_NOTE = "step {step} had no open run (begin missing, or end came first): closed with it"
STALE_AFTER = timedelta(days=1)
STEP_HEADER = "routine {routine}\nstep {label}\ncommand {command}\nstarted {started}\nended {ended}\nexit {code}\n---\n"


@dataclass(frozen=True)
class StepResult:
    label: str
    command: str
    exit_code: int
    started: datetime
    ended: datetime
    output: str


class RoutineRunLog:
    def __init__(self, store: RawFileStore, state: RunStateFolder, clock: Callable[[], datetime]):
        self.store, self.state, self.clock = store, state, clock

    def begin(self, routine: str, session: str = "") -> tuple[OpenRun, str]:
        started = self.clock()
        run = OpenRun(RunFolder.new(routine, started))
        self.state.save(run)
        body = {"routine": routine, "started_at": started.isoformat(), "session": session}
        return run, self._put(run.folder.file(BEGIN), json.dumps(body, indent=1), "begin")

    def open_run(self, routine: str) -> OpenRun | None:
        """The routine's open run; None when there is none or it is a leftover older than a day (a machine that kept
        `work/routine-logs/`): a run crossing midnight stays open, yesterday's dead run never takes today's steps."""
        run = self.state.load(routine)
        fresh = run and self.clock() - run.folder.started_at(self.clock().tzinfo) < STALE_AFTER
        return run if fresh else None

    def step(self, routine: str, result: StepResult) -> tuple[str, str]:
        """Writes the step's file; returns (its Drive path, a line to print when it was not saved, else "")."""
        with self.state.locked(routine):
            run, begun = self.open_run(routine), ""
            orphan = run is None
            if orphan:  # `begin` never ran, or `end` came first: a run of its own, closed below, never "stuck"
                run, begun = self.begin(routine)
            run.steps += 1
            if result.exit_code != 0:
                run.failed.append(result.label)
            self.state.save(run)
        path = run.folder.step_file(run.steps, result.label)
        header = STEP_HEADER.format(routine=routine, label=result.label, command=result.command,
                                    started=result.started.isoformat(), ended=result.ended.isoformat(),
                                    code=result.exit_code)  # fmt: skip
        problem = self._put(path, scrub(header + result.output), result.label)
        if orphan:
            self.end(routine, ORPHAN_NOTE.format(step=result.label))
        return path, problem or begun

    def end(self, routine: str, note: str = "") -> tuple[str, str]:
        """Writes `end.json` (status `failed` when any step failed) and closes the run; returns (status, line)."""
        with self.state.locked(routine):
            run = self.open_run(routine)
            self.state.clear(routine)
        if run is None:  # nothing to close; an empty "ok" run would hide a failed one from the watcher
            return STATUS_NONE, NO_RUN.format(routine=routine)
        status = STATUS_FAILED if run.failed else STATUS_OK
        body = {"routine": routine, "ended_at": self.clock().isoformat(), "status": status, "steps": run.steps,
                "failed_steps": run.failed, "note": scrub(note)}  # fmt: skip
        problem = self._put(run.folder.file(END), json.dumps(body, indent=1), "end")
        return status, problem or SAVED.format(path=run.folder.path)

    def _put(self, path: str, text: str, what: str) -> str:
        try:
            self.store.put(path, text.encode("utf-8"))
        except Exception as error:  # noqa: BLE001 - any Drive failure is reported, never allowed to stop the routine
            return NOT_SAVED.format(what=what, error=scrub(f"{type(error).__name__}: {error}")[:ERROR_CHARS])
        return ""
