"""Story G7b completion, part e (criteria 5 and 15): G8 reads the v4 records kept in Drive beside the repository CSVs.
What it reads is chosen from the receipts (every live row; this code's latest back-fill per forecaster and question),
only verified bytes are read, and it stops on a stale back-fill, an unverified file, a row that does not match its
file, or a second row for a day."""

import json
from datetime import date

import pytest

from fno.forecast_scoring.v4.drive_forecasts import (
    BadRecord,
    CombinedForecasts,
    DriveForecastRecords,
    DuplicateDay,
    StaleBackfill,
    chosen_paths,
)
from fno.forecast_scoring.v4.inputs import ForecastFiles, ForecastValue
from fno.forecast_v4_rules.drive_records import backfill_name, backfill_path, live_bytes, live_path, read_live
from fno.forecast_v4_rules.records import BACKFILL, BASELINE, LIVE, SLOT_REPORTED, csv_text, record, write

METHOD, OTHER = "ab" * 32, "cd" * 32
Q, Q3, F, RAW = "v2_rv_next_5_sessions", "v3_rv_next_20_sessions", "premium_adjusted_implied", "raw_implied"
D1, D2, D3 = date(2026, 10, 22), date(2026, 10, 23), date(2026, 11, 2)


def row(day: date, value: float, label: str, method: str = METHOD, question: str = Q):
    return record(day, question, "ok", value, kind=BASELINE, slot=SLOT_REPORTED, label=label, method_sha256=method,
                  inputs_sha256="0" * 64, made_at="")  # fmt: skip


def backfill(rows, method=METHOD, forecaster=F, question=Q):
    return backfill_path(method, forecaster, question, max(date.fromisoformat(r.day) for r in rows)), csv_text(
        rows
    ).encode()


def test_the_live_format_round_trips_with_sorted_keys():
    live = row(D3, 3e-4, LIVE)
    assert read_live(live_bytes(live, "A")) == (live, "A")
    keys = list(json.loads(live_bytes(live, "A")))
    assert keys == sorted(keys)
    assert live_path(F, Q, D3) == f"v4/records/live/{F}/{Q}/2026/2026-11-02.json"
    assert backfill_name(f"{Q}_to_2026-10-23.csv") == (Q, D2) and backfill_name("notes.csv") is None


def test_chosen_paths_take_every_live_file_and_this_hashs_latest_backfill():
    old, new = backfill_path(METHOD, F, Q, D1), backfill_path(METHOD, F, Q, D2)
    stale_but_covered = backfill_path(OTHER, F, Q, D2)
    live = live_path(F, Q, D3)
    assert chosen_paths([old, live, stale_but_covered, new], METHOD) == [live, new]
    assert chosen_paths([], METHOD) == []
    assert chosen_paths([live], METHOD) == [live]  # only live rows: no back-fill needed


def test_a_pair_with_a_backfill_only_of_other_code_stops_even_when_others_are_current():
    paths = [backfill_path(METHOD, RAW, Q, D2), backfill_path(OTHER, F, Q, D2), backfill_path(OTHER, RAW, Q3, D2)]
    with pytest.raises(StaleBackfill, match="premium_adjusted_implied.*v2_rv|v2_rv.*premium"):
        chosen_paths(paths, METHOD)


def test_a_path_off_the_layout_stops():
    for path in ("v4/records/backfill/abababababab/raw_implied/notes.csv", "v4/records/live/raw_implied/2026.json"):
        with pytest.raises(BadRecord, match="not a v4 record path"):
            chosen_paths([path], METHOD)


def test_reads_live_and_backfill_rows_with_their_labels():
    path, data = backfill([row(D1, 1e-4, BACKFILL), row(D2, 2e-4, BACKFILL)])
    files = {path: data, live_path(F, Q, D3): live_bytes(row(D3, 3e-4, LIVE), "A")}
    drive = DriveForecastRecords(files, METHOD)
    assert drive.forecasters(Q) == [F] and drive.forecasters(Q3) == []
    assert drive.values(Q, F) == {D1: ForecastValue(1e-4, False), D2: ForecastValue(2e-4, False),
                                  D3: ForecastValue(3e-4, True)}  # fmt: skip
    assert DriveForecastRecords({}, METHOD).values(Q, F) == {}


@pytest.mark.parametrize(
    "path, data",
    [
        (live_path(F, Q, D3), live_bytes(row(D3, 3e-4, BACKFILL), "A")),  # a live file holding a back-fill row
        (live_path(F, Q, D2), live_bytes(row(D3, 3e-4, LIVE), "A")),  # a row of another day than its file
        (live_path(F, Q, D3), live_bytes(row(D3, 3e-4, LIVE), "system_late")),  # never written on a late day
        backfill([row(D1, 1e-4, LIVE)]),  # a live row in a back-fill file
        backfill([row(D1, 1e-4, BACKFILL, method=OTHER)]),  # a row made by other code in this hash's file
    ],
)
def test_a_row_that_does_not_match_its_file_stops(path, data):
    with pytest.raises(BadRecord):
        DriveForecastRecords({path: data}, METHOD)


def test_a_second_row_for_a_day_stops():
    path, data = backfill([row(D3, 1e-4, BACKFILL)])
    files = {path: data, live_path(F, Q, D3): live_bytes(row(D3, 3e-4, LIVE), "A")}
    with pytest.raises(DuplicateDay, match="2026-11-02"):
        DriveForecastRecords(files, METHOD)


class Seam:
    """`wiring.build_drive_records` replaced: receipted paths per folder, and the files of each fetched one."""

    def __init__(self, held: dict[str, bytes]):
        self.held, self.fetched = held, []

    def __call__(self, folder: str):
        seam = self

        class Records:
            def paths(self):
                return sorted(p for p in seam.held if p.startswith(f"data/{folder}"))

            def files(self):
                seam.fetched.append(folder)
                return {p: seam.held[p] for p in self.paths()}

        return Records()


def test_the_wiring_fetches_only_live_files_and_this_codes_latest_backfill(monkeypatch):
    from fno.forecast_scoring.v4 import wiring
    from fno.forecast_v4_rules.wiring import IMPLIED_METHOD_FILES, method_sha256

    method = method_sha256(IMPLIED_METHOD_FILES)
    old, new = (
        backfill([row(D1, 1e-4, BACKFILL, method)], method),
        backfill([row(D1, 1e-4, BACKFILL, method), row(D2, 2e-4, BACKFILL, method)], method),
    )
    stale = backfill([row(D1, 1e-4, BACKFILL, OTHER)], OTHER)
    live = (live_path(F, Q, D3), live_bytes(row(D3, 3e-4, LIVE, method), "A"))
    seam = Seam({f"data/{p}": d for p, d in (old, new, stale, live)})
    monkeypatch.setattr(wiring, "build_drive_records", seam)
    wiring._forecasts.cache_clear()
    try:
        values = wiring._forecasts().values(Q, F)
    finally:
        wiring._forecasts.cache_clear()
    assert sorted(seam.fetched) == sorted([live[0], new[0]])  # never the older file nor the other code's
    assert set(values) >= {D1, D2, D3}


def test_combined_sources_union_forecasters_and_refuse_a_day_held_twice(tmp_path):
    write(tmp_path, F, Q, [row(D1, 1e-4, BACKFILL)])
    drive = DriveForecastRecords({live_path(F, Q, D3): live_bytes(row(D3, 3e-4, LIVE), "A")}, METHOD)
    combined = CombinedForecasts([ForecastFiles(tmp_path), drive])
    assert combined.forecasters(Q) == [F] and set(combined.values(Q, F)) == {D1, D3}
    twice = DriveForecastRecords({live_path(F, Q, D1): live_bytes(row(D1, 3e-4, LIVE), "A")}, METHOD)
    with pytest.raises(DuplicateDay, match="two sources"):
        CombinedForecasts([ForecastFiles(tmp_path), twice]).values(Q, F)


def test_with_no_receipts_the_report_never_touches_drive(monkeypatch, tmp_path):
    import fno.storage.data_wiring as data_wiring
    from fno.forecast_scoring.v4 import wiring
    from fno.storage.receipts import ReceiptFolder

    monkeypatch.setattr(data_wiring, "receipt_folder", lambda: ReceiptFolder(tmp_path))
    monkeypatch.setattr(data_wiring, "build_drive_cache", lambda: pytest.fail("Drive was built"))
    wiring._forecasts.cache_clear()
    try:
        assert [type(s).__name__ for s in wiring._forecasts().sources] == ["ForecastFiles"]
    finally:
        wiring._forecasts.cache_clear()
