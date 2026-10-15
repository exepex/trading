"""Story E6 (experiment 2, owner option a): a shadow version's forward test has its own account under
`journal/shadow/<name>-v<n>/account/`, never a book's, behind the same firewall and lock."""

from datetime import date

import pytest

from fno.books.account import PaperAccount
from fno.books.paths import BookPathError, account_folder, shadow_account
from fno.composition import open_account_writer
from fno.constants import BOOK1_RULES


def test_a_shadow_account_lives_in_its_own_folder_with_the_paper_account_of_rs_20_lakh(tmp_path):
    name = shadow_account("cand-c-v1")
    assert name == "shadow:cand-c-v1"
    assert account_folder(tmp_path, name) == tmp_path / "journal" / "shadow" / "cand-c-v1" / "account"
    with open_account_writer(name, tmp_path) as writer:
        assert writer.start(date(2026, 10, 14))
    assert PaperAccount(tmp_path, name).summary()["cash_rs"] == 2_000_000.0
    assert not PaperAccount(tmp_path, BOOK1_RULES).started  # nothing written to a book


@pytest.mark.parametrize("bad", ["shadow:", "shadow:Cand-v1", "shadow:cand", "shadow:../book1_rules-v1", "cand-c-v1"])
def test_anything_else_is_refused(tmp_path, bad):
    with pytest.raises(BookPathError):
        account_folder(tmp_path, bad)
