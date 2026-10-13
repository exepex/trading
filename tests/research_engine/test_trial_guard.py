"""Story B3 criteria 1 and 6 on a temporary git repository: an unregistered trial stops with "not registered" before
any data is read; the decisive period needs a "frozen at commit" line whose commit exists, precedes the run and holds
the same rules."""

import subprocess
from datetime import date

import pytest

from fno.research_engine.ledger import Ledger, NotRegistered, write_ledger
from fno.research_engine.trial_guard import LedgerTrialGuard, ProtocolNotFrozen, frozen_commit

PROTOCOL = "research/exp/PROTOCOL.md"
RULES = "# Protocol\nP1: SC every opportunity\n"


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def commit(root, message):
    git(root, "add", ".")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.invalid")
    git(tmp_path, "config", "user.name", "test")
    (tmp_path / "research/exp").mkdir(parents=True)
    (tmp_path / PROTOCOL).write_text(RULES)
    rules_commit = commit(tmp_path, "rules")
    Ledger(tmp_path).register("P1", "exp", "SC every opportunity", "prospective", True, PROTOCOL, date(2026, 10, 13))
    commit(tmp_path, "register P1")
    return tmp_path, rules_commit


def freeze(root, protocol_text, ledger_commit_of_protocol=None):
    (root / PROTOCOL).write_text(protocol_text)
    frozen = commit(root, "freeze protocol")
    ledger = Ledger(root)
    rows = ledger.rows()
    rows[0]["protocol_commit"] = ledger_commit_of_protocol or frozen
    ledger.file.write_text(write_ledger(rows))
    commit(root, "ledger: protocol commit")


def guard(root):
    return LedgerTrialGuard(Ledger(root))


def test_an_unregistered_trial_stops_with_not_registered(repo):
    root, _ = repo
    with pytest.raises(NotRegistered, match="not registered"):
        guard(root).check(["P9"], PROTOCOL, decisive=False)


def test_a_committed_registration_is_enough_for_the_reported_period_but_not_the_decisive_one(repo):
    root, _ = repo
    guard(root).check(["P1"], PROTOCOL, decisive=False)
    with pytest.raises(NotRegistered, match="no frozen protocol commit"):
        guard(root).check(["P1"], PROTOCOL, decisive=True)


def test_the_decisive_period_needs_the_frozen_at_commit_line(repo):
    root, rules_commit = repo
    freeze(root, RULES + "\nNo freeze line here.\n")
    with pytest.raises(ProtocolNotFrozen, match="no 'frozen at commit"):
        guard(root).check(["P1"], PROTOCOL, decisive=True)


def test_a_frozen_line_naming_an_unknown_commit_is_refused(repo):
    root, _ = repo
    freeze(root, RULES + "frozen at commit 0123456789abcdef0123456789abcdef01234567\n")
    with pytest.raises(ProtocolNotFrozen, match="does not exist or does not precede"):
        guard(root).check(["P1"], PROTOCOL, decisive=True)


def test_rules_changed_after_the_named_commit_are_refused(repo):
    root, rules_commit = repo
    freeze(root, RULES.replace("SC", "SF") + f"Frozen at commit {rules_commit}\n")
    with pytest.raises(ProtocolNotFrozen, match="changed after its frozen commit"):
        guard(root).check(["P1"], PROTOCOL, decisive=True)


def test_a_valid_freeze_lets_the_decisive_period_run(repo):
    root, rules_commit = repo
    freeze(root, RULES + f"Frozen at commit `{rules_commit}` (12 Oct 2026)\n")
    guard(root).check(["P1"], PROTOCOL, decisive=True)
    assert frozen_commit((root / PROTOCOL).read_text()) == rules_commit
