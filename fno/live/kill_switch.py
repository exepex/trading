"""A file flag that stops all trading at once: open trades are closed and no new ones open until released."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class KillSwitch:
    def __init__(self, flag_path: Path):
        self.flag_path = flag_path

    @property
    def engaged(self) -> bool:
        return self.flag_path.exists()

    @property
    def reason(self) -> str:
        return self.flag_path.read_text(encoding="utf-8").strip() if self.engaged else ""

    def engage(self, reason: str, at: datetime) -> None:
        self.flag_path.parent.mkdir(parents=True, exist_ok=True)
        self.flag_path.write_text(f"{at.isoformat(timespec='seconds')} {reason}\n", encoding="utf-8")

    def release(self) -> None:
        self.flag_path.unlink(missing_ok=True)
