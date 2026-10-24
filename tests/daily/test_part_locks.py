"""Story O1, gap F1: a 3 pm part's lock is held by the real child for its whole life, through `ChildProcesses`'s
`pass_fds`, and freed by the kernel when the child ends or is killed; the run's own copy is closed at once."""

import time
from datetime import date, datetime

from fno.daily.part_locks import PART_LOCKS, PartLocks
from fno.daily.processes import ChildProcesses
from fno.models import IST

DAY = date(2026, 10, 14)
STARTED = datetime(2026, 10, 14, 14, 38, tzinfo=IST)
WAITS_FOR_STOP = (
    "import pathlib, sys, time\nwhile not pathlib.Path(sys.argv[-1] + '.stop').exists():\n    time.sleep(0.02)\n"
)


def child_root(tmp_path):
    """A checkout whose `python -m fno ... <last>` is a recorder stand-in that runs until `<last>.stop` appears."""
    (tmp_path / "fno").mkdir()
    (tmp_path / "fno" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "fno" / "__main__.py").write_text(WAITS_FOR_STOP, encoding="utf-8")
    return tmp_path


def ended(process, seconds=10.0):
    deadline = time.monotonic() + seconds
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.02)
    return process.poll() is not None


def started_child(tmp_path):
    root, locks = child_root(tmp_path), PartLocks(tmp_path / PART_LOCKS)
    with locks.taken(DAY, "nifty", STARTED) as lock:
        process = ChildProcesses(root, report=lambda line: None).start(("quotes", "record"), hold=lock)
    return root, locks, process


def test_the_child_holds_the_lock_for_its_life_and_the_kernel_frees_it_when_it_ends(tmp_path):
    root, locks, process = started_child(tmp_path)
    assert locks.held(DAY, "nifty") and locks.started(DAY, "nifty") == STARTED.isoformat()  # the run's copy is closed
    (root / "record.stop").touch()
    assert ended(process) and not locks.held(DAY, "nifty")


def test_a_killed_child_frees_its_lock(tmp_path):
    _, locks, process = started_child(tmp_path)
    process.stop()
    assert not locks.held(DAY, "nifty")


def test_a_held_lock_is_never_taken_twice_and_no_other_child_inherits_it(tmp_path):
    root, locks, process = started_child(tmp_path)
    with locks.taken(DAY, "nifty", STARTED) as again:
        assert again is None
    other = ChildProcesses(root, report=lambda line: None).start(("quotes", "record", "--source", "nse"))
    (root / "record.stop").touch()
    assert ended(process) and other.poll() is None and not locks.held(DAY, "nifty")  # the other child never had it
    (root / "nse.stop").touch()
    assert ended(other)
