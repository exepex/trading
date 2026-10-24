"""Story MS-P1d (orchestrator, 22 Oct 2026): the market school's driver accounts under `journal/school/` are private
paper account files too: the public-record scan refuses them by path even when added past `.gitignore`, and the
desk's own patterns are unchanged."""

import pytest

from fno.record_scan.forbidden_files import PAPER_ACCOUNT_FILES
from tests.record_scan.test_forbidden_files import _stage
from tests.record_scan.test_routine_gate import git, repo  # noqa: F401 - the routine checkout fixture

KIND = "private paper account file"
SCHOOL = "journal/school/journal/shadow/school-cs1-v1/account/"


@pytest.mark.parametrize("name", ["cash_ledger.csv", "equity_history.csv", "positions.json", "school_positions.jsonl"])
def test_a_force_added_school_account_file_is_refused(repo, name):  # noqa: F811
    path = SCHOOL + name
    _stage(repo, path, "entry_id,kind\nopening,opening\n")
    commit = git(repo, "commit", "-q", "-m", "school account")
    assert commit.returncode != 0 and f"{path}:0: {KIND}" in commit.stderr
    assert git(repo, "rev-parse", "HEAD").returncode != 0


def test_the_patterns_are_the_desk_s_plus_the_school_s():
    assert PAPER_ACCOUNT_FILES.patterns == ("journal/*/account/", "journal/shadow/*/account/", "journal/school/")
    assert PAPER_ACCOUNT_FILES.matches(SCHOOL + "cash_ledger.csv")
    for path in ("journal/schools/a.csv", "x/journal/school/a.csv", "research/school/reviews/brake_lifts.csv"):
        assert not PAPER_ACCOUNT_FILES.matches(path), path
