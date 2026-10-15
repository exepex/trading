"""Story A16 criterion 1 ("Two checkouts, one ledger", judge 108 addendum 1 should-fix B): two overlapping recorder
runs in two git clones of one bare repository, sharing one Drive, race for the same marks. GitHub ends with exactly one
row per mark (the first pushed), no conflict markers, and both runs' pushes succeed."""

import subprocess
from datetime import time

from fno.intraday.clock import ClockCheck
from fno.intraday.first_version_store import FirstVersionStore
from fno.intraday.heartbeat import Heartbeat
from fno.intraday.ledger import SlotLedger
from fno.intraday.realised_vol import QuoteSnapshotRv15m
from fno.intraday.recorder import IntradayRecorder
from fno.intraday.rv_table import RvTable
from fno.intraday.session_rv import SessionRv
from fno.intraday.sync import GitLedgerSync
from fno.storage.manifest_commit import GitManifestRecorder
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


def recorder(checkout, drive, clock, latency=1.0):
    ledger_folder = checkout / FOLDER
    store = FirstVersionStore(AreaStore(drive, "raw"), AreaStore(drive, "revisions"), ledger_folder / "revisions",
                              clock.now)  # fmt: skip
    source = FakeSource(clock, latency=latency)  # two real runs never get byte-identical answers
    committer = GitManifestRecorder(checkout, ledger_folder, message="Data: intraday slots ({what})",
                                    label="intraday files", keep_remote_on_conflict=True)  # fmt: skip
    rv = SessionRv(store, source.name, calendar(), RvTable(ledger_folder), QuoteSnapshotRv15m(), clock.now)
    clocks = ClockCheck([FixedServer("github", 0.2)])
    return IntradayRecorder(source, store, SlotLedger(ledger_folder), Heartbeat(ledger_folder), calendar(),
                            FakeAlerts(), clocks, rv, GitLedgerSync(committer), clock.now, clock.sleep)  # fmt: skip


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

    outcome_first = first.snapshot()  # settles 09:15 and 09:30 as missed, takes 09:45 first, pushes
    second.sync.pull = lambda: "pull happened just before the first run's push"  # the race the overlap allows
    second._stored = lambda day, mark: False  # and it looked at Drive just before the first run's copy landed
    outcome_second = second.snapshot()  # writes the same missed rows; its 09:45 copy is second

    assert outcome_first.status == "good" and outcome_second.status == "already recorded"
    assert all(o.lines[-1].startswith("intraday files committed and pushed") for o in (outcome_first, outcome_second))
    assert "kept as a revision" in outcome_second.detail
    git(seed, "pull", "-q", "origin", "main")
    rows = sorted((seed / FOLDER / "slots").rglob("*.csv"))
    assert [p.name for p in rows] == ["nifty_20261015_0915.csv", "nifty_20261015_0930.csv", "nifty_20261015_0945.csv"]
    for path in rows:
        text = path.read_text()
        assert text.count("\n") == 2 and "<<<<<<<" not in text and ">>>>>>>" not in text  # header and one row
        assert ",run-a," not in text  # rows carry no checkout name; the first push's copy is kept
    kept = (seed / FOLDER / "slots" / "2026" / "10" / "15" / "nifty_20261015_0915.csv").read_text()
    assert kept == (first_checkout / FOLDER / "slots" / "2026" / "10" / "15" / "nifty_20261015_0915.csv").read_text()
    assert len(list((seed / FOLDER / "revisions").glob("*.csv"))) == 1  # the second copy of 09:45, indexed once
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
