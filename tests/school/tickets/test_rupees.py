"""Story MS-P1f follow-up (judges 481.2 and 490.2): an account outcome whose exit the shared displayed size could not
serve is left out of `account_net` and named, as an unservable entry is."""

from dataclasses import replace
from datetime import timedelta

from fno.school.constants import SIDE_BUY, SIDE_SELL
from fno.school.contracts.accounts import FilledLeg, FillResult
from fno.school.tickets.rupees import account_net
from fno.school.tickets.shared_size import OwnedFill, allocate
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import outcome_record

AT = b.SLOT_AT + timedelta(minutes=4)
SNAP = b.snapshot(quotes={b.key(1000.0): b.quote(size=30), b.key(900.0): b.quote(4.0, 5.0, size=30)})


def closing(units: int = 30) -> FillResult:
    """Buys the short back and sells the protection: an exit of the fixture put spread."""
    legs = (FilledLeg(b.key(1000.0), SIDE_BUY, units, 11.0, 0.0), FilledLeg(b.key(900.0), SIDE_SELL, units, 4.0, 0.0))
    return FillResult(legs, filled_at=AT, rests_on="cd" * 32)


def test_an_outcome_whose_exit_could_not_be_served_is_left_out_and_named():
    exit_fill = closing()
    allocation = allocate([OwnedFill("CS1@1", exit_fill), OwnedFill("REF@1", exit_fill)], SNAP, "15:00")
    lost = allocation.unservable[0].owner
    outcomes = [replace(outcome_record(), position_id=f"p-{owner}", driver_id=owner, exit=exit_fill, net=250.0)
                for owner in ("CS1@1", "REF@1")]  # fmt: skip
    total = account_net(outcomes, allocation.unservable_fills)
    assert total.net == 250.0 and total.left_out == (f"p-{lost}",)


def test_an_exit_that_fits_beside_the_others_is_summed():
    exit_fill = closing(15)
    allocation = allocate([OwnedFill("CS1@1", exit_fill), OwnedFill("REF@1", exit_fill)], SNAP, "15:00")
    outcomes = [replace(outcome_record(), position_id=owner, driver_id=owner, exit=exit_fill, net=250.0)
                for owner in ("CS1@1", "REF@1")]  # fmt: skip
    assert allocation.unservable == () and account_net(outcomes, allocation.unservable_fills).net == 500.0
