"""Where a routine run's files live in Drive's `logs/routines` area: one folder per IST day, one per routine, one per
run (`<HHMMSS>-<token>`, sortable by start time), holding `begin.json`, one `steps/<NN>-<label>.log` per command and
`end.json`. Every file is written once; a later step is a new file, so a run that dies keeps what it wrote."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import date, datetime

LOGS_AREA = "logs/routines"
BEGIN, END, STEPS = "begin.json", "end.json", "steps"
NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
BAD_NAME = "a routine or step name is 1-48 lower-case letters, digits and hyphens: {name!r}"


def check_name(name: str) -> str:
    if not NAME.match(name):
        raise ValueError(BAD_NAME.format(name=name))
    return name


@dataclass(frozen=True)
class RunFolder:
    day: date
    routine: str
    run: str  # "<HHMMSS>-<token>"

    @classmethod
    def new(cls, routine: str, started: datetime) -> RunFolder:
        return cls(started.date(), check_name(routine), f"{started:%H%M%S}-{secrets.token_hex(3)}")

    @property
    def routine_folder(self) -> str:
        return f"{self.day.isoformat()}/{self.routine}"

    @property
    def path(self) -> str:
        return f"{self.routine_folder}/{self.run}"

    def file(self, name: str) -> str:
        return f"{self.path}/{name}"

    def step_file(self, number: int, label: str) -> str:
        return f"{self.path}/{STEPS}/{number:02d}-{check_name(label)}.log"

    def started_hhmm(self) -> str:
        return f"{self.run[:2]}:{self.run[2:4]}"
