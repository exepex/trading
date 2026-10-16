"""Story E2c fixtures: E3's daily run with the paper accounts in a fake Drive (A4b's local index store), E2's real
private pack in Drive and each day started in a fresh container (no local account folder, no local private pack)."""

from __future__ import annotations

import shutil
from datetime import time

from fno.books.paths import account_folder
from fno.constants import BOOK1_RULES, BOOKS
from fno.desk.drive_sync import DriveAccountSync
from fno.desk.pack_store import PackStore
from fno.desk.packs import WrittenPacks
from fno.desk.private_files import PrivateFiles
from fno.desk.private_pack import PrivatePackBuilder
from fno.desk.wiring import open_desk_journal
from fno.storage.index_store import LocalIndexStore

from .fakes import TIMETABLE, daily_run, pack_for


class CommonPacks:
    def build(self, day, cutoff):
        return pack_for(day)


def fresh_container(root) -> None:
    """What a new container's checkout holds of the private records: nothing (git-ignored, never committed)."""
    for book in BOOKS:
        shutil.rmtree(account_folder(root, book), ignore_errors=True)
    for pack in root.glob("journal/*/packs/*/private.json"):
        pack.unlink()


def drive_run(root, tmp_path, alerts, books, decisions, validity, rules, store=None):
    """`root`'s started accounts moved to Drive (the merge's one-time move), then removed locally."""
    files = PrivateFiles(lambda: store or LocalIndexStore(tmp_path / "drive"), root)
    files.move_accounts()
    fresh_container(root)
    run, clock, capture, commits = daily_run(root, tmp_path, alerts, books, decisions, validity, rules)
    run.files = files
    lease = TIMETABLE.lock_lease_seconds
    journal = lambda book: open_desk_journal(book, root, lease, files)  # noqa: E731
    run.steps.sync = DriveAccountSync(journal, run.committer, root)
    run.marking.open_journal = journal  # story E2d: the marks in the same Drive-backed journal
    run.steps.packs = WrittenPacks(CommonPacks(), PrivatePackBuilder(root), PackStore(root), time(15, 0),
                                   (BOOK1_RULES,), keep=files.push)  # fmt: skip
    return run, clock, capture, commits, files
