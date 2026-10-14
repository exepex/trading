"""Judge 69: a shadow account must be separate from every real book, by name and by storage, or it is refused; a
refused shadow never changes Book 1's decision."""

from pathlib import Path

import pytest

from fno.constants import Decision
from fno.playbook.shadow import ShadowAccount
from tests.risk.builders import book

from .evaluation_builders import REAL, REPO, Counts, OwnShadowBooks, run, strategy

JOURNAL = REPO / "journal"


def account(storage: Path, name: str = "shadow-sc-new") -> ShadowAccount:
    return ShadowAccount(book(name=name), Counts(), storage)


def test_a_separate_shadow_folder_is_accepted():
    assert REAL.overlap(account(JOURNAL / "shadow" / "sc-new")) is None


@pytest.mark.parametrize(
    "storage",
    [
        JOURNAL / "book1_rules",  # a real book's own folder
        JOURNAL / "book2_hybrid" / "account",  # inside a real book's folder
        JOURNAL,  # above every real book
        JOURNAL / "shadow" / ".." / "book3_ai",  # the same folder written another way
    ],
)
def test_storage_that_overlaps_a_real_book_is_refused(storage):
    assert "overlaps the real book folder" in REAL.overlap(account(storage))


def test_a_shadow_named_like_a_real_book_is_refused():
    assert "named like the real book" in REAL.overlap(account(JOURNAL / "shadow" / "x", name="book1_rules"))


def test_the_evaluator_refuses_a_shadow_stored_in_book_1_and_book_1_is_unchanged():
    candidate = strategy("sc-new", status="research")
    misplaced = OwnShadowBooks(storage=JOURNAL / "book1_rules" / "account")
    with_shadow = run([strategy("sc-a"), candidate], shadow=misplaced, registered=[candidate.key])
    refused = next(o for o in with_shadow.outcomes if o.opportunity.strategy.name == "sc-new")
    assert refused.decision == Decision.SHADOW_NO_TRADE and refused.risk is None and "overlaps" in refused.reason
    book1 = [o.record() for o in with_shadow.outcomes if o.opportunity.mode == "book"]
    assert book1 == [o.record() for o in run([strategy("sc-a")]).outcomes]
