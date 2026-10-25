"""Receipts by observation at the deadline (story F1t criterion 5): a commit counts at the first valid reading of the
remote that contains it; a failed, late or early reading proves nothing; a commit's own date is never used."""

from datetime import datetime, timedelta

import pytest

from fno.ai.observed_receipts import GRACE, Observation, ObservationFile, ObservedPushes
from fno.ai.receipts import ReceiptUnknown
from fno.models import IST

FIRST = datetime(2026, 10, 19, 15, 10, tzinfo=IST)
SECOND = datetime(2026, 10, 19, 15, 11, tzinfo=IST)


class Chain:
    """Ancestry over a straight history: each commit name contains every earlier one."""

    def __init__(self, *order: str):
        self.order = list(order)

    def is_ancestor(self, older: str, newer: str) -> bool:
        return older in self.order and newer in self.order and self.order.index(older) <= self.order.index(newer)


def reading(deadline, commit, late=0.4, error=""):
    started = deadline + timedelta(seconds=late)
    return Observation(deadline, started, started + timedelta(seconds=1), commit, error)


def test_a_commit_on_the_remote_at_the_first_reading_is_received_at_that_deadline():
    pushes = ObservedPushes([reading(FIRST, "b"), reading(SECOND, "c")], Chain("a", "b", "c"))
    assert pushes.received_at("a") == FIRST
    assert pushes.received_at("b") == FIRST


def test_a_commit_pushed_after_the_first_reading_is_received_at_the_second():
    pushes = ObservedPushes([reading(FIRST, "b"), reading(SECOND, "c")], Chain("a", "b", "c"))
    assert pushes.received_at("c") == SECOND


def test_a_commit_in_no_reading_is_unknown():
    pushes = ObservedPushes([reading(FIRST, "b"), reading(SECOND, "c")], Chain("a", "b", "c", "d"))
    with pytest.raises(ReceiptUnknown, match="not on the remote"):
        pushes.received_at("d")


@pytest.mark.parametrize("late, valid", [(0, True), (GRACE.total_seconds(), True), (GRACE.total_seconds() + 1, False)])
def test_a_reading_started_more_than_the_grace_after_its_deadline_proves_nothing(late, valid):
    pushes = ObservedPushes([reading(FIRST, "b", late=late)], Chain("a", "b"))
    if valid:
        assert pushes.received_at("a") == FIRST
    else:
        with pytest.raises(ReceiptUnknown, match="started 31 s after"):
            pushes.received_at("a")


def test_a_reading_started_before_its_deadline_proves_nothing():
    pushes = ObservedPushes([reading(FIRST, "b", late=-1)], Chain("a", "b"))
    with pytest.raises(ReceiptUnknown, match="started before"):
        pushes.received_at("a")


def test_a_failed_reading_is_skipped_and_a_later_valid_one_still_counts():
    pushes = ObservedPushes([reading(FIRST, None, error="timeout"), reading(SECOND, "b")], Chain("a", "b"))
    assert pushes.received_at("a") == SECOND
    assert pushes.valid_at(FIRST) is None
    assert pushes.valid_at(SECOND).commit == "b"


def test_no_reading_at_all_is_unknown():
    with pytest.raises(ReceiptUnknown, match="none was taken"):
        ObservedPushes([], Chain("a")).received_at("a")


def test_the_observation_file_keeps_every_reading_in_order(tmp_path):
    out = ObservationFile(tmp_path / "obs" / "day.json")
    assert out.read() == []
    out.append(reading(FIRST, "b"))
    out.append(reading(SECOND, None, error="refused"))
    assert [(o.deadline, o.commit, o.error) for o in out.read()] == [(FIRST, "b", ""), (SECOND, None, "refused")]
