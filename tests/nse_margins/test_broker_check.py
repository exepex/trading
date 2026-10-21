"""A14c part 2's broker check on a planted day: market hours, the 14:50 hard stop, pacing, the tolerances at their
boundaries, idempotent reruns, and O1's exit and line rules (a mismatch is a finding with its own line; a failure
exits 1 with the reason last and no own alert)."""

from datetime import date

import pytest

from .broker_fakes import BASKETS, LEVEL, ROWS, MemoryRecord, at, exposure_at, make_check

SF100 = ("SF", 100.0)


@pytest.mark.parametrize(
    ("start", "session"),
    [(at(9, 29, 59), True), (at(16, 0), False)],
    ids=["before 09:30", "closed day"],
)
def test_outside_market_hours_nothing_is_asked(start, session):
    check, broker, record, alerts, printed, _ = make_check(start, session=lambda day: session)
    assert check.run() == 0 and broker.asked == [] and record.written == [] and alerts.sent == []
    assert printed == ["margin check 2026-10-14: outside market hours"]


def test_every_basket_ok_is_recorded_paced_with_the_index_first():
    check, broker, record, alerts, printed, clock = make_check(at(9, 30))
    assert check.run() == 0 and alerts.sent == []
    assert broker.asked[0][0] == "NIFTY" and [key for key, _ in broker.asked[1:]] == list(BASKETS)
    assert clock.slept == [2.0] * len(BASKETS)  # one request every 2 seconds; the first does not wait
    assert [r.status for r in record.written[0]] == ["ok"] * 6
    assert printed[-1].startswith("margin check 2026-10-14: 6 ok, 0 mismatch, 0 error; record data/margins/")


@pytest.mark.parametrize(
    ("span_off", "exposure_share", "status"),
    [
        (1.00, 0.0, "ok"), (0.99, 0.0, "ok"), (1.01, 0.0, "mismatch"), (-1.01, 0.0, "mismatch"),
        (0.0, 0.0010, "ok"), (0.0, 0.00099, "ok"), (0.0, 0.00101, "mismatch"), (0.0, 0.002, "mismatch"),
    ],
    ids=["Rs 1.00", "Rs 0.99", "Rs 1.01", "Rs 1.01 low", "0.10%", "0.099%", "0.101%", "planted 0.2% high"],
)  # fmt: skip
def test_the_tolerances_at_and_around_their_boundaries(span_off, exposure_share, status):
    basket = BASKETS[SF100]
    broker_figures = (basket.span_expected + span_off, exposure_at(basket) * (1 + exposure_share))
    check, broker, record, alerts, printed, _ = make_check(at(10, 0))
    broker.answers[SF100] = broker_figures
    assert check.run() == 0
    assert record.written[0][0].status == status and all(r.status == "ok" for r in record.written[0][1:])
    if status == "mismatch":
        assert (
            len(alerts.sent) == 1
            and alerts.sent[0].startswith("Omenix F&O margin check: Groww and A14 differ beyond tolerance for SF 100 (")
            and alerts.sent[0].endswith(": review the stress factor")
        )
        assert printed[-1] == "alert sent"  # the run log keeps the line (or "alert NOT sent" when Slack is down)
    else:
        assert alerts.sent == []


def test_exposure_is_recomputed_at_the_live_level_never_implied_from_groww():
    """A correct exposure at the file's close (20,000) is wrong at the live 20,050 the broker charges on."""
    basket = BASKETS[SF100]
    check, broker, record, *_ = make_check(at(10, 0))
    broker.answers[SF100] = (basket.span_expected, exposure_at(basket, 20_000.0))
    check.run()
    found = record.written[0][0]
    assert found.status == "mismatch" and found.exposure_expected == pytest.approx(exposure_at(basket, LEVEL))
    assert f"at NIFTY {LEVEL:.2f}" in found.detail


@pytest.mark.parametrize(
    ("start", "asked"),
    [(at(14, 49, 59), 1), (at(14, 50), 0), (at(14, 50, 1), 0), (at(14, 49, 55), 3)],
    ids=["14:49:59", "14:50:00", "14:50:01", "14:49:55"],
)
def test_no_request_starts_at_or_after_14_50_and_the_rest_are_errors(start, asked):
    """At 14:49:59 only the index is asked; the first basket would start at 14:50:01. From 14:49:55: 55, 57, 59."""
    check, broker, record, alerts, printed, _ = make_check(start)
    assert check.run() == 1 and len(broker.asked) == asked and alerts.sent == []
    assert all(when.time().isoformat() < "14:50:00" for _, when in broker.asked)
    statuses = [(r.status, r.detail) for r in record.written[0]]
    assert statuses[max(0, asked - 1) :] == [("error", "deadline")] * (6 - max(0, asked - 1))
    assert "not checked (deadline)" in printed[-1] and "else today's broker figure is lost" in printed[-1]


def test_a_rerun_asks_only_what_is_not_done_and_a_done_day_asks_nothing():
    check, broker, record, *_ = make_check(at(11, 0), record=MemoryRecord(done=set(BASKETS) - {SF100}))
    assert check.run() == 0 and [key for key, _ in broker.asked[1:]] == [SF100]
    check, broker, record, _, printed, _ = make_check(at(11, 0), record=MemoryRecord(done=set(BASKETS)))
    assert check.run() == 0 and broker.asked == [] and record.written == []
    assert printed == ["margin check 2026-10-14: nothing to check (6 baskets already checked)"]


def test_no_a14_row_for_the_day_is_a_refusal_o1_records():
    check, broker, record, _, printed, _ = make_check(at(11, 0, day=date(2026, 10, 15)))
    assert check.run() == 0 and broker.asked == [] and record.written == []
    assert printed == ["margin check 2026-10-15: nothing written: margins.csv has no A14 row for 2026-10-15"]


@pytest.mark.parametrize("failing", ["basket", "index"])
def test_a_broker_failure_is_an_error_row_exit_1_and_no_own_alert(failing):
    check, broker, record, alerts, printed, _ = make_check(at(11, 0))
    if failing == "index":
        broker.level = ConnectionError("secret in the text")
    else:
        broker.fail[SF100] = ConnectionError("secret in the text")
    assert check.run() == 1 and alerts.sent == []
    errors = [r for r in record.written[0] if r.status == "error"]
    want = "NIFTY quote: ConnectionError" if failing == "index" else "Groww: ConnectionError"
    assert len(errors) == (6 if failing == "index" else 1) and {r.detail for r in errors} == {want}
    assert "secret" not in printed[-1] and want in printed[-1]  # the class name only, never the text


def test_a_record_that_cannot_be_written_or_read_exits_1():
    check, *_, printed, _ = make_check(at(11, 0), record=MemoryRecord(refuse=RuntimeError("the record was not saved")))
    assert check.run() == 1 and "the record was not saved" in printed[-1]
    check, broker, *_, printed, _ = make_check(at(11, 0), record=MemoryRecord(done=OSError("Drive answered 503")))
    assert check.run() == 1 and broker.asked == [] and "OSError: Drive answered 503" in printed[-1]


def test_a_row_its_file_does_not_reproduce_or_a_missing_file_is_an_error_not_a_check():
    changed = [dict(ROWS[0], scan_per_lot_rs="1.00"), *ROWS[1:]]
    check, broker, record, *_ = make_check(at(11, 0), rows=changed)
    assert check.run() == 1 and SF100 not in [key for key, _ in broker.asked]
    assert record.written[0][0].status == "error" and "is not reproduced" in record.written[0][0].detail
    check, broker, record, *_ = make_check(at(11, 0), file=None)
    assert check.run() == 1 and {r.detail for r in record.written[0]} == {"the day's SPAN file is not in the archive"}


def test_a_mismatch_and_an_error_together_alert_the_finding_and_exit_1():
    check, broker, record, alerts, printed, _ = make_check(at(11, 0))
    broker.answers[SF100] = (0.0, 0.0)
    broker.fail[("BF", 200.0)] = TimeoutError()
    assert check.run() == 1 and len(alerts.sent) == 1 and "SF 100" in alerts.sent[0]
    assert "1 basket(s) not checked (Groww: TimeoutError)" in printed[-1]
