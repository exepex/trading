"""Composition root of scoreboard B (story S2): the three books' records, E3's run logs and D3's stores, D6's versions,
the session calendar, the recorded execution snapshots for marks, C1's charges and operating costs, the AI cost until
F8, and the protocol's status (S1). Swapping any source changes this file only."""

from __future__ import annotations

from pathlib import Path

from ..books.account import PaperAccount
from ..books.versions import Versions
from ..config import ROOT
from ..constants import BOOKS
from ..desk.records import DeskRecords
from ..research_data.calendar import SessionCalendar
from .book_board import BookBoard
from .committed_runs import CommittedRuns
from .daily_values import DayMarks
from .entry_decisions import EntryDecisions
from .ports import ProtocolStatus
from .sources import AiCostBeforeF8, FileOperatingCosts, RecordedOwnerOverride, SnapshotMarks, input_hashes
from .whole_system import WholeSystemBoard


def board_from(
    root: Path, charges: dict, calendar: SessionCalendar, versions: Versions, marks: DayMarks,
    protocol: ProtocolStatus,
) -> WholeSystemBoard:  # fmt: skip
    runs = CommittedRuns(root)
    return WholeSystemBoard(
        BOOKS, lambda book: DeskRecords(PaperAccount(root, book)),
        lambda: EntryDecisions(runs.runs(), runs.records, versions, RecordedOwnerOverride()), calendar.sessions, marks,
        FileOperatingCosts(root), BookBoard(calendar.sessions, AiCostBeforeF8()), charges, protocol,
        lambda: input_hashes(root, BOOKS, runs.runs()), runs.uncollected,
    )  # fmt: skip


def build_whole_system_board(cfg: dict, root: Path = ROOT) -> WholeSystemBoard:
    from ..composition import build_session_calendar, build_versions
    from ..desk.wiring import build_execution_snapshots
    from .protocol_status import protocol_status

    marks = SnapshotMarks(build_execution_snapshots(), CommittedRuns(root).snapshot_ids())
    return board_from(
        root, cfg["charges"], build_session_calendar(), build_versions(root), marks, protocol_status(root)
    )
