"""What the watcher found for one expected start of one routine, and the alert line that names its likely cause."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

MISSING, STUCK, FAILED = "missing", "stuck", "failed"
TITLE = {
    MISSING: "did not start, or stopped before its first logged step",
    STUCK: "started but has not finished",
    FAILED: "finished with a failed step",
}
HINT = {
    MISSING: "likely cause: the scheduled task did not fire, setup failed, or the session stopped early; open the "
    "task's last run at claude.ai/code/routines",
    STUCK: "likely cause: the session ended or hung inside the step below",
    FAILED: "the failing step's last lines are below",
}
ALERT = "Omenix F&O routine {routine} ({start} IST) {title}. {hint}.{where}{lines}"


def run_key(routine: str, run: str, kind: str = FAILED) -> str:
    return f"{routine}-{run}-{kind}"


@dataclass(frozen=True)
class Finding:
    routine: str
    day: date  # the IST day of the expected start: its alert marker lives there
    start: time
    kind: str
    run_path: str = ""
    step: str = ""
    lines: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        """One alert per finding: a run's finding by its run (a failed one: the in-run alert's key), a missing one by
        its slot."""
        if self.run_path:
            return run_key(self.routine, self.run_path.rsplit("/", 1)[-1], self.kind)
        return f"{self.routine}-{self.start:%H%M}-{self.kind}"

    def alert_text(self) -> str:
        where = f" Log: Drive logs/routines/{self.run_path}" + (f", step {self.step}." if self.step else ".")
        lines = ("\n" + "\n".join(self.lines)) if self.lines else ""
        return ALERT.format(routine=self.routine, start=f"{self.start:%H:%M}", title=TITLE[self.kind],
                            hint=HINT[self.kind], where=where if self.run_path else "", lines=lines)  # fmt: skip
