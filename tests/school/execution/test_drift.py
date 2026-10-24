"""Story MS-P1d criterion 10: the NIFTY drift diagnostic. A filled leg's touch against the same contract's same-side
touch in E3's 15:15 capture; a leg absent from that capture (or without a usable quote there) gives `drift_unknown`,
never a number; other indices get no row; the capture is the day's latest committed record, hash-checked."""

import json
from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from fno.desk.snapshot import ExecutionQuote, ExecutionSnapshot, SnapshotError
from fno.models import IST
from fno.school.constants import SIDE_BUY, SIDE_SELL, RoadCode
from fno.school.execution.capture_1515 import RecordedCapture1515
from fno.school.execution.drift import drift_rows
from tests.school.contracts import builders as b

from .school_builders import AT, fills


def capture(quotes: dict, day: date = b.SESSION, snapshot_id: str = "nifty_20261102_151824") -> ExecutionSnapshot:
    start = datetime.combine(day, datetime.min.time(), IST).replace(hour=15, minute=18)
    return ExecutionSnapshot(day, snapshot_id, "11" * 32, "22" * 32, start, start + timedelta(minutes=3), True, quotes)


def at_1515(strike: float, bid: float, ask: float, valid: bool = True) -> tuple:
    key = (b.EXPIRY, strike, "PE")
    return key, ExecutionQuote("", *key, bid, ask, 500.0, 500.0, valid, "", True)


def nifty_fill(tmp_path):
    sealed = replace(b.sealed(), decision=replace(b.decision(), road=RoadCode.NIFTY_MONTHLY))
    return fills(tmp_path).enter(sealed, b.snapshot(code=RoadCode.NIFTY_MONTHLY), b.seal(), AT)


def test_each_nifty_leg_gets_its_same_side_drift(tmp_path):
    later = capture(dict((at_1515(1000.0, 9.0, 10.0), at_1515(900.0, 5.0, 6.0))))
    rows = drift_rows(b.SESSION, "p1", RoadCode.NIFTY_MONTHLY, nifty_fill(tmp_path), later)
    assert [(r.leg.side, r.leg.price, r.price_1515, r.drift) for r in rows] == [
        (SIDE_SELL, 10.0, 9.0, -1.0),  # sold at the bid 10; the 15:15 bid is 9
        (SIDE_BUY, 5.0, 6.0, 1.0),  # bought at the ask 5; the 15:15 ask is 6
    ]


@pytest.mark.parametrize(
    "quotes", [dict((at_1515(1000.0, 9.0, 10.0),)), dict((at_1515(1000.0, 9.0, 10.0), at_1515(900.0, 5.0, 6.0, False)))]
)
def test_a_leg_absent_or_unusable_at_1515_is_drift_unknown(tmp_path, quotes):  # fmt: skip
    rows = drift_rows(b.SESSION, "p1", RoadCode.NIFTY_MONTHLY, nifty_fill(tmp_path), capture(quotes))
    unknown = rows[1]
    assert unknown.unknown and unknown.price_1515 is None and unknown.drift is None
    assert not rows[0].unknown


def test_no_capture_that_day_makes_every_row_unknown(tmp_path):
    rows = drift_rows(b.SESSION, "p1", RoadCode.NIFTY_WEEKLY, nifty_fill(tmp_path), None)
    assert len(rows) == 2 and all(r.unknown for r in rows)


def test_other_indices_and_unfilled_results_get_no_row(tmp_path):
    filled = fills(tmp_path).enter(b.sealed(), b.snapshot(), b.seal(), AT)
    assert drift_rows(b.SESSION, "p1", RoadCode.BANKNIFTY_MONTHLY, filled, capture({})) == ()
    refused = fills(tmp_path).enter(b.sealed(), b.snapshot(quotes={}), b.seal(), AT)
    assert drift_rows(b.SESSION, "p1", RoadCode.NIFTY_MONTHLY, refused, capture({})) == ()


def test_another_day_s_capture_is_refused(tmp_path):
    with pytest.raises(ValueError, match="not of"):
        drift_rows(b.SESSION, "p1", RoadCode.NIFTY_MONTHLY, nifty_fill(tmp_path), capture({}, b.SESSION + timedelta(1)))


class Snapshots:
    def __init__(self, snapshot: ExecutionSnapshot):
        self.found, self.asked = snapshot, []

    def snapshot(self, day, snapshot_id):
        self.asked.append((day, snapshot_id))
        return replace(self.found, snapshot_id=snapshot_id)


def record(root, snapshot_id: str, finished: str, sha: str = "11" * 32):
    folder = root / "journal" / "execution" / b.SESSION.isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    body = {"snapshot_id": snapshot_id, "finished_at": finished, "csv_sha256": sha}
    (folder / f"{snapshot_id}.json").write_text(json.dumps(body), encoding="utf-8")


def test_the_1515_capture_is_the_day_s_latest_committed_record(tmp_path):
    source = Snapshots(capture({}))
    assert RecordedCapture1515(tmp_path, source).for_session(b.SESSION) is None
    record(tmp_path, "nifty_20261102_152500", "2026-11-02T15:27:00+05:30")
    record(tmp_path, "nifty_20261102_151824", "2026-11-02T15:21:00+05:30")
    found = RecordedCapture1515(tmp_path, source).for_session(b.SESSION)
    assert found.snapshot_id == "nifty_20261102_152500" and source.asked == [(b.SESSION, "nifty_20261102_152500")]


def test_a_capture_not_matching_its_record_is_an_error(tmp_path):
    record(tmp_path, "nifty_20261102_151824", "2026-11-02T15:21:00+05:30", sha="99" * 32)
    with pytest.raises(SnapshotError, match="differs"):
        RecordedCapture1515(tmp_path, Snapshots(capture({}))).for_session(b.SESSION)
