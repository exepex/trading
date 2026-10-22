"""Part a's frozen types (story MS-INS): each refuses a record that could not be true, and every record reads back to
identical bytes."""

import dataclasses
import hashlib

import pytest

from fno.school.constants import RoadCode
from fno.school.instructor.contracts import (
    Attribution,
    Cause,
    HeldPath,
    MapStatus,
    Measure,
    PairedRow,
)
from fno.school.instructor.records_file import decode_instructor_file, encode_instructor_file
from tests.school.instructor.builders import RULES, SESSIONS, attribution, classification, outcome, snap


def paired(**changes) -> PairedRow:
    values = dict(
        driver_id="CS1@1",
        control_id="N0@1",
        measure=Measure.PER_OPPORTUNITY,
        first=None,
        last=None,
        sessions=0,
        road_slots=0,
        driver_abstentions=0,
        control_abstentions=0,
        unavailable=0,
        after_cut=0,
        mean=None,
        low=None,
        high=None,
        block=5,
        status=MapStatus.EXPLORATORY,
        rules_sha256=RULES,
    )
    return PairedRow(**{**values, **changes})


def test_map_status_has_exactly_the_three_statuses_327_allows():
    assert {s.value for s in MapStatus} == {"exploratory", "watching", "not_established"}


def test_the_causes_are_325s_thirteen():
    assert len(Cause) == 13


@pytest.mark.parametrize("build", [attribution, classification, paired])
def test_every_type_is_frozen(build):
    with pytest.raises(dataclasses.FrozenInstanceError):
        build().driver_id = "x"


def test_an_attribution_must_add_up_to_its_net_within_a_paisa():
    assert attribution(residual=0.01).residual == 0.01  # boundary: one paisa is the tolerance
    with pytest.raises(ValueError, match="add up"):
        attribution(residual=0.02)


def test_a_nan_attribution_is_refused():
    with pytest.raises(ValueError, match="add up"):
        attribution(delta=float("nan"), net=float("nan"))


def test_an_attribution_names_its_rules_and_counts_nothing_negative():
    with pytest.raises(ValueError):
        attribution(rules_sha256="")
    with pytest.raises(ValueError):
        attribution(steps_merged=-1)


def test_a_classification_takes_at_most_two_secondary_causes():
    three = (Cause.COSTS_ATE_EDGE, Cause.NORMAL_NOISE, Cause.TIME_DECAY)
    assert len(classification(secondary=three[:2]).secondary) == 2
    with pytest.raises(ValueError, match="two secondary"):
        classification(secondary=three)


def test_unclassified_has_no_secondary_and_a_cause_appears_once():
    assert classification(primary=None, secondary=()).causes == ()
    with pytest.raises(ValueError):
        classification(primary=None)
    with pytest.raises(ValueError):
        classification(secondary=(Cause.WRONG_DIRECTION,))
    with pytest.raises(ValueError):
        classification(not_testable=(Cause.COSTS_ATE_EDGE,))


@pytest.mark.parametrize("cause", [Cause.GAP_THROUGH_STOP, Cause.COSTS_ATE_EDGE])
def test_a_winner_never_carries_a_loser_only_cause(cause):
    assert classification(net=-0.01, primary=cause, secondary=()).winner is False
    with pytest.raises(ValueError, match="winner form"):
        classification(net=0.0, primary=cause, secondary=())  # boundary: a flat result reads as a winner


def test_a_paired_row_has_a_mean_exactly_with_sessions_and_an_interval_around_it():
    assert paired().mean is None
    some = dict(sessions=3, first=SESSIONS[0], last=SESSIONS[2])
    assert paired(**some, mean=0.1, low=-0.2, high=0.3).status == MapStatus.EXPLORATORY
    assert paired(**some, mean=0.1).low is None  # an interval is optional (too few sessions to resample)
    for bad in (dict(some), dict(some, mean=0.1, low=0.3, high=-0.2), dict(some, mean=0.1, low=-0.2),
                dict(some, mean=float("nan")), dict(some, mean=0.1, low=float("nan"), high=0.3),
                dict(some, mean=0.1, first=SESSIONS[2], last=SESSIONS[0]), dict(some, mean=0.1, last=None),
                dict(block=0), dict(low=0.0, high=0.0)):  # fmt: skip
        with pytest.raises(ValueError):
            paired(**bad)


def test_records_round_trip_to_identical_bytes_and_a_changed_field_changes_them():
    one = dict(sessions=1, first=SESSIONS[0], last=SESSIONS[0], mean=0.0, low=0.0, high=0.0)
    records = (attribution(), classification(), paired(**one))
    data = encode_instructor_file(records)
    assert decode_instructor_file(data) == records and encode_instructor_file(decode_instructor_file(data)) == data
    assert encode_instructor_file((attribution(theta=76.0, residual=-1.0),) + records[1:]) != data


def test_an_empty_file_round_trips_and_a_foreign_record_is_refused():
    assert decode_instructor_file(encode_instructor_file(())) == ()
    with pytest.raises(TypeError):
        encode_instructor_file((Attribution,))  # a class, not a record


def test_a_held_path_takes_only_its_own_roads_snapshots_in_session_order():
    record = outcome("cd" * 32)
    assert HeldPath(record, None, None, (snap(SESSIONS[0]), snap(SESSIONS[1])), None, 0, ()).attributable
    with pytest.raises(ValueError, match="own road"):
        HeldPath(
            record, None, None, (dataclasses.replace(snap(SESSIONS[0]), road=RoadCode.NIFTY_MONTHLY),), None, 0, ()
        )
    with pytest.raises(ValueError, match="session order"):
        HeldPath(record, None, None, (snap(SESSIONS[1]), snap(SESSIONS[0])), None, 0, ())


def test_the_school_import_boundary_covers_the_instructor():
    """Criterion 6: the school's import test (no order call, Slack or Groww SDK) walks every instructor module."""
    from tests.school.contracts.test_boundaries import FILES

    names = {p.name for p in FILES if "instructor" in p.parts}
    assert {"reader.py", "adapters.py", "wiring.py", "contracts.py"} <= names


def test_an_instructor_file_has_pinned_bytes_so_a_rerun_writes_the_same_file():
    data = encode_instructor_file((attribution(),))
    assert data[4:8] == b"\0\0\0\0" and data[3] & 0x08 == 0  # gzip time zero and no file name
    assert hashlib.sha256(encode_instructor_file((attribution(),))).hexdigest() == hashlib.sha256(data).hexdigest()
