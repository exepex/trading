"""Composition root of the paper desk's daily run (story E3): the timetable from config.yaml, the A7 calendar, git for
commits and account writes across containers, the packs, Book 1's D6 version keeper, the recorder's execution capture
and its committed records, C3's data gate on them, and E4's desks. Each book's orders and exit rules (E5, F5, F6) and
C4's validity gate are passed in: C4 is one line here once it merges."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ..config import ROOT
from ..constants import BOOK1_RULES
from .daily_ports import ExitRules, OrderBuilder, ValidityGate, Waiter
from .daily_run import DailyRun
from .daily_steps import DeskSteps
from .timetable import timetable_from_config


def build_daily_run(cfg: dict, orders: OrderBuilder, validity: ValidityGate, exit_rules: ExitRules,
                    books: Sequence[str] = (BOOK1_RULES,), root: Path = ROOT,
                    waiter: Waiter | None = None) -> DailyRun:  # fmt: skip
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
    from .execution_capture import CommittedExecutionSchedule, RecorderExecutionCapture
    from .git_sync import Git, GitAccountSync, GitCommitter
    from .pack_wiring import build_packs
    from .sleeper import SleepingWaiter
    from .wiring import build_entry_desk, build_execution_snapshots, build_exit_desk, open_desk_journal

    timetable, calendar, git = timetable_from_config(cfg), build_session_calendar(), Git(root)
    committer, history = GitCommitter(git), PlaybookGit(root)
    sync = GitAccountSync(git, lambda book: open_desk_journal(book, root, timetable.lock_lease_seconds))
    packs = build_packs(root, refresh=lambda: git("pull", "-q", "--no-rebase", "--no-edit", "origin", git.branch()))
    versions = Book1Versions(build_playbook_loader(root), VersionRegistry(root / VERSIONS_FILE), history,
                             history.head, committer)  # fmt: skip
    capture = RecorderExecutionCapture(build_quote_recorder(cfg).capture, build_quote_store(), QUOTES_FOLDER, root,
                                       committer)  # fmt: skip
    gate = DataGate(build_data_checks(build_raw_stores(), calendar), build_execution_snapshots(),
                    CommittedExecutionSchedule(root, timetable), build_alert_sender())  # fmt: skip
    steps = DeskSteps(root, books, timetable, versions, packs, D3CommittedDecisions(root, history, orders), capture,
                      gate, validity, sync, build_entry_desk(cfg), build_exit_desk(cfg), exit_rules)  # fmt: skip
    return DailyRun(steps, calendar, committer, waiter or SleepingWaiter(now_ist), now_ist)
