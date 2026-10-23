"""Criterion 4 of story MS-P1b: the capture gate at 10 of 10 and 9 of 10 sessions and at 95.0% and 95.1% of leg
observations (the boundary), the sessions it looks at, and a counts-only report."""

from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from fno.school.constants import ClosureReason, RoadCode
from fno.school.contracts.roads import OPEN, RoadStatus
from fno.school.fakes import FakeRoadCatalogue, FakeSnapshotSource
from fno.school.quality.capture_gate import GATE_SESSIONS, CaptureGateReport, RoadGate, SessionVerdict
from fno.school.quality.gate import LegCounts, RoadQualityGate
from tests.school.contracts import builders as b
from tests.school.roads.capture_builder import CALENDAR, FixtureListing

BANK = RoadCode.BANKNIFTY_MONTHLY
LISTING = FixtureListing(keys=frozenset(b.snapshot().quotes))
DAYS = [date(2026, 10, 19) + timedelta(days=n) for n in range(10)]


def verdicts(observed=100, passed=100, closures=None, count=GATE_SESSIONS):
    """`count` sessions, each with `observed` legs of which `passed` counted; `closures`: {index: reason}."""
    closures = closures or {}
    return tuple(
        SessionVerdict(DAYS[n], closures.get(n), LegCounts(0, 0) if n in closures else LegCounts(observed, passed))
        for n in range(count)
    )


def gate_of(sessions) -> RoadGate:
    return RoadGate(BANK, DAYS[-1], sessions)


def test_ten_of_ten_snapshots_with_every_leg_counting_opens_the_road():
    assert gate_of(verdicts()).passed


def test_nine_of_ten_snapshots_keeps_the_road_closed_even_with_every_other_leg_perfect():
    nine = gate_of(verdicts(closures={4: ClosureReason.HASH_MISMATCH}))
    assert not nine.passed and nine.snapshots_passed == 9 and nine.legs == LegCounts(900, 900)


def test_fewer_than_ten_sessions_never_open_a_road():
    assert not gate_of(verdicts(count=9)).passed


@pytest.mark.parametrize("passed,expected", [(950, False), (951, True), (949, False), (1000, True)])
def test_the_leg_share_must_be_strictly_over_95_percent(passed, expected):
    per_session = [passed // GATE_SESSIONS + (1 if n < passed % GATE_SESSIONS else 0) for n in range(GATE_SESSIONS)]
    sessions = tuple(SessionVerdict(DAYS[n], None, LegCounts(100, per_session[n])) for n in range(GATE_SESSIONS))
    assert gate_of(sessions).legs == LegCounts(1000, passed)
    assert gate_of(sessions).passed is expected  # 95.0% fails, 95.1% passes


def test_the_share_is_over_all_the_sessions_not_each_one():
    sessions = verdicts(passed=100)[:9] + (SessionVerdict(DAYS[9], None, LegCounts(100, 60)),)
    assert gate_of(sessions).passed  # 960 of 1,000 although one session is at 60%


def test_a_line_is_counts_only_and_says_why_a_road_is_closed():
    line = gate_of(verdicts(closures={1: ClosureReason.LOT_MISMATCH, 2: ClosureReason.LOT_MISMATCH})).line()
    assert line == (
        "BANKNIFTY-M through 2026-10-28: snapshots 8 of 10 (lot_mismatch 2); legs 800 of 800 (100.00%); gate closed"
    )
    assert not [word for word in ("strike", "bid", "ask") if word in line]


def test_a_line_with_no_leg_observations_says_so_instead_of_dividing_by_zero():
    sessions = verdicts(closures={n: ClosureReason.CAPTURE_MISSING for n in range(GATE_SESSIONS)})
    assert "legs 0 of 0 (no legs); gate closed" in gate_of(sessions).line()


def trading_days_back(through: date, count: int = GATE_SESSIONS) -> list[date]:
    days, day = [], through
    while len(days) < count:
        if CALENDAR.session_kind(day) in ("regular", "special"):
            days.insert(0, day)
        day -= timedelta(days=1)
    return days


def pair(day: date, status=OPEN):
    """The BANKNIFTY road-day of `day` and its snapshot, started inside the road's window."""
    began = datetime(day.year, day.month, day.day, 15, 2, tzinfo=b.IST)
    road_day = replace(b.road_day(status=status), session=day)
    return road_day, replace(b.snapshot(), session=day, started_at=began, finished_at=began + timedelta(minutes=2))


def report_of(through: date, closed: dict | None = None, changed: dict | None = None):
    """A report over the ten trading days up to `through`; `closed`: {day: reason} the catalogue closed, `changed`:
    {day: function(snapshot) -> snapshot}."""
    seen = trading_days_back(through)
    pairs = {d: pair(d, RoadStatus((closed or {})[d]) if d in (closed or {}) else OPEN) for d in seen}
    snapshots = {(BANK, d): (changed or {}).get(d, lambda s: s)(pairs[d][1]) for d in seen}
    report = CaptureGateReport(
        CALENDAR,
        FakeRoadCatalogue({d: (pairs[d][0],) for d in seen}),
        FakeSnapshotSource(snapshots),
        RoadQualityGate(LISTING),
    )
    return seen, report


def test_it_looks_at_the_last_ten_trading_days_skipping_a_holiday_a_weekend_and_a_muhurat_evening():
    through = date(2026, 11, 9)  # a Monday; 3 Nov a holiday, 7 Nov a Saturday, 8 Nov a muhurat-only Sunday
    seen, report = report_of(through)
    assert {date(2026, 11, 3), date(2026, 11, 7), date(2026, 11, 8)}.isdisjoint(seen)
    assert [v.session for v in report.build(through)[0].sessions] == seen


def test_a_non_trading_through_day_counts_back_from_the_last_trading_day():
    _, report = report_of(date(2026, 11, 6))
    assert report.build(date(2026, 11, 8))[0].sessions[-1].session == date(2026, 11, 6)


def test_the_report_builds_each_roads_verdicts_from_the_catalogue_the_snapshot_and_the_gate():
    seen = trading_days_back(date(2026, 11, 9))

    def impossible_bid(snapshot):
        key = next(iter(snapshot.quotes))
        return replace(snapshot, quotes={**snapshot.quotes, key: replace(snapshot.quotes[key], bid=9999.0, ask=9999.5)})

    _, report = report_of(
        date(2026, 11, 9), closed={seen[2]: ClosureReason.LOT_MISMATCH}, changed={seen[5]: impossible_bid}
    )
    gate = report.build(date(2026, 11, 9))[0]
    got = {v.session: v.closure for v in gate.sessions}
    assert got[seen[2]] is ClosureReason.LOT_MISMATCH and got[seen[5]] is ClosureReason.IMPOSSIBLE_PRICE
    assert sum(1 for c in got.values() if c is None) == 8 and not gate.passed
    assert gate.legs.observed == 8 * RoadQualityGate(LISTING).legs(*pair(seen[0])).observed


def test_a_report_line_exists_for_each_road_of_the_latest_session():
    _, report = report_of(date(2026, 11, 9))
    lines = report.lines(date(2026, 11, 9))
    assert len(lines) == 1 and lines[0].startswith("BANKNIFTY-M through 2026-11-09: snapshots 10 of 10")


def test_a_snapshot_that_cannot_be_read_after_the_catalogue_read_it_is_a_closed_session_not_a_crash():
    through = date(2026, 11, 9)
    seen, report = report_of(through)
    report.snapshots = FakeSnapshotSource({})  # the capture vanished between the two reads
    gate = report.build(through)[0]
    assert {v.closure for v in gate.sessions} == {ClosureReason.CAPTURE_MISSING} and not gate.passed
