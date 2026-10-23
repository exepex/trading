"""FL1-1d: A4h's close read as the evening's close: NIFTY 50 and NIFTY BANK from the day's record (else the 16:00
recheck), each synced as one file through O9's real cache (FL1-1e), only when NSE stamped the list that
day at or after 15:30; never INDIA VIX; nothing when no verified record exists. Made-up levels only."""

import json
from datetime import date

from fno.forecast_lab.a4h_closes import A4hTodayCloses

from .drive_files import DriveFiles

WED = date(2026, 10, 21)
RECORD, RECHECK = "data/closes/2026/10/2026-10-21.json", "data/closes/2026/10/2026-10-21.recheck.json"


def a4h(tmp_path, files, damaged=()):
    parts = DriveFiles(tmp_path)
    for path, document in files.items():
        parts.put(path, json.dumps(document).encode())
    for path in damaged:
        parts.damage(path)
    return A4hTodayCloses(parts.cache)


def record(stamp="21-Oct-2026 15:30", nifty=1000.5):
    return {"nse_stamp": stamp, "provisional": True, "indices": {
        "NIFTY 50": {"last": nifty, "open": 990.0, "official_close": True},
        "NIFTY BANK": {"last": 2000.25, "open": 1990.0, "official_close": True},
        "INDIA VIX": {"last": 15.7, "open": 14.0, "official_close": False}}}  # fmt: skip


def test_the_day_s_record_gives_nifty_and_banknifty(tmp_path):
    closes = a4h(tmp_path, {RECORD: record()})
    assert (closes.close("NIFTY", WED), closes.close("BANKNIFTY", WED)) == (1000.5, 2000.25)
    assert closes.close("INDIA VIX", WED) is None


def test_a_list_stamped_before_15_30_or_another_day_is_never_the_close(tmp_path):
    for stamp in ("21-Oct-2026 15:29", "20-Oct-2026 15:30", ""):
        assert a4h(tmp_path / stamp.replace(" ", "_"), {RECORD: record(stamp)}).close("NIFTY", WED) is None


def test_the_recheck_serves_when_the_first_read_is_missing_or_damaged(tmp_path):
    recheck = {**record(nifty=1001.0), "indices": {"NIFTY 50": {"last": 1001.0, "open": 990.0}}}
    assert a4h(tmp_path / "a", {RECHECK: recheck}).close("NIFTY", WED) == 1001.0
    assert a4h(tmp_path / "b", {RECORD: record(), RECHECK: recheck}, damaged={RECORD}).close("NIFTY", WED) == 1001.0
    none = a4h(tmp_path / "c", {})
    assert none.close("NIFTY", WED) is None and f"{RECORD}: no receipts under it" in none.why_missing(WED)


def test_a_damaged_record_names_its_problem_in_the_edition_s_words(tmp_path):
    damaged = a4h(tmp_path, {RECORD: record()}, damaged={RECORD})
    assert damaged.close("NIFTY", WED) is None
    why = damaged.why_missing(WED)
    assert why.startswith("A4h's close of 2026-10-21 was not read (") and f"{RECORD}: Drive's bytes do not match" in why


def test_an_index_a4h_marks_as_not_the_official_close_is_never_used(tmp_path):
    marked = record()
    marked["indices"]["NIFTY 50"]["official_close"] = False  # A4h's own word wins over the name
    assert a4h(tmp_path, {RECORD: marked}).close("NIFTY", WED) is None


def test_an_older_copy_on_disk_is_never_used_past_a_problem(tmp_path):
    parts = DriveFiles(tmp_path)
    parts.put(RECORD, json.dumps(record()).encode())
    older = parts.cache.local(RECORD)
    older.parent.mkdir(parents=True, exist_ok=True)
    older.write_text(json.dumps(record(nifty=999.0)), encoding="utf-8")  # not the receipted bytes
    parts.damage(RECORD)  # and Drive's copy fails its check
    assert A4hTodayCloses(parts.cache).close("NIFTY", WED) is None


def test_the_day_s_levels_come_from_the_same_record_and_only_when_recorded(tmp_path):
    full = record()
    full["indices"]["NIFTY 50"].update(high=1010.0, low=985.0)
    full["indices"]["NIFTY BANK"].update(high=None)  # recorded as empty: left out
    closes = a4h(tmp_path / "a", {RECORD: full})
    assert closes.levels("NIFTY", WED) == {"open": 990.0, "high": 1010.0, "low": 985.0}
    assert closes.levels("BANKNIFTY", WED) == {"open": 1990.0}  # high and low not recorded: never made up
    assert a4h(tmp_path / "b", {RECORD: record("21-Oct-2026 15:29")}).levels("NIFTY", WED) == {}
