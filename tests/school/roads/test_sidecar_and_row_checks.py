"""Judge 482 finding 2: each check of a capture's sidecar and rows has a test whose oracle is the plant itself (a
capture built to break exactly that check), not the code under test."""

from datetime import UTC, date, timedelta, timezone

import pytest

from fno.school.constants import ClosureReason, RoadCode
from fno.school.quality.gate import RoadQualityGate
from fno.school.roads.capture import CaptureProblem, CaptureReader
from tests.school.roads.capture_builder import MONTHLIES, SESSION, DictStore, Plant, reader_over_all, road

BANK = road(RoadCode.BANKNIFTY_MONTHLY)


def read(**plant):
    store = DictStore()
    Plant(BANK, **plant).write(store)
    return CaptureReader({BANK.dataset: store}).read(BANK, SESSION)


def reason_of(**plant):
    with pytest.raises(CaptureProblem) as raised:
        read(**plant)
    return raised.value.reason


def test_a_leg_the_a4_rule_marks_invalid_is_not_a_valid_quote_and_does_not_pass_the_leg_count():
    def invalidate(rows):
        for row in rows:
            if row["expiry"] == MONTHLIES[0].isoformat() and row["strike"] == "1000" and row["type"] == "CE":
                row["valid"] = "false"  # bid, ask and sizes stay: only A4's verdict says it is unusable

    capture = read(change_rows=[invalidate])
    snapshot = capture.snapshot()
    invalid = [k for k, q in snapshot.quotes.items() if not q.valid]
    assert len(invalid) == 1 and invalid[0].strike == 1000.0
    assert (
        snapshot.quotes[invalid[0]].bid
        and snapshot.quotes[invalid[0]].ask
        and not snapshot.quotes[invalid[0]].two_sided
    )
    store = DictStore()
    Plant(BANK, change_rows=[invalidate]).write(store)
    from fno.school.roads.catalogue import RecordedRoadCatalogue
    from tests.school.roads.capture_builder import CALENDAR, FixedExpiries, FixedLots

    reader = reader_over_all(store)
    day = next(d for d in RecordedRoadCatalogue(CALENDAR, reader, FixedExpiries(), FixedLots()).day(SESSION)
               if d.road is BANK)  # fmt: skip
    counts = RoadQualityGate(band_steps=10).legs(day, snapshot)
    assert (counts.observed, counts.passed) == (32, 31)


@pytest.mark.parametrize("failures", [["one contract failed"], ["a"], ["raw quote file not saved"]])
def test_a_sidecar_with_failures_is_incomplete_even_when_it_says_complete(failures):
    assert reason_of(failures=failures) is ClosureReason.CAPTURE_INCOMPLETE


@pytest.mark.parametrize("spot", [0, -5.0, "nan", "inf", "-inf", None, "text", [1050]])
def test_a_spot_that_is_not_finite_and_positive_is_incomplete(spot):
    assert reason_of(spot=spot) is ClosureReason.CAPTURE_INCOMPLETE


def test_a_spot_just_above_zero_is_accepted():
    assert read(spot=0.01).spot == 0.01


def test_a_capture_that_finished_before_it_started_is_incomplete_but_one_that_took_no_time_is_not():
    assert reason_of(minutes=-1) is ClosureReason.CAPTURE_INCOMPLETE
    assert read(minutes=0).finished_at == read(minutes=0).started_at


def test_a_capture_stamped_on_another_day_is_out_of_window_whichever_end_is_wrong():
    assert reason_of(start_day=-1) is ClosureReason.OUT_OF_WINDOW  # a day early, the same clock time
    assert reason_of(start_day=1) is ClosureReason.OUT_OF_WINDOW
    assert reason_of(start_day=-1, finish_day=1) is ClosureReason.OUT_OF_WINDOW  # started yesterday, finished today
    assert reason_of(finish_day=1) is ClosureReason.OUT_OF_WINDOW  # started today but finished tomorrow


def test_times_are_judged_in_ist_whatever_zone_the_sidecar_wrote():
    in_utc = read(zone=UTC)  # 09:32 UTC is 15:02 IST
    assert in_utc.started_at.utcoffset() == timedelta(0) and in_utc.started_at.hour == 9
    assert read(zone=timezone(timedelta(hours=-5))).session == SESSION
    assert reason_of(relabel=UTC) is ClosureReason.OUT_OF_WINDOW  # 15:02 wall clock under a UTC label is 20:32 IST


def test_a_capture_at_the_very_end_of_the_day_in_utc_is_the_same_session_in_ist():
    late = date(2026, 11, 2)
    # 15:02 IST on 2 Nov written in a zone far enough behind to date it 1 Nov would be 1 Nov there, 2 Nov in IST
    behind = timezone(timedelta(hours=-12))
    capture = read(zone=behind)
    assert capture.started_at.date() == date(2026, 11, 1) and capture.session == late
