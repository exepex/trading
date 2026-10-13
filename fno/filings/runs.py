"""The filings archive's run log (story A12): one row per run, committed with the manifests. It shows the backfill's
progress, and lets the scheduled job do the daily check once a day after a complete run.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .librarian import FilingsReport

RUN_FIELDS = ("started", "finished", "companies", "checked", "saved", "already_there", "gaps", "failures", "result")
COMPLETE, INCOMPLETE = "complete", "incomplete"


class RunLog:
    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, started: datetime, finished: datetime, report: FilingsReport) -> None:
        new_file = not self.path.is_file()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="") as out:
            writer = csv.writer(out, lineterminator="\n")
            if new_file:
                writer.writerow(RUN_FIELDS)
            writer.writerow(
                (
                    started.isoformat(timespec="seconds"),
                    finished.isoformat(timespec="seconds"),
                    report.companies,
                    len(report.checked),
                    report.saved,
                    report.present,
                    len(report.gaps),
                    len(report.failures),
                    COMPLETE if report.complete else INCOMPLETE,
                )
            )

    def last_complete(self, companies: int) -> datetime | None:
        """When the latest complete run over that many companies finished (None if none was): a trial run over a
        few symbols never stands for the whole list."""
        if not self.path.is_file():
            return None
        rows = csv.DictReader(self.path.read_text(encoding="utf-8").splitlines())
        finished = [
            datetime.fromisoformat(r["finished"])
            for r in rows
            if r["result"] == COMPLETE and int(r["companies"]) == companies
        ]
        return max(finished) if finished else None
