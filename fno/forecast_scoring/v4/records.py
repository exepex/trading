"""What a look writes and reads (story G8), and the freeze and slot registrations it depends on. Before protocol v4's
freeze record exists nothing is a look record: every output is exploratory. After it, each look's record is written
once (`look_<name>.json`) and never overwritten; look 2 reads look 1's to know which members closed."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from ...constants import V4_CLAIM
from ...forecast_v4.terms import LOOK_STOP_REVIEW

EXPLORATORY = "EXPLORATORY: protocol v4 not frozen; nothing here counts"


class LookRecordExists(RuntimeError):
    """A look's record is written once; a second write is refused."""


class SlotRegistry(ABC):
    @abstractmethod
    def registered(self) -> dict[tuple[str, str], str]:
        """(question, slot) -> the forecaster id registered for it in the ledger before its first counted forecast."""


class NoRegistrations(SlotRegistry):
    """Before the freeze writes its ledger row, no slot has a registered forecaster (Test A: undecided)."""

    def registered(self) -> dict[tuple[str, str], str]:
        return {}


class LookRecords:
    def __init__(self, folder: Path, freeze_file: Path):
        self.folder, self.freeze_file = Path(folder), Path(freeze_file)

    def frozen(self) -> bool:
        return self.freeze_file.is_file()

    def path(self, look: str) -> Path:
        return self.folder / f"look_{look}.json"

    def write(self, look: str, payload: dict) -> Path:
        path = self.path(look)
        if path.exists():
            raise LookRecordExists(f"{path.name} is already written; a look is recorded once")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def closed(self, look: str) -> set[tuple[str, str]]:
        """Members closed at look 1 (a claim or a futility "no"), for look 2; none for look 1."""
        if look == LOOK_STOP_REVIEW or not self.path(LOOK_STOP_REVIEW).is_file():
            return set()
        members = json.loads(self.path(LOOK_STOP_REVIEW).read_text(encoding="utf-8"))["members"]
        return {(m["question"], m["slot"]) for m in members if m["verdict"] == V4_CLAIM or m["futile"]}
