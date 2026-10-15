"""Story G10 part 1 (criteria 3 and 4, G8's side): the day files' labels, the system_late day out for every family,
the counts on every report and the live moved-after-cutoff flag from A16's SHA-checked snapshots."""

import hashlib
from datetime import date, datetime, time, timedelta

import pytest

from fno.constants import V4_DAY_A, V4_DAY_A2, V4_DAY_SYSTEM_LATE, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.comparison import compare, paired_rows
from fno.forecast_scoring.v4.cutoff_moves import A16CutoffMoves, SnapshotChanged
from fno.forecast_scoring.v4.days import DayCounts, DayFileError, DayLabel, LateDaysOut, day_counts, parse_day
from fno.forecast_scoring.v4.inputs import Outcome, V4ForecastSource, V4OutcomeSource
from fno.forecast_scoring.v4.render import report_json, report_lines
from fno.forecast_v4.misses import MissReport
from fno.forecast_v4.terms import MOVED_AFTER_CUTOFF_X
from fno.intraday.document import CallRecord, SnapshotDocument
from fno.intraday.ledger import SlotLedger, taken_row
from fno.intraday.status import verdict
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from tests.forecast_scoring_v4.helpers import values

DAY = date(2026, 10, 22)
PACK = "a" * 64


def body(label=V4_DAY_A, sha=PACK, observed="2026-10-22T14:31:12+05:30", day="2026-10-22"):
    return {"day": day, "label": label, "pack_sha256": sha, "observed_by": observed}


def test_a_day_file_carries_its_label_pack_and_latest_observed_at():
    found = parse_day("2026-10-22", body())
    assert found == DayLabel(DAY, V4_DAY_A, PACK, datetime(2026, 10, 22, 14, 31, 12, tzinfo=IST))
    assert parse_day("2026-10-22", body(V4_DAY_A2, observed="2026-10-22T14:40:00+05:30")).label == V4_DAY_A2
    assert parse_day("2026-10-22", body(V4_DAY_SYSTEM_LATE, sha="", observed="")).pack_sha256 == ""


@pytest.mark.parametrize(
    "bad",
    [
        body(observed="2026-10-22T14:40:01+05:30"),  # a field after 14:40:00: the day is system_late, never A
        body(sha=""),  # an A day names its pack
        body(V4_DAY_A2, observed=""),
        body(sha="x" * 64),
        body(label="B"),
        body(day="2026-10-23"),
    ],
)
def test_a_day_file_that_breaks_the_format_stops_scoring(bad):
    with pytest.raises(DayFileError):
        parse_day("2026-10-22", bad)


DAYS = [date(2026, 10, d) for d in range(19, 31) if date(2026, 10, d).weekday() < 5]
LATE = DAYS[3]  # no pack: the forecaster has no row either, the baseline has one
OUTCOMES = {d: Outcome(i % 3 == 0, False, 15.0, 0.001) for i, d in enumerate(DAYS)}


class Files(V4ForecastSource):
    def forecasters(self, question):
        return ["base_rate", "weather_m1"]

    def values(self, question, forecaster):
        given = DAYS if forecaster == "base_rate" else [d for d in DAYS if d != LATE]
        return values({d: 0.2 for d in given}, live=True)


class Outcomes(V4OutcomeSource):
    def outcomes(self, question):
        return OUTCOMES


class Labels:
    def __init__(self, late):
        self.late = late

    def labels(self):
        return {d: DayLabel(d, V4_DAY_SYSTEM_LATE if d in self.late else V4_DAY_A, PACK, None) for d in DAYS}


def _misses(late):
    inputs = LateDaysOut(Files(), Outcomes(), Labels(late))
    rows = paired_rows(inputs.values(V6_BIG_MOVE_5S, "weather_m1"), inputs.values(V6_BIG_MOVE_5S, "base_rate"),
                       inputs.outcomes(V6_BIG_MOVE_5S))  # fmt: skip
    return compare(V6_BIG_MOVE_5S, "weather_m1", "base_rate", rows, inputs.outcomes(V6_BIG_MOVE_5S), 4)


def test_a_system_late_day_is_out_for_every_family_never_a_miss_nor_scored():
    plain, late = _misses(set()), _misses({LATE})
    assert plain.misses == MissReport(observable=len(DAYS), missed=1, big_observable=0, big_missed=0, input_failures=0)
    assert late.misses == MissReport(observable=len(DAYS) - 1, missed=0, big_observable=0, big_missed=0,
                                     input_failures=0)  # fmt: skip
    assert LATE not in late.pairing.scored.days and late.pairing.missing_forecast == 0


def test_every_report_counts_the_labels_and_the_flag_up_to_its_day():
    labels = {d: DayLabel(d, lab, PACK, None) for d, lab in zip(DAYS[:5], [V4_DAY_A, V4_DAY_A, V4_DAY_A2,
              V4_DAY_SYSTEM_LATE, V4_DAY_A])}  # fmt: skip
    flags = {DAYS[0]: True, DAYS[1]: False, DAYS[2]: None, DAYS[3]: None, DAYS[4]: True}
    counts = day_counts(labels, flags.get, as_of=DAYS[3])  # DAYS[4] is after the report's day
    assert counts == DayCounts(a=2, a2=1, late=1, flagged=1, unknown=2)
    assert counts.line() in report_lines([], frozen=False, as_of="x", days=counts)
    assert report_json([], frozen=False, as_of="x", days=counts)["days"]["late"] == 1


def snapshot(at, level, sent_after=0.0):
    mark = datetime.combine(DAY, at, IST)
    answered = mark + timedelta(seconds=sent_after + 1)
    index = CallRecord("index", mark + timedelta(seconds=sent_after), answered, {"last_price": level}, "")
    return SnapshotDocument("groww", "NIFTY", DAY, mark, index, level, answered - timedelta(seconds=1))


def recorded(tmp_path, docs):
    ledger, store = SlotLedger(tmp_path / "intraday"), LocalFolderStore(tmp_path / "drive")
    for n, doc in enumerate(docs):
        data, path = doc.to_bytes(), f"intraday/{n}.json.gz"
        store.put(path, data)
        ledger.append(DAY, [taken_row(doc, verdict(doc, None), path, hashlib.sha256(data).hexdigest(), None)])
    return ledger, store


def test_the_live_flag_reads_a16s_1430_and_1515_levels_and_is_strict(tmp_path):
    start = 25000.0
    above = start * (1 + MOVED_AFTER_CUTOFF_X * 1.01)
    ledger, store = recorded(tmp_path, [snapshot(time(14, 30), start), snapshot(time(15, 15), above)])
    assert A16CutoffMoves(ledger, store, MOVED_AFTER_CUTOFF_X).moved(DAY) is True
    assert A16CutoffMoves(ledger, store, MOVED_AFTER_CUTOFF_X * 1.02).moved(DAY) is False


def test_a_missing_or_unusable_level_is_not_computable_and_a_changed_copy_stops(tmp_path):
    late_answer = snapshot(time(15, 15), 25100.0, sent_after=200)  # answered after the mark's window: unusable
    ledger, store = recorded(tmp_path, [snapshot(time(14, 30), 25000.0), late_answer])
    assert A16CutoffMoves(ledger, store, MOVED_AFTER_CUTOFF_X).moved(DAY) is None
    assert A16CutoffMoves(ledger, store, MOVED_AFTER_CUTOFF_X).moved(DAY + timedelta(days=1)) is None  # no rows
    (tmp_path / "drive" / "intraday" / "0.json.gz").write_bytes(b"changed")  # edited in place in Drive
    with pytest.raises(SnapshotChanged):
        A16CutoffMoves(ledger, store, MOVED_AFTER_CUTOFF_X).moved(DAY)
