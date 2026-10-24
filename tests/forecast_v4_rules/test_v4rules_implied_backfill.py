"""Story G7b completion, part b1, criteria 1 and 5: the exploratory implied back-fill for V2 and V3 (labels, days,
write-once Drive files per method hash and last day, the first live day) and its real-data reproduction."""

import csv
import io
from datetime import date, timedelta

import pytest

from fno.config import load_config
from fno.constants import V2_RV_5S, V3_RV_20S, V4_BASELINE_PREMIUM_ADJUSTED, V4_BASELINE_RAW_IMPLIED
from fno.forecast_v4_rules.baselines import MISSING, NOT_ELIGIBLE, OK
from fno.forecast_v4_rules.implied import IvPoint
from fno.forecast_v4_rules.implied_backfill import FORECASTERS, ImpliedBackfill, backfill_path
from fno.forecast_v4_rules.records import BACKFILL, BASELINE, SLOT_REPORTED
from fno.forecast_v4_rules.series import DayValue
from fno.forecast_v4_rules.wiring import (
    IMPLIED_METHOD_FILES,
    LIVE_RECORDS,
    build_implied_backfill,
    first_live_implied_day,
    method_sha256,
)
from fno.storage.raw_store import RawFileConflict
from fno.storage.receipts import Receipt, ReceiptFolder

METHOD = "ab" * 32
SESSIONS = [date(2024, 1, 1) + timedelta(n) for n in range(60)]  # every day a session: easy to count
RV = [DayValue(d, 0.0001) for d in SESSIONS]
EOD = {d: IvPoint(0.15, d == SESSIONS[3]) for d in SESSIONS[:10]}  # day 3 flagged; days 10+ have no IV30


class WriteOnceDrive:
    def __init__(self):
        self.files = {}

    def put(self, path: str, data: bytes) -> None:
        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data


def make(method=METHOD) -> ImpliedBackfill:
    return ImpliedBackfill(EOD, RV, SESSIONS, method)


def test_days_run_from_2024_to_the_last_close_and_stop_before_the_first_live_day():
    backfill = ImpliedBackfill(EOD, RV, [date(2023, 12, 29), *SESSIONS], METHOD)
    assert backfill.days(SESSIONS[9], None) == SESSIONS[:10]
    assert backfill.days(SESSIONS[9], SESSIONS[5]) == SESSIONS[:5]
    assert backfill.days(date(2023, 12, 30), None) == []


def test_rows_are_backfill_reported_baselines_with_statuses_never_filled():
    rows = make().rows(SESSIONS[:12])
    assert set(rows) == set(FORECASTERS)
    raw = {r.day: r for r in rows[(V4_BASELINE_RAW_IMPLIED, V2_RV_5S)]}
    assert raw["2024-01-01"].status == OK and float(raw["2024-01-01"].value) == pytest.approx(0.15**2 * 5 / 365)
    assert raw["2024-01-04"].status == MISSING  # flagged
    assert raw["2024-01-12"].status == MISSING  # no IV30
    premium = {r.day: r for r in rows[(V4_BASELINE_PREMIUM_ADJUSTED, V3_RV_20S)]}
    assert premium["2024-01-01"].status == NOT_ELIGIBLE  # no 500-point window this early
    for row in raw.values():
        assert (row.label, row.kind, row.slot, row.made_at, row.method_sha256) == (
            BACKFILL, BASELINE, SLOT_REPORTED, "", METHOD)  # fmt: skip


def test_write_is_write_once_per_method_and_last_day_and_a_rerun_is_a_no_op():
    drive, backfill = WriteOnceDrive(), make()
    paths = backfill.write(backfill.rows(SESSIONS[:10]), drive.put)
    assert paths[0] == backfill_path(METHOD, V4_BASELINE_RAW_IMPLIED, V2_RV_5S, SESSIONS[9])
    assert paths[0] == f"v4/records/backfill/{METHOD[:12]}/raw_implied/v2_rv_next_5_sessions_to_2024-01-10.csv"
    before = dict(drive.files)
    assert make().write(make().rows(SESSIONS[:10]), drive.put) == paths and drive.files == before
    longer = make().write(make().rows(SESSIONS[:11]), drive.put)  # a later last day: new files, none overwritten
    assert set(longer).isdisjoint(paths) and all(drive.files[p] == before[p] for p in paths)
    other = make("cd" * 32).write(make("cd" * 32).rows(SESSIONS[:10]), drive.put)
    assert set(other).isdisjoint(paths)


def test_a_changed_row_on_the_same_path_is_refused():
    drive = WriteOnceDrive()
    make().write(make().rows(SESSIONS[:10]), drive.put)
    changed = ImpliedBackfill({d: IvPoint(0.2, False) for d in EOD}, RV, SESSIONS, METHOD)
    with pytest.raises(RawFileConflict):
        changed.write(changed.rows(SESSIONS[:10]), drive.put)


def test_the_file_text_is_phase_1s_record_layout_in_date_order():
    drive, backfill = WriteOnceDrive(), make()
    path = backfill.write(backfill.rows(list(reversed(SESSIONS[:3]))), drive.put)[0]
    rows = list(csv.DictReader(io.StringIO(drive.files[path].decode())))
    assert [r["day"] for r in rows] == ["2024-01-01", "2024-01-02", "2024-01-03"]
    assert list(rows[0])[:4] == ["day", "value", "status", "label"]


def test_empty_days_write_nothing():
    drive = WriteOnceDrive()
    assert make().write(make().rows([]), drive.put) == [] and drive.files == {}


def receipt(folder: ReceiptFolder, path: str) -> None:
    folder.write(Receipt(path, "0" * 64, 1, "2026-11-02T09:00:00+00:00", "test", "run"))


def test_first_live_implied_day_reads_the_receipt_paths_of_implied_forecasters_only(tmp_path):
    folder = ReceiptFolder(tmp_path)
    assert first_live_implied_day(folder) is None
    receipt(folder, f"{LIVE_RECORDS}/v5_ewma_lognormal/v5_close_inside_k_plus_minus_p/2026/2026-10-28.json")
    assert first_live_implied_day(folder) is None
    receipt(folder, f"{LIVE_RECORDS}/raw_implied/v2_rv_next_5_sessions/2026/2026-11-02.json")
    receipt(folder, f"{LIVE_RECORDS}/premium_adjusted_implied/v3_rv_next_20_sessions/2026/2026-10-30.json")
    assert first_live_implied_day(folder) == date(2026, 10, 30)


def test_real_panel_and_closes_reproduce_the_eod_iv30_counts_and_one_raw_value():
    """Criterion 1 on committed data, to 23 Oct 2026: 691 regular sessions from 1 Jan 2024, 652 unflagged and 39
    flagged IV30 values (G7b measured 686 / 647 / 39 to 15 Oct)."""
    backfill, _ = build_implied_backfill(load_config())
    days = [d for d in backfill.days(date(2026, 10, 23), None)]
    points = [backfill.eod.get(d) for d in days]
    assert (
        len(days),
        sum(p is not None and not p.flagged for p in points),
        sum(p is not None and p.flagged for p in points),
    ) == (691, 652, 39)  # noqa: E501
    iv = backfill.eod[date(2026, 10, 23)]
    raw = backfill.implied[V2_RV_5S].raw(date(2026, 10, 23), iv)  # d+5 = Fri 30 Oct, 7 calendar days
    assert raw.value == pytest.approx(iv.value**2 * 7 / 365)


def test_the_implied_rows_carry_their_own_method_hash():
    assert method_sha256(IMPLIED_METHOD_FILES) != method_sha256()
    assert make(method_sha256(IMPLIED_METHOD_FILES)).method == method_sha256(IMPLIED_METHOD_FILES)


def test_a_live_path_off_the_layout_stops_with_its_path(tmp_path):
    folder = ReceiptFolder(tmp_path)
    receipt(folder, f"{LIVE_RECORDS}/raw_implied/2026-11-02.json")
    with pytest.raises(ValueError, match="raw_implied/2026-11-02.json"):
        first_live_implied_day(folder)


def test_days_stop_at_the_last_eod_chain_and_where_the_longest_horizon_still_ends_in_the_sessions():
    # EOD chains for days 0-9 only: a later close does not extend the back-fill (no missing-then-present rows)
    assert make().days(SESSIONS[30], None) == SESSIONS[:10]
    # 60 sessions, V3's horizon 20: the last day with a whole horizon is index 39
    full = ImpliedBackfill({d: IvPoint(0.15, False) for d in SESSIONS}, RV, SESSIONS, METHOD)
    assert full.days(SESSIONS[-1], None)[-1] == SESSIONS[39]
    assert ImpliedBackfill({}, RV, SESSIONS, METHOD).days(SESSIONS[-1], None) == []


def test_real_premium_adjusted_is_first_eligible_at_the_april_2026_refit():
    """Real data: the window first reaches 500 points at the 1 Apr 2026 refit (not at 2 Mar), V2's ratio 0.6336."""
    backfill, _ = build_implied_backfill(load_config())
    ratio = backfill.implied[V2_RV_5S].ratio
    assert ratio.at(date(2026, 3, 2)) is None
    assert ratio.at(date(2026, 4, 1)) == pytest.approx(0.6335897, rel=1e-6)
