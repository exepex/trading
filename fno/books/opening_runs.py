"""Which decision run opened each of a book's trades (story D3b): the source of truth for a trade's terms and exit.

A trade's opening run is the run E3's decisions step collected for the book on the trade's entry day (its first open
fill), as that day's run log names it. A fill row's `decision_id` is the record's opportunity ID, which does not name
the run, so the run log is the source. Only trades opened by fills are the book's: a run never collected, or a chosen
trade never filled, adds nothing.

When the run log is missing, names no run, or names a run that is gone or does not match its committed
`records.sha256` (an edit, or its sums file changed since the commit the log names), there is no opening run: the
problem is named, and nothing falls back to another run, least of all the latest record."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..books.account import PaperAccount
from ..constants import FILL_OPEN, RUN_LOG_DECISIONS_STEP
from ..desk.records import DeskRecords
from ..desk.run_log import RunLog
from ..playbook.decision_store import SUMS_FILE, DecisionStore

NO_LOG = "the run log of {day} names no decision of {book}"
GONE = "its opening run {run} (run log of {day}) is not in the decision store"
CHANGED = "its opening run {run} does not match the records.sha256 committed in {commit}"

SumsAt = Callable[[str, str], bytes | None]  # (repository path, commit) -> the file's bytes at that commit


@dataclass(frozen=True)
class OpeningRuns:
    runs: Mapping[str, Path]  # trade ID -> the run that opened it
    problems: Mapping[str, str]  # trade ID -> why it has no opening run


def opening_runs(root: Path, book: str, sums_at: SumsAt) -> OpeningRuns:
    runs, problems = {}, {}
    for trade_id, day in _entry_days(root, book).items():
        found = _opening_run(Path(root), book, day, sums_at)
        if isinstance(found, Path):
            runs[trade_id] = found
        else:
            problems[trade_id] = found
    return OpeningRuns(runs, problems)


def _entry_days(root: Path, book: str) -> dict[str, date]:
    days: dict[str, date] = {}
    for row in DeskRecords(PaperAccount(root, book)).fill_rows():
        if row["action"] == FILL_OPEN:
            day = datetime.fromisoformat(row["filled_at"]).date()
            days[row["trade_id"]] = min(day, days.get(row["trade_id"], day))
    return days


def _opening_run(root: Path, book: str, day: date, sums_at: SumsAt) -> Path | str:
    log = RunLog.open(root, day)
    entry = log.result(RUN_LOG_DECISIONS_STEP).get(book, {}) if log.done(RUN_LOG_DECISIONS_STEP) else {}
    if "run_id" not in entry:
        return NO_LOG.format(day=day, book=book)
    run = DecisionStore(root, book).day_folder(day) / entry["run_id"]
    if not run.is_dir():
        return GONE.format(run=entry["run_id"], day=day)
    sums = run / SUMS_FILE
    committed = sums_at(sums.relative_to(root).as_posix(), entry["commit"])
    if committed is None or not sums.is_file() or committed != sums.read_bytes() or DecisionStore.edited(run):
        return CHANGED.format(run=entry["run_id"], commit=entry["commit"])
    return run
