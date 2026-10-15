"""Story E6 (D2's `ShadowBooks`, owned by E6): a research candidate's shadow account is its own paper account under
`journal/shadow/<name>-v<n>/account/`; trading in it writes only inside that declared folder, never a book's, and D2's
`RealBooks` finds no overlap. Trade counts come from that account's desk records only."""

import hashlib
from pathlib import Path

import pytest
from playbook.builders import document

from fno.constants import BOOKS, OPTION_PUT, OUTCOME_OPENED, OUTCOME_PARTIAL_FILL
from fno.desk.shadow_books import JournalShadowBooks, shadow_name
from fno.desk.wiring import start_shadow_books
from fno.playbook.schema import parse_strategy
from fno.playbook.shadow import RealBooks

from .builders import DAY, approved, at, decision_market, enter, fly_order, fly_proposal, fly_rows, write_snapshot

CANDIDATE = parse_strategy(document(name="cand-c"))  # a research candidate
NAME = shadow_name(CANDIDATE)


def files(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}  # fmt: skip


def shadow_order(trade_id="t1"):
    proposal = fly_proposal(trade_id)
    return fly_order(trade_id, book=NAME, risk=approved(proposal, NAME), strategy="cand-c-v1")


@pytest.fixture
def started(root):
    assert start_shadow_books([CANDIDATE], DAY, root) == [NAME]
    assert start_shadow_books([CANDIDATE], DAY, root) == []  # once only
    return root


def test_the_shadow_account_is_its_own_folder_and_no_real_book_overlaps_it(started):
    account = JournalShadowBooks(started, decision_market(), {}).account(CANDIDATE)
    assert NAME == "shadow:cand-c-v1" and account.book.name == NAME
    assert account.storage == started / "journal" / "shadow" / "cand-c-v1" / "account"
    real = RealBooks(BOOKS, [started / "journal" / book for book in BOOKS])
    assert real.overlap(account) is None and account.book.state.cash == 2_000_000.0


def test_trading_in_the_shadow_account_writes_only_inside_its_declared_folder(started, store, snapshots, entry_desk):
    storage = JournalShadowBooks(started, decision_market(), {}).account(CANDIDATE).storage
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))  # the quote store is not in `started`
    before = files(started)
    assert enter(started, snapshots, entry_desk, shadow_order()).outcome == OUTCOME_OPENED
    after = files(started)
    changed = {path for path in after if before.get(path) != after[path]} | (before.keys() - after.keys())
    assert changed and all((started / path).resolve().is_relative_to(storage.resolve()) for path in changed)
    assert not any(path.startswith(f"journal/{book}/") for path in changed for book in BOOKS)


def test_trade_counts_come_from_the_shadow_accounts_own_records(started, store, snapshots, entry_desk, check_passed):
    """The unwound entry comes through E4c's guard (a fill failing after the entry check)."""
    write_snapshot(store, "exec", fly_rows({(25000, OPTION_PUT): {"valid": False}}), at(15, 15), at(15, 15, 40))
    assert enter(started, snapshots, entry_desk, shadow_order("t1")).outcome == OUTCOME_PARTIAL_FILL
    counts = JournalShadowBooks(started, decision_market(), {}).account(CANDIDATE).counts
    assert (counts.open("cand-c", 1), counts.completed("cand-c", 1)) == (0, 0)  # an unwound entry never opened
    write_snapshot(store, "exec2", fly_rows(), at(15, 16), at(15, 16, 40))
    assert enter(started, snapshots, entry_desk, shadow_order("t2"), "exec2").outcome == OUTCOME_OPENED
    assert (counts.open("cand-c", 1), counts.completed("cand-c", 1), counts.open("other", 1)) == (1, 0, 0)


def test_an_unstarted_shadow_account_is_refused_not_created(root):
    with pytest.raises(ValueError, match="has not been started"):
        JournalShadowBooks(root, decision_market(), {}).account(CANDIDATE)
    assert not (root / "journal" / "shadow").exists()
