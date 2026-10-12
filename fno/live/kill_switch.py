"""A file flag that stops all trading at once: open trades are closed and no new ones open until released."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..models import IST, now_ist

RELEASED_SUFFIX = ".released"


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

    @property
    def released_at(self) -> datetime | None:
        """When a person last released the switch: the automatic stop then judges only trades closed after it."""
        marker = self._released_marker
        if not marker.exists():
            return None
        released = datetime.fromisoformat(marker.read_text(encoding="utf-8").strip())
        return released if released.tzinfo else released.replace(tzinfo=IST)  # a hand-edited time is IST

    def release(self, at: datetime | None = None) -> None:
        self.flag_path.unlink(missing_ok=True)
        self._released_marker.parent.mkdir(parents=True, exist_ok=True)
        self._released_marker.write_text((at or now_ist()).isoformat(timespec="seconds"), encoding="utf-8")

    @property
    def _released_marker(self) -> Path:
        return self.flag_path.with_name(self.flag_path.name + RELEASED_SUFFIX)
