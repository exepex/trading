"""Criteria 1 and 3 (story MS-P0b): the study pace's gap, and what each answer means."""

import pytest

from fno.school.probes.answers import RawAnswer, Verdict, judge
from fno.school.probes.pace import StudyPace


class Clock:
    def __init__(self):
        self.now, self.slept = 0.0, []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


@pytest.mark.parametrize("gap", [1.0, 3.0])
def test_a_start_never_comes_sooner_than_the_gap(gap):
    clock = Clock()
    pace = StudyPace(gap, clock, clock.sleep)
    starts = []
    for _ in range(4):
        pace.wait_turn()
        starts.append(clock.now)
        clock.now += 0.1  # the request itself
    assert [round(b - a, 9) for a, b in zip(starts, starts[1:])] == [gap] * 3


def test_the_first_request_and_one_exactly_at_the_gap_do_not_wait():
    clock = Clock()
    pace = StudyPace(1.0, clock, clock.sleep)
    pace.wait_turn()
    clock.now = 1.0
    pace.wait_turn()
    assert clock.slept == []


def test_a_late_request_waits_nothing_and_resets_the_gap():
    clock = Clock()
    pace = StudyPace(3.0, clock, clock.sleep)
    pace.wait_turn()
    clock.now = 10.0
    pace.wait_turn()
    clock.now = 11.0
    pace.wait_turn()
    assert clock.slept == [2.0]


@pytest.mark.parametrize(
    ("answer", "first_429_stops", "verdict"),
    [
        (RawAnswer(status=429), True, Verdict.STOP),
        (RawAnswer(rate_limited=True), True, Verdict.STOP),
        (RawAnswer(status=429), False, Verdict.RETRY_RATE),
        (RawAnswer(status=401), False, Verdict.STOP),
        (RawAnswer(status=403), False, Verdict.STOP),
        (RawAnswer(status=404), False, Verdict.STOP),
        (RawAnswer(status=418), True, Verdict.STOP),
        (RawAnswer(status=500), False, Verdict.RETRY_SERVER),
        (RawAnswer(status=503), True, Verdict.RETRY_SERVER),
        (RawAnswer(timed_out=True), True, Verdict.RETRY_SERVER),
        (RawAnswer(error_name="SomethingNew"), True, Verdict.STOP),
        (RawAnswer(status=200, payload={}, shape_ok=False), False, Verdict.STOP),
        (RawAnswer(status=200), False, Verdict.STOP),
        (RawAnswer(status=200, payload={"stocks": []}, shape_ok=True), False, Verdict.OK),
        (RawAnswer(payload={"strikes": {"1": {}}}, shape_ok=True), True, Verdict.OK),
    ],
)
def test_each_answer_has_one_verdict(answer, first_429_stops, verdict):
    assert judge(answer, first_429_stops)[0] is verdict


def test_a_stop_reason_names_the_status_or_class_only():
    assert judge(RawAnswer(status=401), False)[1] == "HTTP 401"
    assert judge(RawAnswer(status=200), False)[1] == "answer is not the expected JSON"
    assert judge(RawAnswer(error_name="GrowwSignInPaused"), True)[1] == "GrowwSignInPaused"
