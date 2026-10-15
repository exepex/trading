"""Story D3b criteria 4 and 4b for S1's first counted decision: the shared run order (commit time, then the
run counter as a number), never the folder name; an uncommitted run is never first counted; on runs r1 to r9 the
result is the same as S1's old name order (main holds no committed decision run yet, so this fixture stands in)."""

import subprocess
from datetime import date

from fno.evaluation.order import CountedDecision, first_counted_decision
from fno.playbook.decision_store import SUMS_FILE
from fno.playbook.history import PlaybookGit
from tests.evaluation.builders import protocol_repo
from tests.playbook.builders import commit_all

BOOK = "book1_rules"


def run(root, day: str, n: int):
    folder = root / "journal" / BOOK / "decisions" / day / f"{day}-r{n}"
    folder.mkdir(parents=True)
    (folder / SUMS_FILE).write_text("x  no_trade.json\n")
    return folder


def old_name_order(root, git, start=None):
    """S1's rule before D3b: days and runs by folder name, the first committed one."""
    folder = root / "journal" / BOOK / "decisions"
    for day in sorted(p for p in folder.iterdir() if p.is_dir()):
        if start is not None and date.fromisoformat(day.name) < start:
            continue
        for found in sorted(p for p in day.iterdir() if p.is_dir() and not p.name.startswith(".")):
            added = git.added_in((found / SUMS_FILE).relative_to(root).as_posix())
            if added:
                return CountedDecision(BOOK, found.relative_to(root).as_posix(), added[0])
    return None


def test_runs_r1_to_r9_give_the_same_first_counted_decision_as_the_old_name_order(tmp_path):
    protocol_repo(tmp_path)
    for day in ("2026-11-02", "2026-11-03", "2026-11-04"):
        for n in range(1, 10):
            run(tmp_path, day, n)
            commit_all(tmp_path, f"{day} r{n}")
    git = PlaybookGit(tmp_path)
    for start in (None, date(2026, 11, 3), date(2026, 11, 4), date(2026, 11, 5)):
        assert first_counted_decision(tmp_path, git, BOOK, start) == old_name_order(tmp_path, git, start)


def test_r2_before_r10_by_commit_order_not_by_name(tmp_path):
    """Ten runs on the day: r1 stays on disk only, r2 lands first, r3 to r10 after it."""
    protocol_repo(tmp_path)
    run(tmp_path, "2026-11-02", 2)
    first = commit_all(tmp_path, "r2")
    for n in range(3, 11):
        run(tmp_path, "2026-11-02", n)
    commit_all(tmp_path, "r3 to r10")
    run(tmp_path, "2026-11-02", 1)  # on disk only: never counted
    git = PlaybookGit(tmp_path)
    found = first_counted_decision(tmp_path, git, BOOK, None)
    assert found.run.endswith("2026-11-02-r2") and found.commit == first
    assert old_name_order(tmp_path, git).run.endswith("2026-11-02-r10")  # what the name order got wrong


def test_an_uncommitted_run_is_never_first_counted(tmp_path):
    protocol_repo(tmp_path)
    run(tmp_path, "2026-11-02", 1)  # on disk only
    run(tmp_path, "2026-11-03", 1)
    subprocess.run(["git", "-C", str(tmp_path), "add", "journal/book1_rules/decisions/2026-11-03"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "11-03"], check=True)
    found = first_counted_decision(tmp_path, PlaybookGit(tmp_path), BOOK, None)
    assert found.run.endswith("2026-11-03/2026-11-03-r1")
