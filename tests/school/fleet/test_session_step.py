"""Story MS-P1j with MS-INS part e: the step after the session's outcomes (the instructor's run) sees the sealed
outcomes before the counts are written, can never stop the school's record, and runs again on a rerun."""

import time

from fno.school.constants import SLOT_1500, RecordKind
from fno.school.contracts.fleet import RunMode
from fno.school.dashcam.names import counts_path
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.session_hook import IsolatedSessionStep
from tests.school.contracts import builders as b
from tests.school.fleet.rig import Rig, all_roads

LAWS = (FakeMaxLossLaw(10_000),)


def rig_with(tmp_path, step) -> Rig:
    rig = Rig(tmp_path, (FakeDriver(all_roads("CS1"), b.put_spread()),), LAWS)
    rig.fleet.after_outcomes = step
    return rig


def test_the_step_runs_once_the_outcomes_are_sealed_and_before_the_counts_are_written(tmp_path):
    seen = []

    def step(session):
        seen.append((rig.dashcam.find(session, SLOT_1500, RecordKind.OUTCOMES) is not None,
                     (tmp_path / counts_path(session, SLOT_1500)).is_file()))  # fmt: skip

    rig = rig_with(tmp_path, step)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert seen == [(True, False)]


def test_a_failing_or_slow_step_alerts_once_by_class_and_the_counts_are_still_written(tmp_path):
    def broken(session):
        raise KeyError("ContractKey(strike=51200)")

    def slow(session):
        time.sleep(0.3)

    for name, work in (("broken", broken), ("slow", slow)):
        alerts = []
        root = tmp_path / name
        rig = rig_with(root, IsolatedSessionStep("instructor", work, alerts.append, seconds=0.1))
        rig.fleet.run(b.SESSION, RunMode.REPLAY)
        assert (root / counts_path(b.SESSION, SLOT_1500)).is_file(), "the school's counts never wait on the step"
        assert len(alerts) == 1 and "instructor not run" in alerts[0] and "51200" not in alerts[0]
        assert ("KeyError" if name == "broken" else "time limit") in alerts[0]


def test_a_rerun_of_a_complete_session_runs_the_step_again_before_committing(tmp_path):
    calls = []
    rig = rig_with(tmp_path, calls.append)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert calls == [b.SESSION, b.SESSION]
