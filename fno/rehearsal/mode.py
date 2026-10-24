"""The rehearsal's identity, carried to every child process in one environment variable (`ENV_FNO_REHEARSAL`): the
replayed day, the run id and the folder holding the shared replay clock. A real run has none."""

from __future__ import annotations

import json
import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..constants import ENV_FNO_REHEARSAL
from ..models import now_utc

DRYRUN_ROOT = "dryrun"
BRANCH_PREFIX = "rehearsal/"
LABEL = "*DRY RUN, {day} replay, not a real trading day*\nNot yet in rehearsal: {pending}"
# The parts of the day not yet replayed (the orchestrator's addition 3): named in every post until each part lands
NOT_YET_IN_REHEARSAL = (
    "Groww's and NSE's recorded captures (REH1b)",
    "the pre-open, morning and evening routines (REH1c)",
)
RUN_ID_TIME = "%Y%m%dT%H%M%SZ"


@dataclass(frozen=True)
class Rehearsal:
    day: date
    run_id: str
    state: Path  # the replay clock's folder, shared by the parent and every child
    record: Path  # the checkout the rehearsal started from: its receipts are the real record it may read

    @classmethod
    def new(cls, day: date, home: Path, record: Path) -> Rehearsal:
        run_id = f"{now_utc().strftime(RUN_ID_TIME)}-{secrets.token_hex(3)}"
        return cls(day, run_id, Path(home) / run_id / "state", Path(record))

    @property
    def drive_root(self) -> str:
        return f"{DRYRUN_ROOT}/{self.run_id}"

    @property
    def branch(self) -> str:
        return f"{BRANCH_PREFIX}{self.day.isoformat()}-{self.run_id}"

    @property
    def label(self) -> str:
        return LABEL.format(day=self.day.isoformat(), pending="; ".join(NOT_YET_IN_REHEARSAL) or "nothing")

    def to_env(self) -> str:
        return json.dumps({"day": self.day.isoformat(), "run_id": self.run_id, "state": str(self.state),
                           "record": str(self.record)})  # fmt: skip

    @classmethod
    def from_env(cls, text: str) -> Rehearsal:
        data = json.loads(text)
        return cls(date.fromisoformat(data["day"]), data["run_id"], Path(data["state"]), Path(data["record"]))


def labelled(label: str, text: str) -> str:
    return f"{label}\n{text}"


def rehearsal(env: Mapping[str, str] = os.environ) -> Rehearsal | None:
    """The process's rehearsal, or None in a real run. Read only by composition roots."""
    text = env.get(ENV_FNO_REHEARSAL)
    return Rehearsal.from_env(text) if text else None
