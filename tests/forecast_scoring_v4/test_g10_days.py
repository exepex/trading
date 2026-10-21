"""Story G10 part 1 (criteria 3 and 4, G8's side): the day files' labels, the system_late day out for every family,
the counts on every report and the moved-after-cutoff flag A16's 15:30 run commits."""

import math
from datetime import date, datetime

import pytest

from fno.constants import V4_DAY_A, V4_DAY_SYSTEM_LATE, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.comparison import compare, paired_rows
from fno.forecast_scoring.v4.cutoff_moves import RecordedCutoffMoves
from fno.forecast_scoring.v4.days import DayCounts, DayFileError, DayLabel, LateDaysOut, day_counts, parse_day
from fno.forecast_scoring.v4.inputs import Outcome, V4ForecastSource, V4OutcomeSource
from fno.forecast_scoring.v4.render import report_json, report_lines
from fno.forecast_v4.cutoff_move import cutoff_flag
from fno.forecast_v4.misses import MissReport
from fno.forecast_v4.terms import MOVED_AFTER_CUTOFF_X, V4_CAPTURE_START, V4_COMMON_SNAPSHOT
from fno.models import IST
from tests.forecast_scoring_v4.helpers import values

DAY = date(2026, 10, 22)
PACK = "a" * 64


def body(label=V4_DAY_A, sha=PACK, observed="2026-10-22T14:31:12+05:30", day="2026-10-22"):
    return {"day": day, "label": label, "pack_sha256": sha, "observed_by": observed}


def test_a_day_file_carries_its_label_pack_and_latest_observed_at():
    found = parse_day("2026-10-22", body())
    assert found == DayLabel(DAY, V4_DAY_A, PACK, datetime(2026, 10, 22, 14, 31, 12, tzinfo=IST))
    assert parse_day("2026-10-22", body(observed="2026-10-22T14:40:00+05:30")).label == V4_DAY_A  # at 14:40:00 exactly
    assert parse_day("2026-10-22", body(V4_DAY_SYSTEM_LATE, sha="", observed="")).pack_sha256 == ""


@pytest.mark.parametrize(
    "bad",
    [
        body(observed="2026-10-22T14:40:01+05:30"),  # a field after 14:40:00: the day is system_late, never A
        body(sha=""),  # an A day names its pack
        body(label="A2", observed="2026-10-22T14:31:12+05:30"),  # A2 dropped (orchestrator, 16 Oct): never a label
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
    labels = {d: DayLabel(d, lab, PACK, None) for d, lab in zip(DAYS[:5], [V4_DAY_A, V4_DAY_A, V4_DAY_A,
              V4_DAY_SYSTEM_LATE, V4_DAY_A])}  # fmt: skip
    flags = {DAYS[0]: True, DAYS[1]: False, DAYS[2]: None, DAYS[3]: None, DAYS[4]: True}
    counts = day_counts(labels, flags.get, as_of=DAYS[3])  # DAYS[4] is after the report's day
    assert counts == DayCounts(a=3, late=1, flagged=1, unknown=2)
    assert counts.line() in report_lines([], frozen=False, as_of="x", days=counts)
    assert report_json([], frozen=False, as_of="x", days=counts)["days"]["late"] == 1


def test_g8_reads_the_flag_a16_committed_and_an_older_row_has_none():
    flags = {"2026-10-19": "yes", "2026-10-20": "no", "2026-10-21": ""}
    rows = [{"session": d, "moved_after_cutoff": f} for d, f in flags.items()] + [{"session": "2026-10-22"}]
    found = RecordedCutoffMoves(rows)
    assert [found.moved(d) for d in DAYS[:5]] == [True, False, None, None, None]  # 23 Oct: no row at all


def test_the_flag_is_strict_at_x_carries_only_a_sign_and_needs_both_levels():
    start, x = 25000.0, MOVED_AFTER_CUTOFF_X
    at = {V4_CAPTURE_START: start}
    assert cutoff_flag({**at, V4_COMMON_SNAPSHOT: start * math.exp(x) * (1 + 1e-9)}, x) == ("yes", "+")
    assert cutoff_flag({**at, V4_COMMON_SNAPSHOT: start * math.exp(x) * (1 - 1e-9)}, x) == ("no", "+")
    assert cutoff_flag({**at, V4_COMMON_SNAPSHOT: start * math.exp(-2 * x)}, x) == ("yes", "-")
    assert cutoff_flag({**at, V4_COMMON_SNAPSHOT: start}, x) == ("no", "0")
    assert cutoff_flag({**at, V4_COMMON_SNAPSHOT: None}, x) == ("", "")
