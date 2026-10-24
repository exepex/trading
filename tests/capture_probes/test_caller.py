"""Criteria 2, 3 and 5 (story MS-P0b) at the caller: the reservation, the refusal rules and the hard stop."""

from datetime import date, datetime, timedelta

import pytest

from fno.capture_probes.answers import RawAnswer
from fno.capture_probes.caller import PacedCaller, SourceStopped
from fno.capture_probes.dry_run import JumpingClock
from fno.capture_probes.pace import StudyPace
from fno.models import IST

OK = RawAnswer(status=200, payload={}, shape_ok=True)


def caller(clock, allowed=10, minutes=6, first_429_stops=False, cap_reason="", earlier_429s=0):
    deadline = clock.wall() + timedelta(minutes=minutes)
    return PacedCaller(StudyPace(1.0, clock.timer, clock.sleep), allowed, deadline, clock.wall, clock.timer,
                       clock.sleep, first_429_stops, earlier_429s, cap_reason)  # fmt: skip


def answers(*sequence):
    queue, sent = list(sequence), []

    def request():
        sent.append(1)
        return queue.pop(0)

    return request, sent


@pytest.fixture
def clock():
    return JumpingClock(date(2026, 10, 29))


def test_the_request_after_the_reservation_is_never_sent(clock):
    call = caller(clock, allowed=2)
    request, sent = answers(OK, OK, OK)
    assert call.call("future", request) and call.call("future", request)
    assert call.call("future", request) is None
    assert len(sent) == 2


def test_a_reservation_cut_by_the_cap_stops_with_the_cap_line(clock):
    call = caller(clock, allowed=1, cap_reason="daily cap reached (240 requests)")
    request, sent = answers(OK, OK)
    call.call("future", request)
    with pytest.raises(SourceStopped, match="daily cap"):
        call.call("future", request)
    assert len(sent) == 1


def test_an_empty_reservation_sends_nothing(clock):
    call = caller(clock, allowed=0, cap_reason="daily cap reached (50 requests)")
    request, sent = answers(OK)
    with pytest.raises(SourceStopped):
        call.call("page", request)
    assert sent == []


def test_groww_stops_at_its_first_429_with_one_request_sent(clock):
    call = caller(clock, first_429_stops=True)
    request, sent = answers(RawAnswer(rate_limited=True), OK)
    with pytest.raises(SourceStopped, match="429"):
        call.call("future", request)
    assert len(sent) == 1


def test_nse_waits_60_s_after_a_429_and_retries_once(clock):
    call = caller(clock)
    request, sent = answers(RawAnswer(status=429), OK)
    before = clock.wall()
    assert call.call("future", request) is OK
    assert len(sent) == 2 and clock.wall() - before >= timedelta(seconds=60)


def test_a_second_429_the_same_day_stops_nse(clock):
    call = caller(clock, earlier_429s=1)
    request, sent = answers(RawAnswer(status=429), OK)
    with pytest.raises(SourceStopped, match="second HTTP 429"):
        call.call("future", request)
    assert len(sent) == 1


@pytest.mark.parametrize("code", [401, 403, 404])
def test_any_other_4xx_stops_at_once(clock, code):
    call = caller(clock)
    request, sent = answers(RawAnswer(status=code), OK)
    with pytest.raises(SourceStopped, match=f"HTTP {code}"):
        call.call("future", request)
    assert len(sent) == 1


def test_a_server_error_is_retried_once_after_30_s_then_the_row_is_missing(clock):
    call = caller(clock)
    request, sent = answers(RawAnswer(status=502), RawAnswer(status=502), OK)
    before = clock.wall()
    assert call.call("chain", request) is None
    assert len(sent) == 2 and clock.wall() - before >= timedelta(seconds=30)


def test_nothing_is_sent_at_or_after_the_hard_stop(clock):
    call = caller(clock, minutes=0)
    request, sent = answers(OK)
    assert call.call("future", request) is None and sent == []


def test_a_wait_that_would_pass_the_hard_stop_ends_the_slot_without_an_early_retry(clock):
    call = caller(clock, minutes=1)  # 60 s left: the 429's 60 s wait does not fit
    request, sent = answers(RawAnswer(status=429), OK)
    assert call.call("future", request) is None
    assert len(sent) == 1


def test_latency_is_kept_per_kind(clock):
    call = caller(clock)

    def slow():
        clock.sleep(0.4)
        return OK

    call.call("chain", slow)
    assert call.latency_ms() == {"chain_median": 400.0, "chain_p95": 400.0}
    assert isinstance(clock.wall(), datetime) and clock.wall().tzinfo == IST
