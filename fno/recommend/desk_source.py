"""Book 1's decisions of the day as a candidate source (story REC1b, section 5): `complete` only when the run log
names the day's decision run and every file of that run matches its `records.sha256` line. A step that failed, was
refused or never ran makes the source unavailable with that status; a file whose hash differs is an input failure."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from ..constants import BOOK1_RULES
from ..desk.run_log import RunLog, book_results
from .constants import CandidateSourceName, SourceState
from .contracts import CandidateSource
from .ports import CandidateSourcePort, InputFailed, SeenDecision, SourceReading
from .refs import RecordRef

DECISIONS_STEP = "decisions"
MANIFEST = "records.sha256"
NOT_DECISIONS = {MANIFEST, "inputs.json"}  # the run's own files that are not decisions
TRADE = "trade"
NO_RUN = "{status} ({why})"
BAD_HASH = "{path}: its SHA-256 is not the one in records.sha256"
NOT_LISTED = "{path}: not in records.sha256"


class DeskSource(CandidateSourcePort):
    name = CandidateSourceName.DESK_BOOK1

    def __init__(self, root: Path, journal: Path, book: str = BOOK1_RULES):
        """`journal`: the folder that holds `<book>/decisions/<day>/<run>/`."""
        self.root, self.journal, self.book = root, journal, book

    def read(self, day: date) -> SourceReading:
        log = RunLog.open(self.root, day)
        entry = book_results(log.result(DECISIONS_STEP)).get(self.book) if log.done(DECISIONS_STEP) else None
        if not entry or "run_id" not in entry:
            return _unavailable(_why_not(log))
        folder = self.journal / self.book / "decisions" / day.isoformat() / entry["run_id"]
        listed = _manifest(folder)
        decisions = tuple(_decision(self.root, path, listed) for path in sorted(folder.glob("*.json"))
                          if path.name not in NOT_DECISIONS)  # fmt: skip
        source = CandidateSource(self.name, SourceState.COMPLETE, None)
        return SourceReading(source, decisions, (_ref(self.root, folder / MANIFEST),))


def _why_not(log: RunLog) -> str:
    if not log.done(DECISIONS_STEP):
        return NO_RUN.format(status="missing", why="the decisions step is not in the run log")
    result = log.result(DECISIONS_STEP)
    return NO_RUN.format(status=result.get("status", "ok"), why=result.get("reason", "no Book 1 decision run"))


def _unavailable(status: str) -> SourceReading:
    return SourceReading(CandidateSource(CandidateSourceName.DESK_BOOK1, SourceState.UNAVAILABLE, status), (), ())


def _manifest(folder: Path) -> dict[str, str]:
    try:
        lines = (folder / MANIFEST).read_text(encoding="utf-8").splitlines()
    except OSError as missing:
        raise InputFailed(f"{folder.name}/{MANIFEST}: {type(missing).__name__}") from None
    return {name: digest for digest, name in (line.split(maxsplit=1) for line in lines if line.strip())}


def _decision(root: Path, path: Path, listed: dict[str, str]) -> SeenDecision:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    relative = path.relative_to(root).as_posix()
    if path.name not in listed:
        raise InputFailed(NOT_LISTED.format(path=relative))
    if listed[path.name] != digest:
        raise InputFailed(BAD_HASH.format(path=relative))
    record = json.loads(data)
    version = record.get("version_id") or record["book"]  # the day record of a book with no version names the book
    return SeenDecision(version, RecordRef(relative, digest), record["decision"]["action"] == TRADE)


def _ref(root: Path, path: Path) -> RecordRef:
    return RecordRef(path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
