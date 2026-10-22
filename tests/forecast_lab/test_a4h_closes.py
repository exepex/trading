"""FL1-1d: A4h's close read as the evening's close: NIFTY 50 and NIFTY BANK from the day's record (else the 16:00
recheck), verified through O9's cache, only when NSE stamped the list that day at or after 15:30; never INDIA VIX;
nothing when no verified record exists. Made-up levels only."""

import json
from datetime import date

from fno.forecast_lab.a4h_closes import A4hTodayCloses

WED = date(2026, 10, 21)
RECORD, RECHECK = "data/closes/2026/10/2026-10-21.json", "data/closes/2026/10/2026-10-21.recheck.json"


class Report:
    def __init__(self, problems=()):
        self.problems = list(problems)


class Cache:
    def __init__(self, root, files, damaged=()):
        self.root, self.files, self.damaged = root, files, set(damaged)

    def local(self, path):
        return self.root / path

    def sync(self, prefix):
        if prefix in self.files:
            (self.root / prefix).parent.mkdir(parents=True, exist_ok=True)
            (self.root / prefix).write_text(json.dumps(self.files[prefix]), encoding="utf-8")
        return Report(["damaged"] if prefix in self.damaged else [])


def record(stamp="21-Oct-2026 15:30", nifty=1000.5):
    return {"nse_stamp": stamp, "provisional": True, "indices": {
        "NIFTY 50": {"last": nifty, "open": 990.0, "official_close": True},
        "NIFTY BANK": {"last": 2000.25, "open": 1990.0, "official_close": True},
        "INDIA VIX": {"last": 15.7, "open": 14.0, "official_close": False}}}  # fmt: skip


def test_the_day_s_record_gives_nifty_and_banknifty(tmp_path):
    closes = A4hTodayCloses(Cache(tmp_path, {RECORD: record()}))
    assert (closes.close("NIFTY", WED), closes.close("BANKNIFTY", WED)) == (1000.5, 2000.25)
    assert closes.close("INDIA VIX", WED) is None


def test_a_list_stamped_before_15_30_or_another_day_is_never_the_close(tmp_path):
    for stamp in ("21-Oct-2026 15:29", "20-Oct-2026 15:30", ""):
        assert (
            A4hTodayCloses(Cache(tmp_path / stamp.replace(" ", "_"), {RECORD: record(stamp)})).close("NIFTY", WED)
            is None
        )


def test_the_recheck_serves_when_the_first_read_is_missing_or_damaged(tmp_path):
    recheck = {**record(nifty=1001.0), "indices": {"NIFTY 50": {"last": 1001.0, "open": 990.0}}}
    assert A4hTodayCloses(Cache(tmp_path / "a", {RECHECK: recheck})).close("NIFTY", WED) == 1001.0
    damaged = Cache(tmp_path / "b", {RECORD: record(), RECHECK: recheck}, damaged={RECORD})
    assert A4hTodayCloses(damaged).close("NIFTY", WED) == 1001.0
    none = A4hTodayCloses(Cache(tmp_path / "c", {}))
    assert none.close("NIFTY", WED) is None and "2026-10-21" in none.why_missing(WED)


def test_an_index_a4h_marks_as_not_the_official_close_is_never_used(tmp_path):
    marked = record()
    marked["indices"]["NIFTY 50"]["official_close"] = False  # A4h's own word wins over the name
    assert A4hTodayCloses(Cache(tmp_path, {RECORD: marked})).close("NIFTY", WED) is None
