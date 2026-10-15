"""Composition root of the paper desk's daily run (story E3): the timetable from config.yaml, the A7 calendar, git for
commits and account writes across containers, the packs, Book 1's D6 version keeper, the recorder's execution capture
and its committed records, C3's data gate on them, C4's pass as recorded in the committed D3 record (judge 83), and
E4's desks. Each book's orders and exit rules (E5, F5, F6) are passed in, and so are story O1's own steps around the
desk's (with the waiter that commits its quote parts, and the git checkout they share)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from ..config import ROOT
from ..constants import BOOK1_RULES
from .daily_ports import DayStep, ExitRules, OrderBuilder, Waiter
from .daily_run import DailyRun
from .daily_steps import DeskSteps
from .timetable import timetable_from_config


def build_daily_run(cfg: dict, orders: OrderBuilder, exit_rules: ExitRules,
                    books: Sequence[str] = (BOOK1_RULES,), root: Path = ROOT,
                    waiter: Waiter | None = None, day_steps: Mapping[str, DayStep] | None = None,
                    git=None, alerts=None) -> DailyRun:  # fmt: skip
    from ..books.version_registry import VersionRegistry
    from ..books.versions import VERSIONS_FILE
    from ..checks.gate import DataGate
    from ..checks.wiring import build_data_checks
    from ..composition import build_alert_sender, build_quote_recorder, build_session_calendar
    from ..models import now_ist
    from ..playbook.history import PlaybookGit
    from ..playbook.wiring import build_playbook_loader
    from ..storage.wiring import QUOTES_FOLDER, build_quote_store, build_raw_stores
    from .book_versions import Book1Versions
    from .committed_decisions import D3CommittedDecisions
    from .drive_sync import DriveAccountSync
    from .execution_capture import CommittedExecutionSchedule, RecorderExecutionCapture
    from .git_sync import Git, GitCommitter
    from .pack_wiring import build_packs
    from .pending_commit import PendingCommitter
    from .recorded_c4 import RecordedC4Pass
    from .sleeper import SleepingWaiter
    from .wiring import (
        build_entry_desk,
        build_execution_snapshots,
        build_exit_desk,
        build_private_files,
        open_desk_journal,
    )

    timetable, calendar, git = timetable_from_config(cfg), build_session_calendar(), git or Git(root)
    committer, history = PendingCommitter(GitCommitter(git), root), PlaybookGit(root)
    alerts, files = alerts or build_alert_sender(), build_private_files(root)
    sync = DriveAccountSync(lambda book: open_desk_journal(book, root, timetable.lock_lease_seconds, files), committer,
                            root)  # fmt: skip
    pull = lambda: git("pull", "-q", "--no-rebase", "--no-edit", "origin", git.branch())  # noqa: E731
    packs = build_packs(root, refresh=pull, files=files)
    versions = Book1Versions(build_playbook_loader(root), VersionRegistry(root / VERSIONS_FILE), history,
                             history.head, committer)  # fmt: skip
    capture = RecorderExecutionCapture(build_quote_recorder(cfg).capture, build_quote_store(), QUOTES_FOLDER, root,
                                       committer)  # fmt: skip
    gate = DataGate(build_data_checks(build_raw_stores(), calendar), build_execution_snapshots(),
                    CommittedExecutionSchedule(root, timetable), alerts)  # fmt: skip
    decisions = D3CommittedDecisions(root, history)
    steps = DeskSteps(root, books, timetable, versions, packs, decisions, orders, capture, gate, RecordedC4Pass(), sync,
                      build_entry_desk(cfg), build_exit_desk(cfg, alerts), exit_rules, alerts, now_ist)  # fmt: skip
    return DailyRun(steps, calendar, committer, waiter or SleepingWaiter(now_ist), now_ist, files, day_steps)
