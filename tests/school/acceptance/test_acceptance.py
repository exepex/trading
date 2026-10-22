"""Story MS-P1i's acceptance tests on a's fakes. Story j runs the same checks with `real_rig` over the real wiring."""

import json
from dataclasses import replace
from datetime import timedelta

import pytest
from _pytest.outcomes import Failed

from fno.school.acceptance.faults import (
    all_faults,
    expiry_mismatch,
    impossible_price,
    lot_mismatch,
    missing_quote,
    refused_entry,
    replay_conflict,
    stale_seal,
)
from fno.school.constants import SLOT_1500, ClosureReason, Outcome, RecordKind, RefusalReason, RoadCode
from fno.school.contracts.accounts import FilledLeg, FillResult, LedgerEntry
from fno.school.contracts.dashcam import ReplayConflict
from fno.school.contracts.decisions import OpenPosition
from fno.school.contracts.fleet import RunMode
from fno.school.contracts.seal import StaleSeal
from fno.school.contracts.slot_file import encode_slot_file
from fno.school.fakes import FakeDashcam
from tests.school.acceptance import harness as h
from tests.school.acceptance.recorded_day import CAP_RS, FILL_AT, recorded_day
from tests.school.acceptance.rig import fake_rig
from tests.school.contracts import builders as b

ROAD = RoadCode.BANKNIFTY_MONTHLY
CLEAN = recorded_day()


def clean_run():
    rig = fake_rig(CLEAN)
    return rig, rig.fleet.run(CLEAN.session, RunMode.REPLAY)


def test_the_clean_recorded_day_trades_on_every_road_and_passes_every_fill_check():
    rig, run = clean_run()
    assert {(r.road, r.decision.driver_id) for r in run.decisions} == CLEAN.scheduled and len(CLEAN.scheduled) == 15
    assert sum(r.decision.outcome == Outcome.TRADE for r in run.decisions) == 10
    h.check_fills(rig, run)
    assert len(rig.ledger()) == 10


def test_the_fixture_snapshots_start_inside_every_roads_window():
    for snapshot in CLEAN.snapshots.values():
        assert (15, 1) <= (snapshot.started_at.hour, snapshot.started_at.minute) <= (15, 10)


# --- criterion 1: each planter makes the fleet give its exact reason code


@pytest.mark.parametrize("fault", all_faults(ROAD), ids=lambda f: f.name)
def test_each_planter_gives_its_exact_reason_code_and_opens_nothing_for_it(fault):
    h.run_fault(fault, fake_rig, CLEAN)


def test_the_planters_name_the_story_s_codes():
    assert missing_quote(ROAD).reason == RefusalReason.MISSING_QUOTE
    assert expiry_mismatch(ROAD).reason == ClosureReason.EXPIRY_MISMATCH
    assert lot_mismatch(ROAD).reason == ClosureReason.LOT_MISMATCH
    assert impossible_price(ROAD).reason == ClosureReason.IMPOSSIBLE_PRICE
    assert stale_seal().reason == RefusalReason.STALE_SEAL
    assert refused_entry(ROAD).reason == RefusalReason.MAX_LOSS and replay_conflict().reason == ""


def test_a_planter_changes_only_its_own_road_and_driver():
    closed = expiry_mismatch(ROAD).plant(CLEAN)
    assert [d.road.code for d in closed.road_days if not d.status.open] == [ROAD]
    assert closed.snapshots == CLEAN.snapshots and closed.drivers == CLEAN.drivers
    quoteless = missing_quote(ROAD).plant(CLEAN)
    assert len(quoteless.snapshots[ROAD].quotes) == len(CLEAN.snapshots[ROAD].quotes) - 1
    assert all(quoteless.snapshots[r] == CLEAN.snapshots[r] for r in CLEAN.snapshots if r != ROAD)


def test_a_fault_check_fails_when_the_fleet_does_not_catch_the_fault():
    uncaught = replace(CLEAN, fill_at=CLEAN.fill_at)  # the stale-seal fault expects refusals; a clean day has none
    rig = fake_rig(uncaught)
    run = rig.fleet.run(uncaught.session, RunMode.REPLAY)
    with pytest.raises(AssertionError):
        h.verify_fault(stale_seal(), rig, run, run)
    with pytest.raises(AssertionError):
        h.verify_fault(expiry_mismatch(ROAD), rig, run, run)
    with pytest.raises(AssertionError):
        h.verify_fault(missing_quote(ROAD), rig, run, run)


def test_a_wrong_reason_code_is_not_accepted():
    rig = fake_rig(lot_mismatch(ROAD).plant(CLEAN))
    run = rig.fleet.run(CLEAN.session, RunMode.REPLAY)
    with pytest.raises(AssertionError):
        h.verify_fault(expiry_mismatch(ROAD), rig, run, run)  # closed, but for another reason


# --- the four fill checks catch what they are for


def bad_entry(rig, **leg_changes) -> LedgerEntry:
    entry = next(e for e in rig.ledger() if not e.closes)
    leg = entry.fill.legs[0]
    legs = (replace(leg, **leg_changes), *entry.fill.legs[1:])
    return LedgerEntry(replace(entry.position, position_id="planted"), replace(entry.fill, legs=legs), closes=False)


def test_an_unsealed_fill_is_caught():
    rig, run = clean_run()
    entry = next(e for e in rig.ledger() if not e.closes)
    stranger = replace(entry.fill, rests_on="ee" * 32)
    planted = h.with_ledger(rig, (LedgerEntry(replace(entry.position, position_id="x"), stranger, closes=False),))
    with pytest.raises(AssertionError, match="unsealed"):
        h.check_no_unsealed_fills(planted, run)
    early = replace(entry.fill, filled_at=rig.scenario.seal_pushed_at - timedelta(seconds=1))
    with pytest.raises(AssertionError, match="unsealed"):
        h.check_no_unsealed_fills(
            h.with_ledger(rig, (LedgerEntry(replace(entry.position, position_id="y"), early, closes=False),)), run
        )


def test_an_over_cap_position_is_caught():
    rig, run = clean_run()
    entry = next(e for e in rig.ledger() if not e.closes)
    big = LedgerEntry(replace(entry.position, position_id="big", max_loss=CAP_RS + 1), entry.fill, closes=False)
    with pytest.raises(AssertionError, match="over-cap"):
        h.check_no_over_cap_trades(h.with_ledger(rig, (big,)), run)


def test_a_fill_away_from_the_touch_or_without_a_quote_is_caught():
    rig, _ = clean_run()
    off_touch = bad_entry(rig, price=0.01)
    with pytest.raises(AssertionError, match="touch"):
        h.check_no_invented_fills(h.with_ledger(rig, (off_touch,)))
    entry = next(e for e in rig.ledger() if not e.closes)
    ghost_key = replace(entry.fill.legs[0].key, strike=12345.0)
    with pytest.raises(AssertionError, match="no two-sided quote"):
        h.check_no_invented_fills(h.with_ledger(rig, (bad_entry(rig, key=ghost_key),)))


def test_a_duplicate_fill_is_caught():
    rig, _ = clean_run()
    entry = next(e for e in rig.ledger() if not e.closes)
    twin = LedgerEntry(entry.position, replace(entry.fill, filled_at=FILL_AT + timedelta(seconds=1)), closes=False)
    with pytest.raises(AssertionError, match="twice"):
        h.check_no_duplicate_fills(h.with_ledger(rig, (twin,)))
    other_id = LedgerEntry(replace(entry.position, position_id="second"), entry.fill, closes=False)
    with pytest.raises(AssertionError, match="one scheduled road decision"):
        h.check_no_duplicate_fills(h.with_ledger(rig, (other_id,)))


# --- criterion 2: the comparator


def test_two_runs_of_one_recorded_day_are_byte_identical_and_a_rerun_seals_nothing_new():
    files = h.check_replay_twice(fake_rig, CLEAN)
    assert set(files) == {"decisions.jsonl.gz", "counts.json"}


def test_the_comparator_fails_on_one_changed_byte_in_a_record_file_or_the_counts_file():
    rig, _ = clean_run()
    files = h.files_of(rig, CLEAN.session)
    assert h.differences(files, dict(files)) == []
    flipped = {**files, "counts.json": files["counts.json"][:-1] + b"X"}
    assert h.differences(files, flipped) == ["counts.json"]
    data = bytearray(files["decisions.jsonl.gz"])
    data[len(data) // 2] ^= 1
    assert h.differences(files, {**files, "decisions.jsonl.gz": bytes(data)}) == ["decisions.jsonl.gz"]
    assert h.differences(files, {"counts.json": files["counts.json"]}) == ["decisions.jsonl.gz"]


def test_a_changed_record_changes_the_files_the_comparator_reads():
    first, _ = clean_run()
    other = fake_rig(replace(CLEAN, drivers=CLEAN.drivers[:2]))  # N0 left out: one record fewer a road
    other.fleet.run(CLEAN.session, RunMode.REPLAY)
    assert h.differences(h.files_of(first, CLEAN.session), h.files_of(other, CLEAN.session)) != []


def test_the_files_are_the_dashcam_s_own_bytes():
    rig, run = clean_run()
    assert h.files_of(rig, CLEAN.session)["decisions.jsonl.gz"] == encode_slot_file(run.decisions)


# --- criterion 3: the planted refusal survives two runs and reaches sections and counts


def test_the_planted_refusal_survives_two_runs_and_is_in_both_sections_inputs_and_every_denominator():
    fault = refused_entry(ROAD)
    scenario = fault.plant(CLEAN)
    key = (ROAD, fault.driver_id)
    first, second = fake_rig(scenario), fake_rig(scenario)
    runs = [first.fleet.run(scenario.session, RunMode.REPLAY), second.fleet.run(scenario.session, RunMode.REPLAY)]
    runs.append(first.fleet.run(scenario.session, RunMode.REPLAY))  # a rerun in the same world
    for rig, run in ((first, runs[0]), (second, runs[1]), (first, runs[2])):
        refused = {(r.road, r.decision.driver_id): r for r in run.decisions}[key].decision
        assert (refused.outcome, refused.reason) == (Outcome.REFUSED, RefusalReason.MAX_LOSS)
        assert refused.proposal.max_loss > CAP_RS, "the refused proposal is kept, so the refusal can be explained"
        for section in ("today", "evening"):
            inputs = rig.section_inputs(scenario.session, section)
            assert key in {(r.road, r.decision.driver_id) for r in inputs}
        assert key in rig.denominator(scenario.session) and rig.denominator(scenario.session) == scenario.scheduled
        assert key not in {(e.position.road, e.position.driver_id) for e in rig.ledger()}
    assert h.differences(h.files_of(first, scenario.session), h.files_of(second, scenario.session)) == []


def test_the_refusal_is_in_the_counts_file_as_not_executed():
    fault = refused_entry(ROAD)
    rig = fake_rig(fault.plant(CLEAN))
    rig.fleet.run(CLEAN.session, RunMode.REPLAY)
    rows = [row for row in json.loads(rig.count_file(CLEAN.session)) if row["driver"] == fault.driver_id]
    assert len(rows) == 5 and {(r["outcome"], r["executed"]) for r in rows} == {("refused", 0)}


def test_every_fault_leaves_every_scheduled_decision_sealed():
    for fault in all_faults(ROAD):
        scenario = fault.plant(CLEAN)
        rig = fake_rig(scenario)
        run = rig.fleet.run(scenario.session, RunMode.REPLAY)
        assert {(r.road, r.decision.driver_id) for r in run.decisions} == scenario.scheduled, fault.name
        assert rig.dashcam.find(scenario.session, SLOT_1500, RecordKind.DECISIONS) is not None


def test_the_harness_builds_only_on_the_contracts():
    entry = b.opening()
    assert isinstance(entry, LedgerEntry) and isinstance(entry.position, OpenPosition)
    assert isinstance(entry.fill, FillResult) and isinstance(entry.fill.legs[0], FilledLeg)


def test_a_dashcam_that_overwrites_a_sealed_file_before_raising_fails_the_replay_conflict_check():
    class Overwriting(FakeDashcam):
        def seal(self, session, slot, kind, records):
            if (session, slot, kind) not in self.files:
                return super().seal(session, slot, kind, records)
            self.files[(session, slot, kind)] = encode_slot_file(records)  # overwrites, then still complains
            raise ReplayConflict("after overwriting")

    scenario = replay_conflict().plant(CLEAN)
    rig = fake_rig(scenario)
    bad = replace(rig, dashcam=Overwriting(pushed_at=scenario.seal_pushed_at))
    bad = replace(bad, fleet=replace(rig.fleet, dashcam=bad.dashcam))
    run = bad.fleet.run(scenario.session, RunMode.REPLAY)
    with pytest.raises((AssertionError, Failed, StaleSeal)):  # the changed file no longer matches its seal
        h.verify_fault(replay_conflict(), bad, run, run)


def test_the_counts_file_marks_executed_entries():
    rig, _ = clean_run()
    rows = json.loads(rig.count_file(CLEAN.session))
    assert sum(row["executed"] for row in rows) == 10 and len(rows) == 15
    assert {row["driver"] for row in rows if row["executed"]} == {"CS1@1", "DR1@1"}
