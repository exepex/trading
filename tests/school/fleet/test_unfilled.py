"""Story MS-P1j for MS-INS part e: the fired entries that never filled, from the dashcam and the ledgers."""

from dataclasses import replace

from fno.school.contracts.fleet import RunMode
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.unfilled import UnfilledEntries
from tests.school.contracts import builders as b
from tests.school.fleet.rig import DAY2, OPEN_ROAD, Rig, all_roads

LAWS = (FakeMaxLossLaw(10_000),)


def thin_rig(tmp_path, *codes, max_new=5) -> Rig:
    quotes = {k: replace(q, bid_qty=30, ask_qty=30) for k, q in b.snapshot().quotes.items()}
    snapshots = {(OPEN_ROAD, s): replace(b.snapshot(quotes=quotes), session=s) for s in (b.SESSION, DAY2)}
    drivers = tuple(FakeDriver(all_roads(c), b.put_spread()) for c in codes) + (FakeDriver(all_roads("N0")),)
    return Rig(tmp_path, drivers, LAWS, snapshots=snapshots, max_new=max_new)


def unfilled(rig: Rig):
    books = rig.fleet.books
    return UnfilledEntries(rig.dashcam, books.account_entries, books.ticket_entries)


def test_an_entry_the_shared_size_could_not_serve_is_unfilled_and_the_served_one_is_not(tmp_path):
    rig = thin_rig(tmp_path, "CS1", "REF")
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    filled = {e.position.driver_id for ledger in rig.accounts.ledgers.values() for e in ledger}
    [loser] = {"CS1@1", "REF@1"} - filled
    assert unfilled(rig)(b.SESSION, b.SESSION) == {(loser, OPEN_ROAD, b.SESSION)}


def test_tickets_count_the_same_way_and_a_no_trade_never_appears(tmp_path):
    rig = thin_rig(tmp_path, "CS1", "REF", max_new=0)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    found = unfilled(rig)(b.SESSION, b.SESSION)
    assert len(found) == 1 and all(driver != "N0@1" for driver, _, _ in found)


def test_sessions_outside_the_range_and_days_with_no_session_are_left_out(tmp_path):
    rig = thin_rig(tmp_path, "CS1", "REF")
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert unfilled(rig)(DAY2, DAY2) == frozenset()
    assert len(unfilled(rig)(b.SESSION - b.SESSION.resolution * 3, DAY2)) == 1
