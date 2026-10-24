"""Story MS-P1j acceptance test 4: MS-P1i's harness on the real fleet (`real_rig`): every planted fault gives its exact
reason, the four fill checks hold, and one recorded session run twice gives identical records."""

import pytest

from fno.school.acceptance.faults import all_faults
from fno.school.accounts.school_accounts import SchoolAccounts
from fno.school.constants import RoadCode
from fno.school.contracts.fleet import RunMode
from tests.school.acceptance import harness as h
from tests.school.acceptance.real_rig import real_rig_builder
from tests.school.acceptance.recorded_day import recorded_day

WAITING = "needs MS-P1d's SchoolAccounts.entries (a3's LedgerReader), not on main yet"
pytestmark = pytest.mark.skipif(not hasattr(SchoolAccounts, "entries"), reason=WAITING)
ROAD = RoadCode.BANKNIFTY_MONTHLY
CLEAN = recorded_day()


def test_the_clean_recorded_day_passes_every_fill_check_on_the_real_fleet(tmp_path):
    rig = real_rig_builder(tmp_path)(CLEAN)
    run = rig.fleet.run(CLEAN.session, RunMode.REPLAY)
    assert {(r.road, r.decision.driver_id) for r in run.decisions} == CLEAN.scheduled
    h.check_fills(rig, run)
    assert rig.ledger(), "the clean day opened positions"
    assert rig.denominator(CLEAN.session) == CLEAN.scheduled


@pytest.mark.parametrize("fault", all_faults(ROAD), ids=lambda f: f.name)
def test_each_planted_fault_gives_its_exact_reason_on_the_real_fleet(fault, tmp_path):
    h.run_fault(fault, real_rig_builder(tmp_path), CLEAN)


def test_one_recorded_session_replayed_twice_gives_identical_records(tmp_path):
    files = h.check_replay_twice(real_rig_builder(tmp_path), CLEAN)
    assert "decisions.jsonl.gz" in files and files["counts.json"]
