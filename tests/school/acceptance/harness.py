"""The acceptance harness (story MS-P1i): fault verification, the four fill checks, the two-run comparator and the
replay-twice check. Everything takes a `Rig`; story j runs the same functions over the real wiring."""

from collections.abc import Callable
from dataclasses import replace

import pytest

from fno.constants import SIDE_BUY
from fno.school.acceptance.faults import Expect, Fault
from fno.school.acceptance.scenario import Scenario
from fno.school.constants import SLOT_1500, Outcome, RecordKind, RefusalReason
from fno.school.contracts.accounts import LedgerEntry
from fno.school.contracts.dashcam import ReplayConflict
from fno.school.contracts.fleet import RunMode, SessionRun
from fno.school.contracts.slot_file import encode_slot_file
from tests.school.acceptance.rig import Rig

BuildRig = Callable[[Scenario], Rig]


# --- the four fill checks: zero unsealed, over-cap, invented or duplicate fills


def check_no_unsealed_fills(rig: Rig, run: SessionRun) -> None:
    """Every entry rests on the sealed decisions file and was made no earlier than the seal's push."""
    seal = rig.dashcam.find(run.session, SLOT_1500, RecordKind.DECISIONS)
    entries = [e for e in rig.ledger() if not e.closes]
    assert entries == [] or seal is not None, "fills exist but no decisions file was sealed"
    for fill in [e.fill for e in entries] + [f for f in run.fills if f.filled]:
        assert seal.covers(fill.rests_on, fill.filled_at), f"unsealed fill resting on {fill.rests_on[:8]}"


def check_no_over_cap_trades(rig: Rig, run: SessionRun) -> None:
    """No trade decision and no opened position risks more than the per-trade cap."""
    cap = rig.scenario.cap_rs
    for record in rig.sealed_decisions(run.session):
        if record.decision.outcome == Outcome.TRADE:
            assert record.decision.proposal.max_loss <= cap, f"over-cap trade {record.decision.driver_id}"
    for entry in rig.ledger():
        assert entry.position.max_loss <= cap, f"over-cap position {entry.position.position_id}"


def check_no_invented_fills(rig: Rig) -> None:
    """Every entry leg fills at the touch of a two-sided quote of its road's snapshot (ask to buy, bid to sell)."""
    for entry in (e for e in rig.ledger() if not e.closes):
        snapshot = rig.snapshot_for(entry.position.road)
        assert len(entry.fill.legs) == len(entry.position.legs), "a partial fill"
        for leg in entry.fill.legs:
            quote = snapshot.quote(leg.key)
            assert quote is not None and quote.two_sided, f"fill with no two-sided quote: {entry.position.position_id}"
            touch = quote.ask if leg.side == SIDE_BUY else quote.bid
            assert leg.price == touch, f"fill away from the touch: {entry.position.position_id}"


def check_no_duplicate_fills(rig: Rig) -> None:
    ids = [e.position.position_id for e in rig.ledger() if not e.closes]
    assert len(ids) == len(set(ids)), "a position opened twice"
    per_slot = [(e.position.driver_id, e.position.road, e.position.opened) for e in rig.ledger() if not e.closes]
    assert len(per_slot) == len(set(per_slot)), "two entries for one scheduled road decision"


def check_fills(rig: Rig, run: SessionRun) -> None:
    check_no_unsealed_fills(rig, run)
    check_no_over_cap_trades(rig, run)
    check_no_invented_fills(rig)
    check_no_duplicate_fills(rig)


# --- the planted faults


def verify_fault(fault: Fault, rig: Rig, run: SessionRun, baseline: SessionRun) -> None:
    """The fault's exact reason code came out, no position opened for it, and nothing else changed."""
    records = {(r.road, r.decision.driver_id): r for r in run.decisions}
    opened = {(e.position.road, e.position.driver_id) for e in rig.ledger() if not e.closes}
    if fault.expect is Expect.ROAD_CLOSED:
        on_road = [r for key, r in records.items() if key[0] == fault.road]
        assert on_road, "no decision on the planted road"
        assert {(r.decision.outcome, r.decision.reason) for r in on_road} == {(Outcome.ROAD_CLOSED, fault.reason)}
        assert not [key for key in opened if key[0] == fault.road]
        others = {key: r.decision.outcome for key, r in records.items() if key[0] != fault.road}
        assert Outcome.ROAD_CLOSED not in others.values(), "a closure leaked to another road"
    elif fault.expect is Expect.REFUSED_OR_UNFILLED:
        driver = fault.driver_id or next(p.card.driver_id for p in rig.scenario.drivers if p.proposal is not None)
        decision = records[(fault.road, driver)].decision
        assert (fault.road, driver) not in opened, "a position opened for a refused entry"
        if decision.outcome == Outcome.REFUSED:
            assert decision.reason == fault.reason and decision.proposal is not None
        else:
            assert decision.outcome == Outcome.TRADE
            assert any(fault.reason in fill.refused for fill in run.fills), "no fill refused with the reason"
    elif fault.expect is Expect.ALL_FILLS_STALE:
        assert run.decisions_seal is not None and run.fills
        assert all(fill.refused == (RefusalReason.STALE_SEAL,) for fill in run.fills)
        assert not rig.ledger()
    elif fault.expect is Expect.REPLAY_CONFLICT:
        before = rig.dashcam.read(run.decisions_seal)
        with pytest.raises(ReplayConflict):
            rig.dashcam.seal(run.session, SLOT_1500, RecordKind.DECISIONS, before[:-1])
        assert rig.dashcam.read(run.decisions_seal) == before, "a sealed file changed"
    assert len(run.decisions) == len(rig.scenario.scheduled), "a scheduled road decision has no sealed outcome"
    assert baseline.decisions, "the clean day sealed nothing"


def run_fault(fault: Fault, build: BuildRig, clean: Scenario) -> tuple[Rig, SessionRun]:
    rig = build(fault.plant(clean))
    run = rig.fleet.run(rig.scenario.session, RunMode.REPLAY)
    baseline = build(clean).fleet.run(clean.session, RunMode.REPLAY)
    verify_fault(fault, rig, run, baseline)
    check_fills(rig, run)
    return rig, run


# --- the two-run comparator


def files_of(rig: Rig, session) -> dict[str, bytes]:
    """The bytes of every sealed record file and the public counts file of the session."""
    files = {}
    for kind in RecordKind:
        seal = rig.dashcam.find(session, SLOT_1500, kind)
        if seal is not None:
            files[f"{kind}.jsonl.gz"] = encode_slot_file(rig.dashcam.read(seal))
    files["counts.json"] = rig.count_file(session)
    return files


def differences(first: dict[str, bytes], second: dict[str, bytes]) -> list[str]:
    return sorted(name for name in first.keys() | second.keys() if first.get(name) != second.get(name))


def check_replay_twice(build: BuildRig, scenario: Scenario) -> dict[str, bytes]:
    """One recorded session run twice in two fresh worlds gives byte-identical files, and a rerun in the same world
    seals and fills nothing new."""
    one, two = build(scenario), build(scenario)
    first = one.fleet.run(scenario.session, RunMode.REPLAY)
    two.fleet.run(scenario.session, RunMode.REPLAY)
    assert differences(files_of(one, scenario.session), files_of(two, scenario.session)) == []
    again = one.fleet.run(scenario.session, RunMode.REPLAY)
    assert (again.decisions, again.decisions_seal, again.fills) == (first.decisions, first.decisions_seal, ())
    assert differences(files_of(one, scenario.session), files_of(two, scenario.session)) == []
    return files_of(one, scenario.session)


def with_ledger(rig: Rig, extra: tuple[LedgerEntry, ...]) -> Rig:
    """The same rig with entries appended to its ledger view (used to plant a bad fill for the checks)."""
    return replace(rig, ledger=lambda: rig.ledger() + extra)
