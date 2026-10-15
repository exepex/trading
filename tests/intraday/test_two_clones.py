"""Story A16 criterion 1 ("Two checkouts, one ledger", judge 108 addendum 1 should-fix B): two overlapping recorder
runs in two git clones of one bare repository, sharing one Drive, race for the same marks. GitHub ends with exactly one
row per mark (the first pushed), no conflict markers, and both runs' pushes succeed."""

import subprocess
from datetime import time

from fno.intraday.clock import ClockCheck
from fno.intraday.heartbeat import Heartbeat
from fno.intraday.ledger import SlotLedger
from fno.intraday.realised_vol import QuoteSnapshotRv15m
from fno.intraday.recorder import IntradayRecorder
from fno.intraday.rv_table import RvTable
from fno.intraday.session_rv import SessionRv
from fno.intraday.snapshot_files import SnapshotFiles
from fno.intraday.sync import GitLedgerSync
from fno.intraday.wiring import OWNED_PATHS
from fno.storage.owned_paths_commit import OwnedPathsCommitter
from fno.storage.raw_store import AreaStore, LocalFolderStore
from tests.intraday.fakes import DAY, FakeAlerts, FakeClock, FakeSource, FixedServer, calendar, ist

FOLDER = "research/data/intraday"


def git(folder, *args) -> str:
    return subprocess.run(["git", *args], cwd=folder, check=True, capture_output=True, text=True).stdout


def clone(tmp_path, origin, name):
    folder = tmp_path / name
    git(tmp_path, "clone", "-q", str(origin), str(folder))
    for key, value in (("user.name", name), ("user.email", f"{name}@example.invalid"), ("core.hooksPath", "hooks")):
        git(folder, "config", key, value)
    return folder


def recorder(checkout, drive, clock, latency=1.0, alerts=None):
    ledger_folder = checkout / FOLDER
    source = FakeSource(clock, latency=latency)  # two real runs never get byte-identical answers
    ledger = SlotLedger(ledger_folder)
    files = SnapshotFiles(source.name, AreaStore(drive, "raw"), ledger)
    committer = OwnedPathsCommitter(checkout, ledger_folder, OWNED_PATHS, message="Data: intraday slots ({what})",
                                    label="intraday files", keep_remote_on_conflict=True)  # fmt: skip
    alerts = FakeAlerts() if alerts is None else alerts
    rv = SessionRv(files, calendar(), RvTable(ledger_folder), QuoteSnapshotRv15m(), clock.now)
    clocks = ClockCheck([FixedServer("github", 0.2, clock.now)], clock.now)
    return IntradayRecorder(source, files, ledger, Heartbeat(ledger_folder), calendar(),
                            alerts, clocks, rv, GitLedgerSync(committer, alerts), clock.now, clock.sleep)  # fmt: skip


def test_two_overlapping_runs_in_two_clones_leave_one_row_per_mark_and_both_push(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    seed = clone(tmp_path, origin, "seed")
    (seed / "README.md").write_text("x\n")
    git(seed, "add", "README.md")
    git(seed, "commit", "-q", "-m", "start")
    git(seed, "push", "-q", "origin", "HEAD:main")
    drive = LocalFolderStore(tmp_path / "drive")
    first_checkout, second_checkout = clone(tmp_path, origin, "run-a"), clone(tmp_path, origin, "run-b")
    first = recorder(first_checkout, drive, FakeClock(ist(DAY, 9, 44)))
    second = recorder(second_checkout, drive, FakeClock(ist(DAY, 9, 44, 30)), latency=2.0)

    outcome_first = first.snapshot()  # settles 09:15 and 09:30 as missed, takes 09:45, pushes first
    second.sync.pull = lambda: "pull happened just before the first run's push"  # the race the overlap allows
    outcome_second = second.snapshot()  # writes the same missed rows and its own 09:45 copy and row

    assert outcome_first.status == outcome_second.status == "good"
    assert all(o.lines[-1].startswith("intraday files committed and pushed") for o in (outcome_first, outcome_second))
    git(seed, "pull", "-q", "origin", "main")
    day_folder = seed / FOLDER / "slots" / "2026" / "10" / "15"
    rows = sorted(day_folder.glob("*.csv"))
    assert [p.name for p in rows] == ["nifty_20261015_0915.csv", "nifty_20261015_0930.csv", "nifty_20261015_0945.csv"]
    for path in rows:
        text = path.read_text()
        assert text.count("\n") == 2 and "<<<<<<<" not in text and ">>>>>>>" not in text  # header and one row
        first_copy = (first_checkout / FOLDER / "slots" / "2026" / "10" / "15" / path.name).read_text()
        assert text == first_copy  # the row first pushed to GitHub is the one kept (the stated rule)
    copies = sorted(p.name for p in (tmp_path / "drive" / "raw").rglob("nifty_20261015_0945_*.json.gz"))
    assert len(copies) == 2  # both runs' copies are in Drive under their own names; neither was written over
    kept = rows[-1].read_text()
    assert sum(name in kept for name in copies) == 1  # the 09:45 row names exactly one of them
    assert "<<<<<<<" not in (seed / FOLDER / "heartbeat.json").read_text()
    assert git(second_checkout, "status", "--porcelain") == ""  # nothing left half-merged


def test_after_a_normal_pull_the_second_run_writes_no_duplicate(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    seed = clone(tmp_path, origin, "seed")
    (seed / "README.md").write_text("x\n")
    git(seed, "add", "README.md")
    git(seed, "commit", "-q", "-m", "start")
    git(seed, "push", "-q", "origin", "HEAD:main")
    drive = LocalFolderStore(tmp_path / "drive")
    first = recorder(clone(tmp_path, origin, "run-a"), drive, FakeClock(ist(DAY, 9, 14)))
    second = recorder(clone(tmp_path, origin, "run-b"), drive, FakeClock(ist(DAY, 9, 29)))
    first.run(time(9, 20))
    second.run(time(9, 35))
    git(seed, "pull", "-q", "origin", "main")
    names = sorted(p.name for p in (seed / FOLDER / "slots").rglob("*.csv"))
    assert names == ["nifty_20261015_0915.csv", "nifty_20261015_0930.csv"]
