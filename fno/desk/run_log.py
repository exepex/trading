"""The daily run's log (story E3 criterion 6): `journal/runs/<date>.json` holds, for every step, its start and end
time, its inputs and its result, in the order the steps ran. It is rewritten whole after each step (written to a
temporary file, then renamed) and committed, so a restarted run reads which steps are done and repeats none of them."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from ..constants import JOURNAL_FOLDER

RUNS_FOLDER = "runs"


@dataclass
class RunLog:
    day: date
    path: Path
    steps: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def open(cls, root: Path, day: date) -> RunLog:
        path = Path(root) / JOURNAL_FOLDER / RUNS_FOLDER / f"{day.isoformat()}.json"
        steps = json.loads(path.read_text(encoding="utf-8"))["steps"] if path.is_file() else {}
        return cls(day, path, steps)

    def done(self, step: str) -> bool:
        return step in self.steps

    def result(self, step: str) -> dict:
        return self.steps[step]["result"]

    def record(self, step: str, started: datetime, finished: datetime, inputs: dict, result: dict) -> None:
        if self.done(step):
            raise ValueError(f"{self.day} step {step} is already recorded: a run never repeats a step")
        self.steps[step] = {"started_at": started.isoformat(), "finished_at": finished.isoformat(),
                            "inputs": inputs, "result": result}  # fmt: skip
        self._write()

    def _write(self) -> None:
        body = {"day": self.day.isoformat(), "kind": "daily_run", "steps": self.steps}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(json.dumps(body, indent=1, sort_keys=False) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)
