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

from .builders import (
    DAY,
    DECIDED_AT,
    approved,
    at,
    decision_market,
    enter,
    fly_order,
    fly_proposal,
    fly_rows,
    write_snapshot,
)

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
    account = JournalShadowBooks(started, decision_market(), lambda account: {}).account(CANDIDATE)
    assert NAME == "shadow:cand-c-v1" and account.book.name == NAME
    assert account.storage == started / "journal" / "shadow" / "cand-c-v1" / "account"
    real = RealBooks(BOOKS, [started / "journal" / book for book in BOOKS])
    assert real.overlap(account) is None and account.book.state.cash == 2_000_000.0


def test_trading_in_the_shadow_account_writes_only_inside_its_declared_folder(started, store, snapshots, entry_desk):
    storage = JournalShadowBooks(started, decision_market(), lambda account: {}).account(CANDIDATE).storage
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
    counts = JournalShadowBooks(started, decision_market(), lambda account: {}).account(CANDIDATE).counts
    assert (counts.open("cand-c", 1), counts.completed("cand-c", 1)) == (0, 0)  # an unwound entry never opened
    write_snapshot(store, "exec2", fly_rows(), at(15, 16), at(15, 16, 40))
    assert enter(started, snapshots, entry_desk, shadow_order("t2"), "exec2").outcome == OUTCOME_OPENED
    assert (counts.open("cand-c", 1), counts.completed("cand-c", 1), counts.open("other", 1)) == (1, 0, 0)


def test_an_unstarted_shadow_account_is_refused_not_created(root):
    with pytest.raises(ValueError, match="has not been started"):
        JournalShadowBooks(root, decision_market(), lambda account: {}).account(CANDIDATE)
    assert not (root / "journal" / "shadow").exists()


def test_a_shadow_with_an_open_trade_is_valued_on_its_own_terms_never_book_1s(started, store, snapshots, entry_desk):
    """Story R3 criterion 2: a shadow's open trade needs its own recorded terms. With terms that lack it (as Book 1's
    did before R3), C2's view raises; with its own, it loads, and the lookup is asked for the shadow account only."""
    from fno.risk.book_view import RiskInputError
    from fno.risk.inputs import TradeTerms

    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    assert enter(started, snapshots, entry_desk, shadow_order("t1")).outcome == OUTCOME_OPENED
    with pytest.raises(RiskInputError, match="has no recorded terms"):
        JournalShadowBooks(started, decision_market(), lambda account: {}).account(CANDIDATE)
    asked = []
    own = lambda account: asked.append(account) or {"t1": TradeTerms("SF", 200, 1)}  # noqa: E731
    account = JournalShadowBooks(started, decision_market(), own).account(CANDIDATE)
    assert asked == [NAME] and [t.trade_id for t in account.book.open_trades] == ["t1"]


def _book1_run_on(root, records: dict[str, dict]) -> None:
    """Book 1's committed run of DAY (one folder for book and shadow records, as D2 writes it), named by the run log."""
    import json

    from fno.constants import BOOK1_RULES
    from fno.desk.run_log import RunLog
    from fno.playbook.decision_store import SUMS_FILE, DecisionStore

    run = DecisionStore(root, BOOK1_RULES).day_folder(DAY) / f"{DAY}-r1"
    run.mkdir(parents=True)
    for name, record in records.items():
        (run / name).write_text(json.dumps(record))
    (run / SUMS_FILE).write_text(
        "".join(f"{hashlib.sha256((run / n).read_bytes()).hexdigest()}  {n}\n" for n in records)
    )
    entry = {"run_id": run.name, "commit": "c1", "committed_at": DECIDED_AT.isoformat()}
    RunLog.open(root, DAY).record("decisions", DECIDED_AT, DECIDED_AT, {}, {BOOK1_RULES: entry})


def test_book1_s_parts_give_each_shadow_book_its_own_trade_terms(started, store, snapshots, entry_desk):
    """Judge 210 finding 1, criterion 2 where it takes effect: `_parts` (Book 1's composition root) values a shadow's
    open trade on the shadow record's terms. Given Book 1's terms instead, the shadow's trade has none and C2 raises."""
    from fno.books.book1_wiring import _parts
    from fno.constants import BOOK1_RULES, STRUCTURE_SHORT_IRON_FLY

    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    assert enter(started, snapshots, entry_desk, fly_order("b1")).outcome == OUTCOME_OPENED  # Book 1's own trade
    assert enter(started, snapshots, entry_desk, shadow_order("t1")).outcome == OUTCOME_OPENED
    trade = {"structure": STRUCTURE_SHORT_IRON_FLY, "width": 200, "lots": 1}
    book = {"chosen_action": "trade", "opportunity_id": "fixture-fly-v1:2026-11-24", "mode": "book"}
    _book1_run_on(started, {"a.json": book | {"structure": trade | {"trade_id": "b1"}},
                            "b.json": book | {"mode": "shadow", "structure": trade | {"trade_id": "t1"}}})  # fmt: skip
    risk_book, _, shadow_books = _parts(started, decision_market())
    assert [t.trade_id for t in risk_book.open_trades] == ["b1"]
    assert [t.trade_id for t in shadow_books.account(CANDIDATE).book.open_trades] == ["t1"]
    assert BOOK1_RULES not in str(shadow_books.account(CANDIDATE).storage)
