"""Story S1, criteria 1 and 3: the freeze record's commit precedes every book's first counted decision (runs before
the common start are pilot and do not count). A decision is counted under the latest version frozen before it."""

from datetime import date
from pathlib import Path

from fno.evaluation.freeze import ProtocolFreezer
from fno.evaluation.order import first_counted_decision, frozen_versions, order_problems, version_of
from fno.evaluation.protocol import PROTOCOL_FILE
from fno.playbook.history import PlaybookGit
from tests.evaluation.builders import protocol_repo
from tests.playbook.builders import commit_all


def decide(root: Path, book: str, day: str, run: str = "r1") -> str:
    """A committed D3 run of `book` on `day` (its records.sha256 is what dates it)."""
    folder = root / "journal" / book / "decisions" / day / f"{day}-{run}"
    folder.mkdir(parents=True)
    (folder / "records.sha256").write_text("x  no_trade.json\n")
    return commit_all(root, f"{book} {day}")


def freeze(root: Path) -> str:
    record = ProtocolFreezer(root, PlaybookGit(root)).freeze(date(2026, 10, 21))
    return commit_all(root, f"freeze v{record.version}")


def new_version(root: Path) -> None:
    """A change after the freeze: the protocol as version 2, committed."""
    protocol = root / PROTOCOL_FILE
    protocol.write_text(protocol.read_text().replace("Protocol version: 1", "Protocol version: 2"))
    commit_all(root, "protocol v2")


def firsts(root, start=None):
    found = (first_counted_decision(root, PlaybookGit(root), book, start) for book in ("book1_rules", "book3_ai"))
    return [f for f in found if f is not None]


def test_decisions_after_the_freeze_are_in_order(tmp_path):
    protocol_repo(tmp_path)
    freeze(tmp_path)
    decide(tmp_path, "book1_rules", "2026-11-02")
    decide(tmp_path, "book3_ai", "2026-11-02")
    assert order_problems(PlaybookGit(tmp_path), 1, firsts(tmp_path)) == []


def test_a_counted_decision_before_the_freeze_is_out_of_order(tmp_path):
    protocol_repo(tmp_path)
    early = decide(tmp_path, "book1_rules", "2026-10-20")
    freeze(tmp_path)
    problems = order_problems(PlaybookGit(tmp_path), 1, firsts(tmp_path))
    assert problems == [
        f"book1_rules: first counted decision journal/book1_rules/decisions/2026-10-20/2026-10-20-r1 ({early[:10]}) "
        "is not after the v1 freeze"
    ]


def test_pilot_decisions_before_the_common_start_do_not_count(tmp_path):
    protocol_repo(tmp_path)
    decide(tmp_path, "book3_ai", "2026-10-20")  # Book 3 pilot, before the freeze
    freeze(tmp_path)
    decide(tmp_path, "book3_ai", "2026-11-02")
    assert order_problems(PlaybookGit(tmp_path), 1, firsts(tmp_path, date(2026, 11, 2))) == []
    assert order_problems(PlaybookGit(tmp_path), 1, firsts(tmp_path)) != []  # counted from the start: out of order


def test_counted_decisions_without_a_committed_freeze_are_refused(tmp_path):
    protocol_repo(tmp_path)
    decide(tmp_path, "book1_rules", "2026-11-02")
    assert order_problems(PlaybookGit(tmp_path), 1, firsts(tmp_path)) == [
        "research/evaluation/FREEZE_v1.md is not committed, but counted decisions exist"
    ]
    assert order_problems(PlaybookGit(tmp_path), 1, []) == []  # nothing counted yet: nothing to check


def test_an_uncommitted_run_is_not_a_counted_decision(tmp_path):
    protocol_repo(tmp_path)
    folder = tmp_path / "journal/book1_rules/decisions/2026-11-02/2026-11-02-r1"
    folder.mkdir(parents=True)
    (folder / "records.sha256").write_text("x\n")
    assert firsts(tmp_path) == []


def test_each_decision_is_counted_under_the_latest_version_frozen_before_it(tmp_path):
    protocol_repo(tmp_path)
    before = decide(tmp_path, "book1_rules", "2026-10-20")
    freeze(tmp_path)
    under_v1 = decide(tmp_path, "book1_rules", "2026-11-02")
    new_version(tmp_path)
    freeze(tmp_path)
    under_v2 = decide(tmp_path, "book1_rules", "2026-11-03")
    history = PlaybookGit(tmp_path)
    assert frozen_versions(tmp_path) == [1, 2]
    assert [version_of(tmp_path, history, c) for c in (before, under_v1, under_v2)] == [None, 1, 2]


def test_a_decision_committed_with_the_freeze_is_not_after_it(tmp_path):
    protocol_repo(tmp_path)
    ProtocolFreezer(tmp_path, PlaybookGit(tmp_path)).freeze(date(2026, 10, 21))
    same = decide(tmp_path, "book1_rules", "2026-11-02")  # one commit holds the freeze record and the decision
    assert order_problems(PlaybookGit(tmp_path), 1, firsts(tmp_path)) == [
        f"book1_rules: first counted decision journal/book1_rules/decisions/2026-11-02/2026-11-02-r1 ({same[:10]}) "
        "is not after the v1 freeze"
    ]
