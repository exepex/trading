"""The AI books' minutes in BG1's usage ledger (story F8c; written by the G11 builder, 013xqaNT, and moved here): each
book's routine publishes its own timing of the run from its `reveal` step (`run_timing.py`, `timing_path`); the
Actions side reads every timing file with BG1's own reader (`SelfTimedUsageReader`) and records it in
`accounting/ai_usage.csv` as books-and-roles use of that book. The ledger records a session-day once, so every file is
offered on every run: one that landed after a collect is recorded by the next. A bad file is a refused line, never a
traceback and never a guessed row."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..budget.constants import PURPOSE_BOOKS_AND_ROLES
from ..budget.self_timed import SelfTimedUsageReader
from ..budget.usage_ledger import Attribution, UsageLedger, UsageRefused
from ..budget.usage_reader import ExportRefused
from ..constants import AI_BOOKS
from .paths import AI_FOLDER

TIMING_GLOB = "timing/*/*.timing.json"
LINE = "Omenix F&O AI books' minutes (BG1): {file}: {result}"
ALREADY = "already recorded"


@dataclass
class BookUsageRecorder:
    root: Path
    ledger: UsageLedger

    def record(self, today: date) -> list[str]:
        """One line per timing file newly recorded or refused; files already in the ledger print nothing."""
        lines = []
        for path in sorted((self.root / AI_FOLDER).glob(TIMING_GLOB)):
            name = path.relative_to(self.root).as_posix()
            try:
                results = self._record(path, today)
            except (ExportRefused, UsageRefused, ValueError) as refused:
                results = [f"refused: {refused}"]
            lines += [LINE.format(file=name, result=result) for result in results if ALREADY not in result]
        return lines

    def _record(self, path: Path, today: date) -> list[str]:
        book = path.name.removesuffix(".timing.json").split("_", 1)[-1]
        if book not in AI_BOOKS:
            raise ValueError(f"{book!r} in the file name is not an AI book")
        reader = SelfTimedUsageReader(path)
        return self.ledger.record(
            reader.days(), Attribution(PURPOSE_BOOKS_AND_ROLES, book), reader.complete_before(today)
        )
