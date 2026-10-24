"""Judge 487 finding 2 and the minors: every check the harness makes is shown to fail on a bad run, so none can be
deleted with the tests still green."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.school.acceptance.faults import expiry_mismatch, missing_quote, refused_entry, stale_seal
from fno.school.constants import ExitReason, RefusalReason, RoadCode
from fno.school.contracts.accounts import LedgerEntry
from fno.school.contracts.fleet import RunMode
from tests.school.acceptance import harness as h
from tests.school.acceptance.recorded_day import CAP_RS, recorded_day
from tests.school.acceptance.rig import fake_rig
from tests.school.contracts import builders as b

ROAD, OTHER = RoadCode.BANKNIFTY_MONTHLY, RoadCode.FINNIFTY_MONTHLY
CLEAN = recorded_day()


def run_of(scenario):
    rig = fake_rig(scenario)
    return rig, rig.fleet.run(scenario.session, RunMode.REPLAY)


def opening(rig) -> LedgerEntry:
    return next(e for e in rig.ledger() if not e.closes)


def test_a_closure_that_leaks_to_another_road_fails_the_fault_check():
    rig, run = run_of(expiry_mismatch(OTHER).plant(expiry_mismatch(ROAD).plant(CLEAN)))
    with pytest.raises(AssertionError, match="leaked"):
        h.verify_fault(expiry_mismatch(ROAD), rig, run, run)


def test_a_position_opened_for_a_refused_entry_fails_the_fault_check():
    fault = refused_entry(ROAD)
    rig, run = run_of(fault.plant(CLEAN))
    clean_rig, _ = run_of(CLEAN)
    entry = opening(clean_rig)
    position = replace(entry.position, driver_id=fault.driver_id, road=ROAD, position_id="opened for the refusal")
    with pytest.raises(AssertionError, match="position opened"):
        h.verify_fault(fault, h.with_ledger(rig, (LedgerEntry(position, entry.fill, closes=False),)), run, run)


def test_a_stale_seal_that_still_reaches_the_ledger_fails_the_fault_check():
    rig, run = run_of(stale_seal().plant(CLEAN))
    clean_rig, _ = run_of(CLEAN)
    with pytest.raises(AssertionError):
        h.verify_fault(stale_seal(), h.with_ledger(rig, (opening(clean_rig),)), run, run)


class Rerunning:
    """A fleet whose rerun does more than skip: it fills again, or seals other decisions."""

    def __init__(self, fleet, again):
        self.fleet, self.again, self.calls = fleet, again, 0

    def run(self, session, mode):
        run = self.fleet.run(session, mode)
        self.calls += 1
        return run if self.calls == 1 else self.again(run)


def test_a_rerun_that_fills_again_or_seals_other_decisions_fails_the_replay_check():
    again_fills = lambda run: replace(run, fills=(b.filled(),))  # noqa: E731
    again_decisions = lambda run: replace(run, decisions=run.decisions[:-1])  # noqa: E731
    for again in (again_fills, again_decisions):

        def build(scenario, again=again):
            rig = fake_rig(scenario)
            return replace(rig, fleet=Rerunning(rig.fleet, again))

        with pytest.raises(AssertionError):
            h.check_replay_twice(build, CLEAN)


def test_a_scheduled_decision_with_no_sealed_outcome_fails_the_fault_check():
    rig, run = run_of(expiry_mismatch(ROAD).plant(CLEAN))
    dropped = replace(run, decisions=run.decisions[:-1])  # the last record belongs to a road the fault does not name
    with pytest.raises(AssertionError, match="no sealed outcome"):
        h.verify_fault(expiry_mismatch(ROAD), rig, dropped, run)


def test_a_trade_decision_over_the_cap_fails_the_over_cap_check():
    lax = replace(CLEAN, cap_rs=2 * CAP_RS)
    rig, run = run_of(refused_entry(ROAD, cap_multiple=0.6).plant(lax))  # 12,000 passes a law that allows 20,000
    strict = replace(rig, scenario=replace(rig.scenario, cap_rs=CAP_RS))
    with pytest.raises(AssertionError, match="over-cap trade"):
        h.check_no_over_cap_trades(strict, run)
    h.check_no_over_cap_trades(rig, run)


def test_a_refusal_with_another_reason_than_the_planted_one_fails_the_fault_check():
    fault = refused_entry(ROAD)
    rig, run = run_of(fault.plant(CLEAN))
    h.verify_fault(fault, rig, run, run)
    with pytest.raises(AssertionError):
        h.verify_fault(replace(fault, reason=RefusalReason.BRAKE), rig, run, run)


def test_the_fill_path_reason_must_be_on_the_planted_drivers_own_fill():
    rig, run = run_of(missing_quote(ROAD).plant(CLEAN))
    cs1 = replace(missing_quote(ROAD), driver_id="CS1@1")
    dr1 = replace(missing_quote(ROAD), driver_id="DR1@1")
    h.verify_fault(cs1, rig, run, run)
    h.verify_fault(dr1, rig, run, run)
    trades = [(r.road, r.decision.driver_id) for r in run.decisions if r.decision.outcome == "trade"]
    swapped = list(run.fills)
    swapped[trades.index((ROAD, "DR1@1"))] = b.filled()  # DR1's own fill did not refuse; CS1's still did
    other_fills = replace(run, fills=tuple(swapped))
    h.verify_fault(cs1, rig, other_fills, run)
    with pytest.raises(AssertionError, match="own fill"):
        h.verify_fault(dr1, rig, other_fills, run)
    with pytest.raises(AssertionError, match="own fill"):
        h.verify_fault(replace(missing_quote(ROAD), reason=RefusalReason.STALE_SEAL, driver_id="CS1@1"), rig, run, run)


def test_a_partial_fill_fails_the_invented_fill_check():
    rig, _ = run_of(CLEAN)
    entry = opening(rig)
    partial = LedgerEntry(replace(entry.position, position_id="partial"), replace(entry.fill, legs=entry.fill.legs[:1]),
                          closes=False)  # fmt: skip
    with pytest.raises(AssertionError, match="partial"):
        h.check_no_invented_fills(h.with_ledger(rig, (partial,)))


def exit_of(rig, price_shift: float = 0.0, reason=ExitReason.PROFIT_TARGET) -> LedgerEntry:
    """The first position closed at the touch of the same snapshot (a buy back pays the ask, a sale takes the bid)."""
    entry = opening(rig)
    snapshot = rig.snapshot_for(entry.position.road)
    flip = {SIDE_BUY: SIDE_SELL, SIDE_SELL: SIDE_BUY}
    legs = tuple(
        replace(leg, side=flip[leg.side], price=_touch(snapshot, leg, flip) + price_shift) for leg in entry.fill.legs
    )
    return LedgerEntry(replace(entry.position, position_id="closing"), replace(entry.fill, legs=legs), closes=True,
                       exit_reason=reason)  # fmt: skip


def _touch(snapshot, leg, flip):
    quote = snapshot.quote(leg.key)
    return quote.ask if flip[leg.side] == SIDE_BUY else quote.bid


def test_exits_are_held_to_the_touch_too_and_a_settlement_is_left_to_its_own_checks():
    rig, _ = run_of(CLEAN)
    h.check_no_invented_fills(h.with_ledger(rig, (exit_of(rig),)))
    with pytest.raises(AssertionError, match="touch"):
        h.check_no_invented_fills(h.with_ledger(rig, (exit_of(rig, price_shift=0.5),)))
    h.check_no_invented_fills(h.with_ledger(rig, (exit_of(rig, 0.5, ExitReason.EXPIRY),)))  # intrinsic, not a quote


def test_the_clean_day_still_passes_after_all_of_that():
    rig, run = run_of(CLEAN)
    h.check_fills(rig, run)
    assert rig.scenario.fill_at - rig.scenario.seal_pushed_at == timedelta(minutes=1)
