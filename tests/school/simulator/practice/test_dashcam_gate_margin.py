"""The practice dashcam, quality gate and margin factor (MS-SIM-d2)."""

import gzip
import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from fno.risk.inputs import RiskInputError
from fno.school.constants import ClosureReason, RecordKind, RoadCode
from fno.school.contracts.dashcam import ReplayConflict
from fno.school.contracts.records import DriftRow
from fno.school.contracts.roads import RoadStatus
from fno.school.contracts.slot_file import decode_slot_file, encode_slot_file
from fno.school.fleet.replay_store import ReplayDashcam
from fno.school.simulator.constants import PRACTICE_LABEL
from fno.school.simulator.practice.clock import practice_clock
from fno.school.simulator.practice.dashcam import PracticeDashcam, labels
from fno.school.simulator.practice.gate import PracticeQualityGate
from fno.school.simulator.practice.margin import PRACTICE_MARGIN_LABEL, latest_factor
from tests.school.contracts import builders as b

SESSION = date(2022, 3, 7)


def records():
    from fno.school.contracts.accounts import FilledLeg

    leg = FilledLeg(b.key(1000.0), "sell", 50, 99.0, 12.0)
    return (DriftRow(SESSION, "p1", leg, 98.5), DriftRow(SESSION, "p2", leg, None))


def test_every_stored_record_line_carries_the_practice_label(tmp_path):
    """Criterion 15: the label is in the record itself, not only in the report."""
    dashcam = PracticeDashcam(tmp_path, practice_clock(SESSION))
    seal = dashcam.seal(SESSION, "15:00", RecordKind.DRIFT, records())
    data = (tmp_path / seal.path).read_bytes()
    assert labels(data) == [PRACTICE_LABEL, PRACTICE_LABEL] and len(decode_slot_file(data)) == 2


def test_a_plain_replay_dashcam_still_reads_a_practice_file_and_the_records_are_the_same(tmp_path):
    clock = practice_clock(SESSION)
    seal = PracticeDashcam(tmp_path, clock).seal(SESSION, "15:00", RecordKind.DRIFT, records())
    assert ReplayDashcam(tmp_path, clock).read(seal) == records()
    assert labels(encode_slot_file(records())) == [None, None]  # the pilot's own encoding carries no label


def test_a_practice_file_is_write_once_and_the_same_bytes_again_are_a_no_op(tmp_path):
    dashcam = PracticeDashcam(tmp_path, practice_clock(SESSION))
    first = dashcam.seal(SESSION, "15:00", RecordKind.DRIFT, records())
    assert dashcam.seal(SESSION, "15:00", RecordKind.DRIFT, records()) == first
    with pytest.raises(ReplayConflict):
        dashcam.seal(SESSION, "15:00", RecordKind.DRIFT, records()[:1])


def test_the_label_key_sits_beside_the_record_in_canonical_order(tmp_path):
    seal = PracticeDashcam(tmp_path, practice_clock(SESSION)).seal(SESSION, "15:00", RecordKind.DRIFT, records())
    line = json.loads(gzip.decompress((tmp_path / seal.path).read_bytes()).splitlines()[0])
    assert list(line) == ["label", "record", "type"] and line["type"] == "DriftRow"


# ---- the gate -------------------------------------------------------------------------------------------------------


def test_the_practice_gate_keeps_a_closed_roads_status_and_opens_an_open_one():
    gate = PracticeQualityGate()
    closed = b.road_day(RoadCode.BANKNIFTY_MONTHLY, RoadStatus(ClosureReason.LOT_MISMATCH))
    assert gate.check(closed, b.snapshot()) == closed.status
    assert gate.check(b.road_day(), b.snapshot()).open


def test_the_practice_gate_does_not_apply_the_capture_window_the_pilots_gate_does():
    """A snapshot stamped at the close is out of the pilot's 14:55-15:10 window; practice has no capture window."""
    from fno.school.quality.gate import RoadQualityGate

    late = b.snapshot()
    from datetime import datetime, timedelta

    close = datetime.combine(late.session, datetime.min.time(), tzinfo=late.started_at.tzinfo) + timedelta(
        hours=15, minutes=30
    )
    late = replace(late, started_at=close, finished_at=close)

    class NoListing:
        def contracts(self, *args):
            raise AssertionError("not asked")

    assert RoadQualityGate(NoListing()).check(b.road_day(), late).closed_by is ClosureReason.OUT_OF_WINDOW
    assert PracticeQualityGate().check(b.road_day(), late).open


def test_the_practice_gate_still_refuses_another_roads_snapshot():
    with pytest.raises(ValueError, match="not the road-day's own"):
        PracticeQualityGate().check(b.road_day(RoadCode.BANKNIFTY_MONTHLY), b.snapshot(RoadCode.NIFTY_MONTHLY))


# ---- the margin factor ---------------------------------------------------------------------------------------------

FACTOR_FILE = Path(__file__).resolve().parents[4] / "research" / "data" / "margins" / "stress_factor.csv"


def test_the_latest_factor_serves_every_session_including_ones_before_the_files_first_row():
    factor = latest_factor(FACTOR_FILE)
    assert factor(date(2019, 6, 3)).factor == factor(date(2026, 10, 12)).factor == factor(date(2026, 11, 20)).factor
    assert factor(date(2020, 1, 2)).factor == 2.1


def test_the_pilots_lookup_refuses_the_same_old_session():
    from fno.risk.stress_factor import factor_in_force

    with pytest.raises(RiskInputError):
        factor_in_force(FACTOR_FILE, date(2022, 3, 7), 30)


def test_a_missing_factor_file_refuses_the_entry_like_the_pilots_does(tmp_path):
    with pytest.raises(RiskInputError):
        latest_factor(tmp_path / "missing.csv")(date(2022, 3, 7))


def test_the_margin_label_says_what_it_is():
    assert "stress factor 2.1" in PRACTICE_MARGIN_LABEL and "computed after the fact" in PRACTICE_MARGIN_LABEL
