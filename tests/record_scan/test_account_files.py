"""Story E2d criterion 6: the public-record scan refuses every file under a book's or a shadow account's `account/`
folder by its path, even when added past `.gitignore` with `git add -f`; the public daily totals still commit."""

import pytest

from fno.record_scan.forbidden_files import PAPER_ACCOUNT_FILES
from tests.record_scan.test_forbidden_files import _stage
from tests.record_scan.test_routine_gate import git, repo  # noqa: F401 - the routine checkout fixture

KIND = "private paper account file"


@pytest.mark.parametrize("path", ["journal/book1_rules/account/trade_marks.csv",
                                  "journal/shadow/fly-a-v1/account/equity_history.csv"])  # fmt: skip
def test_a_force_added_account_file_is_refused(repo, path):  # noqa: F811
    _stage(repo, path, "date,trade_id\n2026-10-14,t1\n")
    commit = git(repo, "commit", "-q", "-m", "desk records")
    assert commit.returncode != 0 and f"{path}:0: {KIND}" in commit.stderr
    assert git(repo, "rev-parse", "HEAD").returncode != 0


def test_the_public_daily_totals_commit(repo):  # noqa: F811
    _stage(repo, "journal/book1_rules/daily_totals.csv", "date,closed_equity_rs\n2026-10-14,2000000.00\n")
    _stage(repo, "journal/shadow/fly-a-v1/daily_totals.csv", "date,closed_equity_rs\n2026-10-14,2000000.00\n")
    assert git(repo, "commit", "-q", "-m", "daily totals").returncode == 0


def test_the_folder_rule_boundaries():
    for path in ("journal/book2_hybrid/account/cash_ledger.csv", "journal/shadow/x-v2/account/fills.csv"):
        assert PAPER_ACCOUNT_FILES.matches(path), path
    for path in ("journal/book1_rules/daily_totals.csv", "x/journal/book1_rules/account/a.csv",
                 "journal/a/b/account/a.csv", "journal/book1_rules/accounts/a.csv"):  # fmt: skip
        assert not PAPER_ACCOUNT_FILES.matches(path), path
