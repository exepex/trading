"""REC1b section 5 for `school` (judge 641 SF1): complete only when the step is `ok` for a reason other than OFF or
NOT_A_SESSION and the session's decisions file is sealed and reads with its hash checked; school off read as
complete is the plant this story names."""

from datetime import datetime

import pytest

from fno.daily.reason_codes import STEP_TEMPLATES
from fno.desk.run_log import RunLog
from fno.recommend.constants import SourceState
from fno.recommend.ports import InputFailed
from fno.recommend.school_source import NOT_RUN, SchoolSource
from fno.school.constants import SLOT_1500, Outcome, RecordKind
from fno.school.fakes import FakeDashcam
from tests.school.instructor.builders import SESSIONS, decision_record

DAY = SESSIONS[0]


def log_school(root, result: dict | None):
    if result is not None:
        now = datetime.now().astimezone()
        RunLog.open(root, DAY).record("school", now, now, {}, result)


def sealed(*records) -> FakeDashcam:
    dashcam = FakeDashcam()
    dashcam.seal(DAY, SLOT_1500, RecordKind.DECISIONS, records)
    return dashcam


def test_a_school_that_ran_and_sealed_its_decisions_is_complete(tmp_path):
    log_school(tmp_path, {"status": "ok", "reason": "command:ok"})
    dashcam = sealed(decision_record(DAY), decision_record(DAY, "REF@1", Outcome.NO_TRADE))
    reading = SchoolSource(tmp_path, dashcam).read(DAY)
    assert reading.source.state is SourceState.COMPLETE
    assert [(d.version, d.traded) for d in reading.decisions] == [("school:CS1@1", True), ("school:REF@1", False)]
    assert all(d.decision.path.endswith("#BANKNIFTY-M") for d in reading.decisions)
    assert reading.used[0].sha256 == dashcam.find(DAY, SLOT_1500, RecordKind.DECISIONS).sha256


@pytest.mark.parametrize(("result", "status"), [
    ({"status": "ok", "reason": "school:OFF"}, "ok, school:OFF"),  # today: the switch is off, the step exits 0
    ({"status": "ok", "reason": "school:NOT_A_SESSION"}, "ok, school:NOT_A_SESSION"),
    ({"status": "refused", "reason": "school:TOO_LATE"}, "refused, school:TOO_LATE"),
    ({"status": "failed", "reason": "school:STOPPED"}, "failed, school:STOPPED"),
    ({"status": "not_built", "reason": "rehearsal:NOT_BUILT"}, "not_built, rehearsal:NOT_BUILT"),
    ({"status": "exercised", "reason": "rehearsal:EXERCISED"}, "exercised, rehearsal:EXERCISED"),
    (None, "missing, the school step is not in the run log"),
])  # fmt: skip
def test_school_off_or_not_run_is_never_complete(tmp_path, result, status):
    """The named plant: with sealed decisions present, an `ok` school:OFF must still read unavailable."""
    log_school(tmp_path, result)
    reading = SchoolSource(tmp_path, sealed(decision_record(DAY))).read(DAY)
    assert (reading.source.state, reading.source.step_status, reading.decisions) == (SourceState.UNAVAILABLE,
                                                                                     status, ())  # fmt: skip


def test_an_ok_run_with_no_sealed_decisions_is_an_input_failure(tmp_path):
    log_school(tmp_path, {"status": "ok", "reason": "command:ok"})
    with pytest.raises(InputFailed, match="no decisions file is sealed"):
        SchoolSource(tmp_path, FakeDashcam()).read(DAY)


def test_a_sealed_file_whose_hash_does_not_match_is_an_input_failure(tmp_path):
    log_school(tmp_path, {"status": "ok", "reason": "command:ok"})
    dashcam = sealed(decision_record(DAY))
    dashcam.files[(DAY, SLOT_1500, RecordKind.DECISIONS)] += b"x"  # the file changed after its seal
    seal = dashcam.find(DAY, SLOT_1500, RecordKind.DECISIONS)
    dashcam.find = lambda *_: seal.__class__(seal.path, "0" * 64, seal.pushed_at, seal.commit)
    with pytest.raises(InputFailed):
        SchoolSource(tmp_path, dashcam).read(DAY)


def test_the_not_run_reasons_are_the_school_step_s_own_codes():
    codes = {code for code, _ in STEP_TEMPLATES["school"]}
    assert codes >= NOT_RUN


def test_an_unreadable_seal_is_an_input_failure_never_fewer_decisions(tmp_path):
    log_school(tmp_path, {"status": "ok", "reason": "command:ok"})
    dashcam = sealed(decision_record(DAY))

    def unreadable(seal):
        raise OSError("drive down")

    dashcam.read = unreadable
    with pytest.raises(InputFailed, match="OSError"):
        SchoolSource(tmp_path, dashcam).read(DAY)
