"""Story G7: one day's records, the live capture's cutoff, V1's start, the back-fill and the record files."""

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from fno.constants import (
    V1_RV_1S,
    V4_BASELINE_BASE_RATE,
    V4_BASELINE_HAR_INTRADAY,
    V4_RULE_V1_CLOSE_BLEND,
    V6_BIG_MOVE_1S,
)
from fno.forecast_v4_rules import records
from fno.forecast_v4_rules.backfill import backfill, backfill_days
from fno.forecast_v4_rules.baselines import NOT_ELIGIBLE, NOT_STARTED, OK
from fno.forecast_v4_rules.capture import CaptureRefused, DayForecasts, Inputs, capture_day, cutoff
from fno.forecast_v4_rules.series import SessionRv, closes_rows, regular_closes
from fno.models import IST

ROOT = Path(__file__).resolve().parents[2]
TEXT = (ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv").read_text()
TODAY = date(2026, 10, 15)


def forecasts(intraday=(), extra_session=TODAY):
    closes = regular_closes(closes_rows(TEXT))
    lines = [line for line in TEXT.splitlines()[1:] if line.split(",")[1] == "regular"]
    sessions = [c.day for c in closes] + [extra_session]
    return DayForecasts(Inputs(closes, lines, list(intraday), sessions, "m" * 64))


def live_rows(n, last=date(2026, 10, 14), void=()):
    out, day = [], last
    while len(out) < n:
        if day.weekday() < 5:
            seen = datetime.combine(day, datetime.min.time(), IST) + timedelta(hours=16)
            out.append(SessionRv(day, None if len(out) in void else 1e-4 * (1 + len(out) % 7), seen))
        day -= timedelta(days=1)
    return sorted(out, key=lambda r: r.day)


def test_v1_starts_after_20_live_non_void_sessions():
    assert forecasts(live_rows(19)).values(TODAY)[(V4_RULE_V1_CLOSE_BLEND, V1_RV_1S)].status == NOT_STARTED
    assert forecasts(live_rows(20)).values(TODAY)[(V4_RULE_V1_CLOSE_BLEND, V1_RV_1S)].status == OK
    void_one = live_rows(20, void={5})  # 19 usable: a void session is never a value
    assert forecasts(void_one).values(TODAY)[(V4_RULE_V1_CLOSE_BLEND, V1_RV_1S)].status == NOT_STARTED


def test_a_row_first_seen_after_the_cutoff_does_not_count():
    rows = live_rows(20)
    late = rows[-1]
    rows[-1] = SessionRv(late.day, late.value, cutoff(TODAY) + timedelta(minutes=1))
    assert forecasts(rows).values(TODAY)[(V4_RULE_V1_CLOSE_BLEND, V1_RV_1S)].status == NOT_STARTED


def test_har_intraday_is_eligible_from_250_live_sessions():
    key = (V4_BASELINE_HAR_INTRADAY, V1_RV_1S)
    assert forecasts(live_rows(249)).values(TODAY)[key].status == NOT_ELIGIBLE
    assert forecasts(live_rows(250)).values(TODAY)[key].status == OK


def test_records_carry_label_kind_slot_and_hashes():
    rows = forecasts().records(TODAY, records.LIVE, "2026-10-15T14:50:00+05:30")
    rule = rows[(V4_RULE_V1_CLOSE_BLEND, V1_RV_1S)]
    assert (rule.status, rule.kind, rule.slot, rule.value) == (NOT_STARTED, "rule", "rules", "")
    base = rows[(V4_BASELINE_BASE_RATE, V6_BIG_MOVE_1S)]
    assert (base.status, base.slot, base.label) == (OK, "reported", "live") and float(base.value) == pytest.approx(
        0.02667, abs=1e-5
    )


def test_inputs_hash_moves_with_an_earlier_close_and_not_with_a_later_one():
    plain = forecasts().records(TODAY - timedelta(days=1), "x", "")[(V4_BASELINE_BASE_RATE, V6_BIG_MOVE_1S)]
    lines = TEXT.splitlines()
    later = "\n".join(lines[:-1] + [lines[-1].replace("22622.7", "22000.0")]) + "\n"
    earlier = TEXT.replace("2026-10-13,regular,", "2026-10-13,regular,1", 1)
    for text, same in ((later, True), (earlier, False)):
        closes = regular_closes(closes_rows(text))
        lines_reg = [line for line in text.splitlines()[1:] if line.split(",")[1] == "regular"]
        moved = DayForecasts(Inputs(closes, lines_reg, [], [c.day for c in closes], "m" * 64))
        row = moved.records(TODAY - timedelta(days=1), "x", "")[(V4_BASELINE_BASE_RATE, V6_BIG_MOVE_1S)]
        assert (row.inputs_sha256 == plain.inputs_sha256) is same


def test_capture_writes_only_before_the_cutoff_and_only_on_a_session(tmp_path):
    f = forecasts()

    def write(forecaster, question, rows):
        return records.write(tmp_path, forecaster, question, rows)

    before_cutoff = datetime(2026, 10, 15, 14, 59, tzinfo=IST)
    assert capture_day(f, TODAY, before_cutoff, write) == 9
    with pytest.raises(CaptureRefused):
        capture_day(f, TODAY, datetime(2026, 10, 15, 15, 0, tzinfo=IST), write)
    with pytest.raises(CaptureRefused):
        capture_day(f, date(2026, 10, 17), datetime(2026, 10, 17, 11, 0, tzinfo=IST), write)  # a Saturday
    with pytest.raises(CaptureRefused):
        capture_day(forecasts(extra_session=date(2026, 10, 16)), date(2026, 10, 16), before_cutoff, write)  # not today
    assert records.first_live_day(tmp_path) == TODAY


def test_backfill_stops_before_the_first_live_day_skips_unstarted_v1_and_repeats_identically(tmp_path):
    f = forecasts()

    def write(forecaster, question, rows):
        return records.write(tmp_path, forecaster, question, rows)

    days = backfill_days(f, date(2026, 10, 14))
    assert days[-1] == date(2026, 10, 13)
    assert backfill(f, days, write) == 4 * len(days)  # V6 only: V1 has not started
    first = {p: p.read_bytes() for p in tmp_path.glob("*/*.csv")}
    assert backfill(f, days, write) == 0
    assert {p: p.read_bytes() for p in tmp_path.glob("*/*.csv")} == first


def test_records_refuse_invalid_values_and_changed_rows(tmp_path):
    audit = dict(label="live", kind="rule", slot="reported", method_sha256="m", inputs_sha256="i", made_at="t")
    with pytest.raises(records.InvalidRecord):
        records.record(TODAY, V6_BIG_MOVE_1S, OK, 1.01, **audit)
    with pytest.raises(records.InvalidRecord):
        records.record(TODAY, V1_RV_1S, OK, 0.0, **audit)
    row = records.record(TODAY, V6_BIG_MOVE_1S, OK, 0.5, **audit)
    assert records.write(tmp_path, "f", V6_BIG_MOVE_1S, [row]) == 1
    rerun = records.record(TODAY, V6_BIG_MOVE_1S, OK, 0.5, **{**audit, "made_at": "later"})
    assert records.write(tmp_path, "f", V6_BIG_MOVE_1S, [rerun]) == 0  # same row, another time: nothing changes
    with pytest.raises(records.RecordConflict):
        records.write(tmp_path, "f", V6_BIG_MOVE_1S, [records.record(TODAY, V6_BIG_MOVE_1S, OK, 0.6, **audit)])
    header = (tmp_path / "f" / f"{V6_BIG_MOVE_1S}.csv").read_text().splitlines()[0]
    assert header.startswith("day,value,status,label,")
