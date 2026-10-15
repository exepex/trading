"""The run's guard (PROTOCOL.md section 19): the trial must be registered with its protocol frozen (B4's ledger guard),
every analysis file's SHA-256 must be in FREEZE.md, and git must see no change in the study folder."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from fno.research_engine.ledger import Ledger

from .contracts import REPOSITORY

FOLDER = Path(__file__).resolve().parents[1]
FROZEN = ("PROTOCOL.md", "study.py")
OUTPUTS = ("results.json", "results.md")


class NotFrozen(RuntimeError):
    """A file is not frozen, or the folder has an uncommitted change."""


def frozen_files(folder: Path = FOLDER) -> list[Path]:
    return [folder / name for name in FROZEN] + sorted((folder / "ft1study").glob("*.py"))


def check_frozen(trial: str, folder: Path = FOLDER) -> None:
    Ledger(REPOSITORY).require_registered(trial)
    freeze = (folder / "FREEZE.md").read_text(encoding="utf-8")
    unfrozen = [f.name for f in frozen_files(folder) if hashlib.sha256(f.read_bytes()).hexdigest() not in freeze]
    status = subprocess.run(["git", "status", "--porcelain", "--", str(folder)], capture_output=True, text=True)
    dirty = [line for line in status.stdout.splitlines() if not line.endswith(OUTPUTS)]
    if unfrozen or dirty or status.returncode:
        raise NotFrozen(f"not frozen: {unfrozen}; uncommitted: {dirty}")
