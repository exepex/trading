"""Story S2 with S1's `common_start` rule, read from the records: the first session on which every book has an on-time
committed run under a version registered before it. A run committed after the execution snapshot started is late; a
run whose served components differ from its registered version is unscored, and D6 pauses that book until a new
version is registered. Until the day comes, every figure is pilot evidence and no head-to-head section exists."""

from datetime import date

from fno.constants import BOOK1_RULES, BOOK3_AI, BOOKS
from fno.scoreboard.book_board import COMMON_START_NOT_REACHED
from fno.scoreboard.committed_runs import CommittedRuns
from fno.scoreboard.entry_decisions import EntryDecisions
from fno.scoreboard.sources import SnapshotMarks

from .builders import SERVED, record, versions, write_log, write_run
from .test_whole_system import build, history

D1, D2, D3 = date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)
V1 = [(book, f"{book}-v1", date(2026, 10, 1)) for book in BOOKS]


def decide_all(root, day, committed="15:05:00", book3_served=SERVED):
    run_id = f"{day}-r1"
    for book in BOOKS:
        served = book3_served if book == BOOK3_AI else SERVED
        write_run(root, book, day, run_id, record(book, day, run_id, "x", served=served))
    write_log(root, day, dict.fromkeys(BOOKS, run_id), committed=committed)


def common_start(root, rows=V1):
    found = CommittedRuns(root)
    return EntryDecisions(found.runs(), found.records, versions(*rows)).common_start(BOOKS)


def test_a_late_run_does_not_start_the_comparison(tmp_path):
    decide_all(tmp_path, D1, committed="15:16:00")  # after the execution snapshot started at 15:15
    decide_all(tmp_path, D2)
    assert common_start(tmp_path) == D2


def test_an_unscored_run_pauses_its_book_until_a_new_version_is_registered(tmp_path):
    decide_all(tmp_path, D1, book3_served={**SERVED, "playbook": "pb-2"})  # Book 3 is not running its version
    decide_all(tmp_path, D2)
    assert common_start(tmp_path) is None  # D6 keeps Book 3 paused: still v1
    assert common_start(tmp_path, [*V1, (BOOK3_AI, f"{BOOK3_AI}-v2", D2)]) == D2


def test_a_book_without_a_registered_version_never_starts_it(tmp_path):
    decide_all(tmp_path, D1)
    assert common_start(tmp_path, V1[:2]) is None


def test_without_the_common_start_every_figure_is_pilot(tmp_path):
    board = build(history(tmp_path, common=False))
    one = board["books"][BOOK1_RULES]
    assert board["common_start"] is None and one["head_to_head"] is None and one["overridden"] is None
    assert one["pilot"]["label"] == COMMON_START_NOT_REACHED
    assert one["pilot"]["trades"]["ids"] == ["p1", "h1", "o1", "u1"]


class Snapshots:
    def __init__(self):
        self.read = []

    def snapshot(self, day, snapshot_id):
        from types import SimpleNamespace

        self.read.append((day, snapshot_id))
        quote = SimpleNamespace(valid=True, bid=9.0, ask=11.0)
        return SimpleNamespace(quotes={(date(2026, 11, 26), 25000.0, "CE"): quote})


def test_marks_come_from_the_snapshot_e3_recorded_once_per_day():
    source = Snapshots()
    marks = SnapshotMarks(source, {D1: "snap-a"})
    assert marks(D1) == {(date(2026, 11, 26), 25000.0, "CE"): 10.0} and marks(D1) == marks(D1)
    assert marks(D2) == {} and source.read == [(D1, "snap-a")]
