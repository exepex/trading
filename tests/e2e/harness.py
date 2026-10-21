"""Story O2: one fixture day of `python -m fno daily run` through its real composition root (`fno/daily/wiring.py`),
in a fresh checkout with its own `origin`, with only the outside services replaced (`OUTSIDE_SEAMS`, criterion 6).

The checkout is a temporary git repository holding the playbook and the version registry; the paper accounts are in
the fake Drive, as E2c keeps them, and the container starts without them. The package's own `ROOT` files (calendar,
closes, events, config) are read as they are, never written. The quote store is the real one (A4b's Drive-only store
over the fake Drive); only its default folder, the package's `QUOTES_FOLDER`, is moved to the checkout's own, because
the run writes there and `Git`'s guard expects it there."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path

from fno.composition import open_account_writer
from fno.config import ROOT, load_app_config
from fno.constants import BOOKS, PLAYBOOK_FOLDER
from fno.daily.runner import DayRunner
from fno.desk.private_files import PrivateFiles
from fno.models import IST
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.storage.index_store import DriveIndexStore
from fno.storage.raw_store import LocalFolderStore
from fno.storage.wiring import QUOTES_FOLDER
from tests.checks.builders import CALENDAR, nse_files
from tests.timetable.drive_day import fresh_container

from .children import Background, Children, Foreground, groww_snapshot, nse_snapshot
from .outside import (
    DAY,
    START,
    FakeClock,
    FakeOwnerDrive,
    FakeSlack,
    FixtureProvider,
    NoNseArchive,
)

QUOTES = QUOTES_FOLDER.relative_to(ROOT)
CALENDAR_NAME = "research/data/calendar/nse_sessions.csv"
COPIED = ("fno", PLAYBOOK_FOLDER, "journal/versions.csv", ".gitignore", "config.yaml")  # the code too: D3 hashes it
# Every name the suite replaces, and nothing else (criterion 6): a test checks the set
OUTSIDE_SEAMS = (
    "fno.models.datetime",  # the clock
    "fno.composition.build_alert_sender",  # Slack
    "fno.storage.wiring.build_owner_drive",  # the owner's Drive (private records)
    "fno.storage.quote_wiring.build_owner_drive",  # the owner's Drive (Groww's raw quote files)
    "fno.storage.wiring.build_raw_stores",  # the shared Drive's raw NSE files (C3)
    "fno.storage.wiring.build_nse_fo_library",  # NSE's archive
    "fno.desk.wiring.build_nse_fo_library",
    "fno.composition.build_nse_fo_library",
    "fno.composition.build_quote_recorder",  # Groww's 15:15 capture
    "fno.daily.processes.ChildProcesses",  # the child commands
    "fno.storage.wiring.build_quote_store",  # the real quote store, its folder this checkout's (module note)
    "fno.desk.wiring.build_quote_store",
    "fno.composition.build_quote_store",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def checkout(tmp_path: Path) -> Path:
    """A fresh clone with its own bare `origin`, holding what the run reads from its checkout."""
    origin, root = tmp_path / "origin.git", tmp_path / "checkout"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(root))
    for key, value in (("user.email", "e2e@example.com"), ("user.name", "e2e"), ("commit.gpgsign", "false")):
        git(root, "config", key, value)
    for name in COPIED:
        source, target = ROOT / name, root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy(source, target)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture checkout")
    git(root, "push", "-q", "-u", "origin", "HEAD:main")
    return root


@dataclass
class Day:
    root: Path
    clock: FakeClock
    drive: FakeOwnerDrive
    slack: FakeSlack
    provider: FixtureProvider
    children: Children
    day: date = DAY
    printed: list[str] = field(default_factory=list)

    def quote_store(self):
        from fno.storage.wiring import build_quote_store  # the patched binding: this checkout's folder

        return build_quote_store()

    def recorder(self) -> QuoteSnapshotRecorder:
        """A4's real NIFTY recorder over the fake Groww, on the run's clock, into this checkout's quote store."""
        self.provider.clock = self.clock
        return QuoteSnapshotRecorder(self.provider, self.quote_store(), self.clock, self.clock.advance,
                                     calendar=CALENDAR)  # fmt: skip

    def runner(self) -> DayRunner:
        from fno.daily.wiring import build_day_runner

        return build_day_runner(load_app_config(), self.root, sleep=self.clock.advance)

    def run(self) -> tuple[int, str]:
        return self.runner().run(self.day)

    def log(self, day: date | None = None) -> dict:
        """The committed run log of `day` (this day by default); {} when there is none."""
        path = self.root / "journal/runs" / f"{day or self.day}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

    def committed(self, message: str) -> bool:
        """True once this checkout made a commit with exactly `message` (read from git's own reflog, cheaply)."""
        reflog = self.root / ".git/logs/HEAD"
        return reflog.is_file() and f"commit: {message}\n" in reflog.read_text(encoding="utf-8")

    def origin_subjects(self) -> list[str]:
        """Every commit message `origin` holds: what the run published."""
        return git(self.root.parent / "origin.git", "log", "--format=%s", "main").splitlines()

    def step(self, name: str) -> dict:
        return self.log()["steps"][name]["result"]

    def move_to(self, day: date) -> None:
        """The next routine: a new container (no private record left locally), 14:33 on `day`, fresh child commands."""
        fresh_container(self.root)
        self.day = day
        self.clock.set(datetime.combine(day, START.timetz()))
        self.children = children(self)


def children(day_: Day) -> Children:
    return Children(day_.clock, quote_parts_script(day_), day_.root / QUOTES)


def in_checkout(root: Path):
    """`build_quote_store` with this checkout's quote folder as its default (the real store, the fake Drive)."""
    from fno.storage.wiring import build_quote_store

    return lambda folder=None: build_quote_store(folder or root / QUOTES)


def start_accounts_in_drive(root: Path, drive: FakeOwnerDrive, day: date) -> None:
    """E2c's state: every book's account started and kept in Drive, none in the new container."""
    for book in BOOKS:
        with open_account_writer(book, root) as writer:
            writer.start(day - timedelta(days=7))
    PrivateFiles(lambda: DriveIndexStore(drive, "paper"), root).move_accounts()
    fresh_container(root)


def book1_decides(day_: Day) -> Foreground:
    """`desk book1 --day D` as the child runs it, at this checkout (`cmd_book1` reads the package's ROOT)."""

    def work():
        from fno.books.book1_wiring import build_book1
        from fno.desk.wiring import download_private_records

        files = download_private_records(day_.day, day_.root)
        return 0, [str(build_book1(load_app_config(), day_.root, files=files).decide(day_.day))]

    return Foreground(0, work)


def printed(action) -> list[str]:
    """What a command printed while `action` ran (a child's stdout)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = action()
    return code, [line for line in out.getvalue().splitlines() if line.strip()]


def quote_parts_script(day_: Day) -> dict:
    """The 3 pm parts: NIFTY by A4's real `record_today` over the fake Groww, NSE's chain at 14:57, the three indices
    by 15:13 (their window), each in its own time."""
    from fno.daily.alerts import ReportedAlerts
    from fno.quotes.cli import record_today
    from fno.storage.wiring import build_quote_store

    def nifty(clock, staging):
        day_.provider.clock = clock
        build = lambda: QuoteSnapshotRecorder(day_.provider, build_quote_store(staging), clock, clock.advance,  # noqa: E731
                                              calendar=CALENDAR)  # fmt: skip
        alerts = ReportedAlerts(day_.slack)  # as `cmd_quotes` wires it: an unsent alert prints with its text
        return printed(lambda: record_today(build, alerts, False, CALENDAR_NAME))

    def nse(clock, staging):
        clock.set(max(clock(), datetime.combine(day_.day, time(14, 57), IST)))
        nse_snapshot(LocalFolderStore(staging), day_.day, clock())
        return 0, ["recorded: nse (complete=True)"]

    def indices(clock, staging):
        clock.set(max(clock(), datetime.combine(day_.day, time(15, 13), IST)))
        for name in ("banknifty", "finnifty", "midcpnifty"):
            groww_snapshot(build_quote_store(staging), day_.day, name, clock())
        return 0, ["recorded: 3 indices"]

    return {
        ("quotes", "record"): Background(nifty),
        ("quotes", "record", "--source", "nse"): Background(nse),
        ("quotes", "record-indices"): Background(indices),
        ("desk", "book1"): book1_decides(day_),
        ("intraday", "backfill"): Foreground(0, lambda: (0, ["nothing to catch up"])),  # A16b: no Groww candles here
    }


def fixture_day(tmp_path: Path, monkeypatch) -> Day:
    """The day built and its outside seams patched; nothing has run yet."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))  # never the owner's ~/.trading.env
    for name in [n for n in os.environ if n.startswith(("FNO_", "GROWW_"))]:
        monkeypatch.delenv(name)
    for name in ("GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE"):
        monkeypatch.setenv(name, "")  # restored after the test; the clock sets them as it moves
    root, clock, drive, slack = checkout(tmp_path), FakeClock(os.environ), FakeOwnerDrive(), FakeSlack()
    day_ = Day(root, clock, drive, slack, FixtureProvider(clock), None)
    quote_store = in_checkout(root)
    sessions = CALENDAR.sessions(date(2026, 9, 1), date(2026, 10, 31))
    seams = {
        "fno.models.datetime": clock.datetime_class(),
        "fno.composition.build_alert_sender": lambda: slack,
        "fno.storage.wiring.build_owner_drive": lambda *a, **k: drive,
        "fno.storage.quote_wiring.build_owner_drive": lambda *a, **k: drive,
        "fno.storage.wiring.build_raw_stores": lambda *a, **k: [nse_files(*sessions)],
        "fno.storage.wiring.build_nse_fo_library": lambda *a, **k: NoNseArchive(),
        "fno.desk.wiring.build_nse_fo_library": lambda *a, **k: NoNseArchive(),
        "fno.composition.build_nse_fo_library": lambda *a, **k: NoNseArchive(),
        "fno.composition.build_quote_recorder": lambda cfg: day_.recorder(),
        "fno.daily.processes.ChildProcesses": lambda root: day_.children,
        "fno.storage.wiring.build_quote_store": quote_store,
        "fno.desk.wiring.build_quote_store": quote_store,
        "fno.composition.build_quote_store": quote_store,
    }
    assert tuple(seams) == OUTSIDE_SEAMS
    for target, value in seams.items():
        monkeypatch.setattr(target, value)
    day_.children = children(day_)
    start_accounts_in_drive(root, drive, DAY)
    return day_
