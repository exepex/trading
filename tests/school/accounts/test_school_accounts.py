"""Story MS-P1d: one E1 paper account per driver version (criterion 11's conformance), opened at Rs 20 lakh, written
only through its lock, fills recorded once with C1's charges, positions marked at their road's mids (worst case when a
leg cannot be marked), one equity row per session, and the files mirrored through E2c's private files."""

from datetime import timedelta

import pytest

from fno.books.account import AccountError, AccountWriter, PaperAccount
from fno.books.lock import AccountLock
from fno.constants import LEDGER_FILL, LEDGER_SETTLEMENT
from fno.school.accounts.ledger_fills import EntryMismatch, ledger_fills
from fno.school.accounts.names import account_name
from fno.school.accounts.position_book import EntryConflict
from fno.school.constants import ExitReason
from fno.school.contracts.accounts import LedgerEntry
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c
from tests.school.execution.school_builders import CHARGES, fills, settlement_folder

from .account_builders import ACCOUNT_RS, NEXT, Sync, accounts, closing, marks, opening, spread_quotes


def ledger(tmp_path) -> list[dict]:
    return PaperAccount(tmp_path, account_name("CS1@1")).ledger_rows()


def test_the_account_port_conforms(tmp_path):
    c.check_account_port(accounts(tmp_path), opening(tmp_path), marks(), b.SESSION)


def test_an_account_opens_at_the_school_s_size_on_first_view(tmp_path):
    view = accounts(tmp_path).view("CS1@1", {}, b.SESSION)
    assert (view.capital, view.cash, view.equity, view.equity_high) == (ACCOUNT_RS,) * 4
    assert view.loss_since_previous_slot == 0 and view.brake_engaged_on is None and not view.open_positions
    folder = tmp_path / "journal" / "shadow" / "school-cs1-v1" / "account"
    assert (folder / "cash_ledger.csv").exists(), "under the school's own root, never the desk's journal/shadow"


def test_an_entry_moves_cash_by_its_fills_and_is_recorded_once(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    port.record("CS1@1", entry)
    rows = [r for r in ledger(tmp_path) if r["kind"] == LEDGER_FILL]
    assert len(rows) == 2 and {r["trade_id"] for r in rows} == {"p1"}
    received = sum(leg.price * leg.units * (1 if leg.side == "sell" else -1) - leg.charges for leg in entry.fill.legs)
    assert port.view("CS1@1", marks(), b.SESSION).cash == pytest.approx(ACCOUNT_RS + received)


def test_a_different_entry_for_a_recorded_position_is_refused(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    other = LedgerEntry(entry.position, opening(tmp_path / "x", lots=1).fill, closes=False)
    moved = LedgerEntry(other.position, type(other.fill)(other.fill.legs, filled_at=other.fill.filled_at,
                                                         rests_on="ff" * 32), closes=False)  # fmt: skip
    with pytest.raises(EntryConflict):
        port.record("CS1@1", moved)


def test_a_fill_that_does_not_match_its_position_writes_nothing(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    half = LedgerEntry(entry.position, type(entry.fill)(entry.fill.legs[:1], filled_at=entry.fill.filled_at,
                                                        rests_on=entry.fill.rests_on), closes=False)  # fmt: skip
    with pytest.raises(EntryMismatch):
        port.record("CS1@1", half)
    assert not [r for r in ledger(tmp_path) if r["kind"] == LEDGER_FILL]


def test_a_fill_before_the_first_view_or_for_another_driver_is_refused(tmp_path):
    with pytest.raises(AccountError, match="first view"):
        accounts(tmp_path).record("CS1@1", opening(tmp_path))
    with pytest.raises(ValueError, match="belongs to"):
        accounts(tmp_path).record("DB1@1", opening(tmp_path))


def test_a_close_ends_the_position_and_realises_its_net(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    port.record("CS1@1", closing(tmp_path, entry))
    view = port.view("CS1@1", marks(), b.SESSION)
    assert not view.open_positions and [p.position_id for p in view.opened_this_session] == ["p1"]
    assert view.equity == pytest.approx(view.cash)


def test_a_settlement_is_recorded_as_one(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    settled = fills(settlement_folder(tmp_path / "nse", day=b.EXPIRY)).settle(entry.position, b.EXPIRY)
    port.record("CS1@1", LedgerEntry(entry.position, settled, closes=True, exit_reason=ExitReason.EXPIRY))
    assert [r["kind"] for r in ledger(tmp_path)].count(LEDGER_SETTLEMENT) == 2


def test_open_positions_are_marked_at_their_road_s_mids(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    view = port.view("CS1@1", marks(spread_quotes(20.0, 6.0), NEXT), NEXT)
    assert view.equity == pytest.approx(view.cash - 20.0 * 30 + 6.0 * 30)


def test_an_unmarkable_position_counts_at_its_maximum_loss(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    view = port.view("CS1@1", marks({b.key(1000.0): b.quote()}, NEXT), NEXT)  # the 900 put has no quote
    assert view.equity == pytest.approx(ACCOUNT_RS - entry.position.max_loss)
    row = [r for r in PaperAccount(tmp_path, account_name("CS1@1")).equity_history() if r["date"] == str(NEXT)][0]
    assert row["stale_marks"] == "BANKNIFTY20261123PE900"


def test_the_session_row_is_written_once_at_the_first_view(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    first = port.view("CS1@1", marks(spread_quotes(20.0, 6.0), NEXT), NEXT)
    again = port.view("CS1@1", marks(spread_quotes(60.0, 6.0), NEXT), NEXT)
    rows = [r for r in PaperAccount(tmp_path, account_name("CS1@1")).equity_history() if r["date"] == str(NEXT)]
    assert len(rows) == 1 and float(rows[0]["marked_equity_rs"]) == pytest.approx(first.equity)
    assert again.equity < first.equity, "the view itself is current; the row stays the slot's first"


def test_the_loss_since_the_previous_slot(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path, lots=10)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    view = port.view("CS1@1", marks(spread_quotes(30.0, 6.0), NEXT), NEXT)
    assert view.loss_since_previous_slot == pytest.approx(ACCOUNT_RS - view.equity)
    later = port.view("CS1@1", marks(spread_quotes(10.5, 4.5), NEXT + timedelta(1)), NEXT + timedelta(1))
    assert later.loss_since_previous_slot == 0.0, "a gain is no loss"


def test_ledger_and_position_records_must_agree(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    (tmp_path / "journal" / "shadow" / "school-cs1-v1" / "account" / "school_positions.jsonl").write_text("")
    with pytest.raises(AccountError, match="disagree"):
        port.view("CS1@1", marks(), b.SESSION)


def test_files_are_pulled_once_and_pushed_after_each_write(tmp_path):
    sync = Sync()
    port = accounts(tmp_path, sync=sync)
    port.view("CS1@1", marks(), b.SESSION)
    port.view("CS1@1", marks(), b.SESSION)  # nothing new to write: no push
    port.record("CS1@1", opening(tmp_path))
    names = ["cash_ledger.csv", "positions.json", "equity_history.csv", "school_positions.jsonl"]
    assert sync.pulled == [names] and sync.pushed == [names, names]


@pytest.mark.parametrize("driver_id", ["cs1@1", "CS1@0", "CS1", "CS-1@1"])
def test_a_driver_id_of_another_form_is_refused(driver_id):
    with pytest.raises(ValueError, match="not <code>@<version>"):
        account_name(driver_id)


def test_a_crash_part_way_through_a_close_is_caught_unit_for_unit(tmp_path):
    """One of two close fills reached the ledger: the IDs still agree, the units do not; nothing is valued."""
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    half = ledger_fills(closing(tmp_path, entry), CHARGES)[0]
    with AccountLock(tmp_path, account_name("CS1@1")) as lock:
        AccountWriter(PaperAccount(tmp_path, account_name("CS1@1")), lock, ACCOUNT_RS).apply_fill(half)
    with pytest.raises(AccountError, match="disagree"):
        port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", closing(tmp_path, entry))  # the rerun completes the close
    assert not port.view("CS1@1", marks(), b.SESSION).open_positions


def test_a_view_never_looks_back_at_an_earlier_session(tmp_path):
    port = accounts(tmp_path)
    port.view("CS1@1", marks(session=NEXT), NEXT)
    with pytest.raises(ValueError, match="look ahead"):
        port.view("CS1@1", marks(), b.SESSION)


def test_a_close_of_a_position_never_opened_or_a_reused_id_is_refused_before_any_fill(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path)
    port.view("CS1@1", marks(), b.SESSION)
    with pytest.raises(EntryConflict, match="not open"):
        port.record("CS1@1", closing(tmp_path, entry))
    assert not [r for r in ledger(tmp_path) if r["kind"] == LEDGER_FILL]
    port.record("CS1@1", entry)
    port.record("CS1@1", closing(tmp_path, entry))
    with pytest.raises(EntryConflict, match="already recorded differently"):  # a second close of p1
        port.record("CS1@1", LedgerEntry(entry.position, closing(tmp_path, entry, spread_quotes(9.0, 4.0)).fill,
                                         closes=True, exit_reason=ExitReason.PROFIT_TARGET))  # fmt: skip
    with pytest.raises(EntryConflict, match="already recorded differently"):  # p1 reused for another position
        port.record("CS1@1", opening(tmp_path, lots=2))
