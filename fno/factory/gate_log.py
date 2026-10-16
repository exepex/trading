"""The gate log (story R1): `research/factory/gates.csv`, one row per gate an idea reached, append-only.

B4's ledger keeps its ten columns, so an idea's status is the last row of its trial here. The guard refuses an edit or
deletion of any earlier row, in the working file or anywhere in its git history (D1's append-only check)."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import astuple, dataclass
from pathlib import Path
from typing import Protocol

from ..playbook.registry import rewritten_history
from .constants import GATE_COLUMNS, GATES_FILE, NUMBERS_PATTERN, Gate, Outcome


class GateLogError(ValueError):
    """The gate log is refused: a bad row, or an earlier row edited or deleted."""


class FileHistory(Protocol):
    def file_versions(self, path: str) -> list[str]: ...


@dataclass(frozen=True)
class GateRow:
    trial_id: str
    gate: str
    outcome: str
    on: str  # ISO date the gate ran
    commit: str  # the commit the gate ran at
    numbers: str  # the gate's own figures as k=v;k=v, never a market value of a test's outcomes


def _check_row(row: GateRow) -> None:
    if not row.trial_id.isdigit():
        raise GateLogError(f"trial id {row.trial_id!r} is not a ledger trial number")
    if row.gate not in set(Gate) or row.outcome not in set(Outcome):
        raise GateLogError(f"trial {row.trial_id}: unknown gate {row.gate!r} or outcome {row.outcome!r}")
    if not re.match(NUMBERS_PATTERN, row.numbers):
        raise GateLogError(f"trial {row.trial_id}: numbers {row.numbers!r} are not k=v;k=v")


def parse_gate_rows(text: str) -> list[GateRow]:
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header is not None and tuple(header) != GATE_COLUMNS:
        raise GateLogError(f"{GATES_FILE} columns must be {GATE_COLUMNS}")
    rows = [GateRow(*line) for line in reader if line]
    for row in rows:
        _check_row(row)
    return rows


def _render(*lines: tuple) -> str:
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(lines)
    return out.getvalue()


class GateLog:
    def __init__(self, root: Path, history: FileHistory):
        self.file = Path(root) / GATES_FILE
        self.history = history

    def _text(self) -> str:
        return self.file.read_text(encoding="utf-8") if self.file.is_file() else ""

    def rows(self) -> list[GateRow]:
        return parse_gate_rows(self._text())

    def last(self, trial_id: str) -> GateRow | None:
        mine = [row for row in self.rows() if row.trial_id == trial_id]
        return mine[-1] if mine else None

    def history_problems(self) -> list[str]:
        """Earlier rows edited or deleted, in git history or in the working file (empty when append-only)."""
        current = [self._text()] if self.file.is_file() else []
        return rewritten_history(self.history.file_versions(GATES_FILE) + current)

    def require_append_only(self) -> None:
        problems = self.history_problems()
        if problems:
            raise GateLogError(f"{GATES_FILE} history is not append-only: {'; '.join(problems)}")
        self.rows()  # every row valid

    def append(self, row: GateRow) -> None:
        self.require_append_only()
        _check_row(row)
        before = self._text() or _render(GATE_COLUMNS)
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(before + _render(astuple(row)), encoding="utf-8")
