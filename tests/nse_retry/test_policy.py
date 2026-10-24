"""Story A9b, criteria 1, 2 and 4: one retry policy for every NSE source class, GET and HEAD alike; a success is
unchanged; nothing but `RawSourceUnavailable` (or its `RawFileRefused`) leaves a source."""

from datetime import UTC, datetime
from email.utils import format_datetime

import pytest
import requests

from fno.http_pacing import PacedSession, RequestPacer, SourceCoolingOff
from fno.storage.raw_source import RawFileRefused, RawSourceCoolingOff, RawSourceUnavailable
from tests.nse_retry.fake_nse import ScriptedNse, a_path, answer, nse_source_classes, source_with

CLASSES = nse_source_classes()
NOW = datetime(2026, 10, 15, 10, 0, tzinfo=UTC)
STAMP = "Wed, 14 Oct 2026 12:30:00 GMT"
DROPPED = requests.ConnectionError("connection reset")


def run(cls, *answers, head=False, now=NOW):
    session, waits = ScriptedNse(*answers), []
    source = source_with(cls, session, waits, now)
    path = a_path(cls)
    result = source.last_written(path) if head else source.fetch_published(path)
    return result, session, waits


def test_every_nse_source_class_is_covered():
    assert len(CLASSES) == 26  # A1, A8, A10, A11, A12, A14, A15, P6, P8 (15 Oct 2026), A20a's two lists, A23's two


@pytest.mark.parametrize("cls", CLASSES, ids=lambda c: c.__qualname__)
@pytest.mark.parametrize("head", [False, True], ids=["GET", "HEAD"])
def test_a_success_is_unchanged_one_request_no_wait(cls, head):
    result, session, waits = run(cls, answer(200, b"bytes", Last_Modified=STAMP), head=head)
    assert len(session.requests) == 1 and waits == []
    assert session.requests[0][0] == ("HEAD" if head else "GET")
    expected = datetime(2026, 10, 14, 12, 30, tzinfo=UTC)
    assert result == expected if head else (result.data, result.last_modified) == (b"bytes", expected)


@pytest.mark.parametrize("cls", CLASSES, ids=lambda c: c.__qualname__)
@pytest.mark.parametrize("head", [False, True], ids=["GET", "HEAD"])
def test_not_published_is_none_after_one_request(cls, head):
    result, session, waits = run(cls, answer(404), head=head)
    assert result is None and len(session.requests) == 1 and waits == []


@pytest.mark.parametrize("cls", CLASSES, ids=lambda c: c.__qualname__)
@pytest.mark.parametrize("head", [False, True], ids=["GET", "HEAD"])
def test_a_server_error_is_retried_and_four_stop_with_a_named_failure(cls, head):
    result, _, waits = run(cls, answer(503), answer(503), answer(200, b"bytes", Last_Modified=STAMP), head=head)
    assert waits == [5, 15] and result is not None
    with pytest.raises(RawSourceUnavailable) as failed:
        run(cls, *[answer(503)] * 4, head=head)
    assert (failed.value.status, failed.value.tries) == (503, 4) and not isinstance(failed.value, RawFileRefused)
    assert str(failed.value).endswith("HTTP 503 after 4 tries") and a_path(cls) in str(failed.value)


@pytest.mark.parametrize("status", [429, 500, 502, 504, 599])
def test_every_retried_status_and_a_dropped_connection(status):
    cls = CLASSES[0]
    assert run(cls, answer(status), answer(200, b"x"))[2] == [5]
    assert run(cls, DROPPED, DROPPED, DROPPED, answer(200, b"x"))[2] == [5, 15, 45]
    with pytest.raises(RawSourceUnavailable, match="connection reset after 4 tries") as failed:
        run(cls, *[DROPPED] * 4)
    assert failed.value.status is None and failed.value.tries == 4


@pytest.mark.parametrize("cls", CLASSES, ids=lambda c: c.__qualname__)
@pytest.mark.parametrize("status", [403, 400, 401, 410, 451, 100, 199, 301, 304, 399, 600, 0])
def test_a_refusal_is_never_retried(cls, status):
    with pytest.raises(RawFileRefused) as refused:
        run(cls, answer(status), answer(200, b"never asked"))
    assert (refused.value.status, refused.value.tries) == (status, 1)
    assert str(refused.value).endswith(f"HTTP {status} after 1 try")


@pytest.mark.parametrize("cls", CLASSES, ids=lambda c: c.__qualname__)
def test_a_host_cooling_off_stops_at_once_without_waiting(cls):
    paused = SourceCoolingOff("nsearchives.nseindia.com refused requests (HTTP 403); not calling it for 15 minutes")
    with pytest.raises(RawSourceUnavailable, match="not calling it for 15 minutes") as stopped:
        run(cls, paused)
    assert isinstance(stopped.value, RawSourceCoolingOff) and stopped.value.tries == 0  # no request was sent


def test_a_second_429_stops_at_once_without_waiting_into_the_pause():
    class Nse429(requests.adapters.BaseAdapter):
        def send(self, request, **kwargs):
            got = answer(429)
            got.request, got.url = request, request.url
            return got

        def close(self):
            pass

    pacer = RequestPacer(spacing={})
    pacer.sleep = lambda seconds: None
    session = PacedSession(pacer)
    session.mount("https://", Nse429())
    waits = []
    with pytest.raises(RawSourceCoolingOff, match="HTTP 429 after 2 tries") as stopped:
        source_with(CLASSES[0], session, waits, NOW).fetch(a_path(CLASSES[0]))
    assert waits == [5] and stopped.value.status == 429  # the pacer paused the host at the second 429
    with pytest.raises(RawSourceCoolingOff, match="not calling it for 15 minutes"):
        source_with(CLASSES[0], session, waits, NOW).fetch(a_path(CLASSES[0]))  # the next file: no request
    assert run(CLASSES[0], answer(429), answer(503), answer(429), answer(200, b"x"))[2] == [5, 15, 45]


@pytest.mark.parametrize(
    ("header", "wait"),
    [
        ("30", 30),  # over the scheduled 5 s
        ("3", 5),  # under it: the scheduled wait
        ("120", 120),  # at the cap
        (format_datetime(datetime(2026, 10, 15, 10, 1, tzinfo=UTC), usegmt=True), 60),  # an HTTP date
        ("soon", 5),  # malformed: ignored
        (format_datetime(datetime(2026, 10, 15, 9, 0, tzinfo=UTC), usegmt=True), 5),  # past: ignored
        ("", 5),  # empty: ignored
    ],
)
def test_retry_after_stretches_the_wait_up_to_the_cap(header, wait):
    assert run(CLASSES[0], answer(429, Retry_After=header), answer(200, b"x"))[2] == [wait]


def test_a_retry_after_over_the_cap_stops_at_once():
    with pytest.raises(RawSourceUnavailable) as stopped:
        run(CLASSES[0], answer(503, Retry_After="121"), answer(200, b"never asked"))
    assert str(stopped.value).endswith("HTTP 503 (Retry-After 121) after 1 try") and stopped.value.tries == 1


def test_an_empty_success_is_returned_as_is_for_the_dataset_check():
    result, session, waits = run(CLASSES[0], answer(200, b""))
    assert result.data == b"" and len(session.requests) == 1 and waits == []


def test_a_retry_after_that_only_looks_numeric_is_ignored():
    assert run(CLASSES[0], answer(503, Retry_After="\u00b2"), answer(200, b"x"))[2] == [5]


def test_a_request_that_cannot_be_built_is_not_retried():
    with pytest.raises(RawSourceUnavailable, match=r"\(not sent\)") as failed:
        run(CLASSES[0], requests.exceptions.InvalidURL("bad url"), answer(200, b"never asked"))
    assert failed.value.tries == 1


@pytest.mark.parametrize(
    ("stamp", "expected"),
    [("garbage", None), ("Wed, 14 Oct 2026 12:30:00 -0000", datetime(2026, 10, 14, 12, 30, tzinfo=UTC))],
)
def test_an_unreadable_or_zoneless_last_modified_never_raises(stamp, expected):
    for head in (False, True):
        result = run(CLASSES[0], answer(200, b"x", Last_Modified=stamp), head=head)[0]
        assert (result if head else result.last_modified) == expected
