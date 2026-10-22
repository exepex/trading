"""Only verified recorded captures feed the model (MS-SIM-b, 7.4 test 4)."""

from fno.school.constants import RoadCode
from fno.school.roads.capture import CaptureReader
from fno.school.simulator.spreads.learner import SpreadLearner
from fno.school.simulator.spreads.recorded import Skipped, recorded_snapshots
from tests.school.roads.capture_builder import SESSION, DictStore, Plant, road

BANK = road(RoadCode.BANKNIFTY_MONTHLY)


def read(plants: list[Plant], sessions):
    store = DictStore()
    for plant in plants:
        plant.write(store)
    skipped = Skipped()
    found = list(recorded_snapshots(CaptureReader({BANK.dataset: store}), [BANK], sessions, skipped))
    return found, skipped


def test_a_good_capture_becomes_a_snapshot_and_feeds_the_learner():
    found, skipped = read([Plant(BANK)], [SESSION])
    assert len(found) == 1 and not skipped.reasons
    assert SpreadLearner().learn(found).by_session


def test_a_tampered_capture_is_skipped_with_its_reason_and_never_repaired():
    found, skipped = read([Plant(BANK, tamper=True)], [SESSION])
    assert found == [] and skipped.reasons == [(RoadCode.BANKNIFTY_MONTHLY, SESSION, "hash_mismatch")]


def test_a_missing_capture_and_an_incomplete_one_are_skipped():
    other = SESSION.replace(day=4)
    found, skipped = read([Plant(BANK, other, complete=False)], [SESSION, other])
    assert found == [] and [r[2] for r in skipped.reasons] == ["capture_missing", "capture_incomplete"]


def test_no_sessions_is_empty():
    found, skipped = read([], [])
    assert found == [] and not skipped.reasons
