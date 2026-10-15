"""The committed decision runs the desk used, read from E3's daily run logs (`journal/runs/<day>.json`) and D3's
stores (story S2). A run counts only when the day's log names it (run ID and holding commit): a run decided but not
collected by the deadline was never the book's decision. It is on time when it was committed before the day's
execution snapshot started (E3's late rule)."""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..constants import JOURNAL_FOLDER, RUN_LOG_DECISIONS_STEP
from ..desk.run_log import RUNS_FOLDER
from ..playbook.decision_store import INPUTS_FILE, DecisionStore

DECISIONS_STEP, SNAPSHOT_STEP = RUN_LOG_DECISIONS_STEP, "snapshot"


@dataclass(frozen=True)
class DayRun:
    book: str
    day: date
    run_id: str
    commit: str
    on_time: bool


class CommittedRuns:
    def __init__(self, root: Path):
        self.root = Path(root)

    def logs(self) -> Iterator[tuple[date, dict]]:
        folder = self.root / JOURNAL_FOLDER / RUNS_FOLDER
        for path in sorted(folder.glob("*.json")) if folder.is_dir() else ():
            yield date.fromisoformat(path.stem), json.loads(path.read_text(encoding="utf-8"))["steps"]

    def runs(self) -> list[DayRun]:
        found = []
        for day, steps in self.logs():
            snapshot = steps.get(SNAPSHOT_STEP)
            started = datetime.fromisoformat(snapshot["started_at"]) if snapshot else None
            for book, entry in sorted(steps.get(DECISIONS_STEP, {}).get("result", {}).items()):
                if "run_id" in entry:
                    late = started is None or datetime.fromisoformat(entry["committed_at"]) >= started
                    found.append(DayRun(book, day, entry["run_id"], entry["commit"], not late))
        return found

    def uncollected(self, books: Sequence[str]) -> dict[str, list[dict]]:
        """Each book's runs the decisions step saw but did not collect (story D3b), with corrections: shown apart on
        the board, never scored."""
        found: dict[str, list[dict]] = {book: [] for book in books}
        for day, steps in self.logs():
            for book, entry in sorted(steps.get(DECISIONS_STEP, {}).get("result", {}).items()):
                found.setdefault(book, []).extend({"day": day.isoformat(), **o} for o in entry.get("others", ()))
        return found

    def snapshot_ids(self) -> dict[date, str]:
        """Each day's valid execution snapshot, the one the day's fills and marks used."""
        ids = {}
        for day, steps in self.logs():
            result = steps.get(SNAPSHOT_STEP, {}).get("result", {})
            if result.get("valid"):
                ids[day] = result["snapshot_id"]
        return ids

    def records(self, run: DayRun) -> list[dict]:
        folder = DecisionStore(self.root, run.book).day_folder(run.day) / run.run_id
        paths = sorted(p for p in folder.glob("*.json") if p.name != INPUTS_FILE)
        return [json.loads(p.read_text(encoding="utf-8")) for p in paths]
