"""Where the desk keeps its results: append-only JSONL files in this repo (saved to GitHub at the end of each day).

The interface stays the same when results move to a database later (see duckdb_results_store.py for one).
Only compact results are stored here, never raw minute-by-minute market data.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from ..models import IST

log = logging.getLogger(__name__)

EVENT_KINDS = ("scan", "idea", "rejected", "opened", "closed", "kill_switch")


class ResultsStore(ABC):
    """Append-only event log. Implementations log errors instead of raising: storage must not stop the desk."""

    @property
    @abstractmethod
    def location(self) -> str: ...

    @abstractmethod
    def record(self, kind: str, payload: dict, at: datetime, symbol: str | None = None) -> None: ...

    @abstractmethod
    def count(self, kind: str | None = None) -> int: ...

    def close(self) -> None:  # noqa: B027 - optional hook
        """Release connections, if any."""


class JsonlResultsStore(ResultsStore):
    """One file per IST day: <root>/YYYY/MM/YYYY-MM-DD.jsonl, the same layout as the stock tool's data."""

    def __init__(self, root: Path):
        self.root = root

    @property
    def location(self) -> str:
        return str(self.root)

    def _file_for(self, at: datetime) -> Path:
        day = at.astimezone(IST).date()
        return self.root / f"{day:%Y}" / f"{day:%m}" / f"{day.isoformat()}.jsonl"

    def record(self, kind: str, payload: dict, at: datetime, symbol: str | None = None) -> None:
        line = {"recorded_at": at.isoformat(timespec="seconds"), "kind": kind, "symbol": symbol, "payload": payload}
        path = self._file_for(at)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, default=str) + "\n")
        except OSError as exc:
            log.error("could not store %s event: %s", kind, exc)

    def count(self, kind: str | None = None) -> int:
        total = 0
        for path in self.root.rglob("*.jsonl"):
            with path.open(encoding="utf-8") as handle:
                total += sum(1 for line in handle if kind is None or json.loads(line)["kind"] == kind)
        return total
