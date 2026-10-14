"""Judge 84, must-fix D, on a real git checkout: a same-day rerun with the same inputs is refused by D3's store as a
duplicate, so C4's failure log must not change either. C4 checks without writing; the run logs the failed reports only
after its records are written. Otherwise the uncommitted rows refuse every later account write, for every book."""

import subprocess
from datetime import time
from pathlib import Path

from fno.books.book1 import Book1
from fno.books.paths import book_folder
from fno.checks.validity import ValidityReport
from fno.checks.validity_adapter import BookTradeValidator
from fno.checks.validity_failures import ValidityFailureLog
from fno.checks.validity_proposal import CheckResult
from fno.constants import BOOK1_RULES, VALIDITY_FAILURES_FILE
from fno.desk.git_sync import Git, GitCommitter
from fno.playbook.decision_run import DecisionRun
from fno.playbook.decision_store import DecisionStore
from tests.checks.builders import CALENDAR
from tests.decisions.builders import doc, snapshot

from .builders import DAYS, FixedInputs, priced_evaluator


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def checkout(tmp_path: Path) -> Path:
    origin, clone = tmp_path / "origin.git", tmp_path / "desk"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(clone))
    git(clone, "config", "user.email", "desk@example.invalid")
    git(clone, "config", "user.name", "desk")
    git(clone, "checkout", "-q", "-b", "main")
    (clone / "README").write_text("desk\n")
    git(clone, "add", "README")
    git(clone, "commit", "-q", "-m", "start")
    git(clone, "push", "-q", "origin", "main")
    return clone


class FailingChecker:
    """C4's checker failing every trade on one check: the real validator and failure log around it."""

    def check(self, proposal, capture):
        failed = CheckResult("evidence", False, "no committed capture record", {"day": proposal.day.isoformat()})
        return ValidityReport(proposal.book, proposal.opportunity_id, "playbook", (failed,))


class NoCapture:
    def record(self, day):
        return None


def test_a_same_day_rerun_leaves_the_failure_log_unchanged_and_the_checkout_clean(tmp_path):
    root = checkout(tmp_path)
    validator = BookTradeValidator(BOOK1_RULES, FailingChecker(), NoCapture(), time(15, 12), ValidityFailureLog(root))
    run = DecisionRun(priced_evaluator(), DecisionStore(root, BOOK1_RULES), validator)
    playbook = snapshot(doc("sc-a"))
    decider = Book1(root, CALENDAR, lambda: playbook, FixedInputs(), run, GitCommitter(Git(root)))
    assert "decided" in decider.decide(DAYS[0])
    failures = book_folder(root, BOOK1_RULES) / VALIDITY_FAILURES_FILE
    logged = failures.read_bytes()
    assert logged.count(b"\n") == 2  # the header and the one failed check of the blocked trade
    assert git(root, "status", "--porcelain") == ""
    assert "already decided" in decider.decide(DAYS[0])
    assert failures.read_bytes() == logged
    assert git(root, "status", "--porcelain") == ""
