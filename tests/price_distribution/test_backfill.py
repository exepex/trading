"""G13 criterion 8: back-fill. It stops before the first live day, writes one gzip file per run and underlying, is
byte-identical on a rerun (a no-op), goes to a new path when the method hash changes, never alerts and counts the days
it skips by reason."""

import gzip
import json
import math
from datetime import date, timedelta

from fno.forecast_v4_rules.series import DayValue
from fno.price_distribution.backfill import Backfill
from fno.price_distribution.build import DayBuilder
from fno.price_distribution.cli import CACHE_PREFIX
from fno.price_distribution.record_files import read_records
from fno.price_distribution.sources import ChainUnavailable
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.drive_cache import DriveCache
from tests.price_distribution.builders import DAY, RATE, Chains, chain_day, drive_store

CALENDAR = CsvSessionCalendar("date,kind,description,source_url\n2026-10-20,holiday,Test,https://example.invalid\n")
CLOSES = [DayValue(DAY - timedelta(days=900 - i), 22_000 * math.exp(0.01 * math.sin(i))) for i in range(900)]
MONDAY, TUESDAY, WEDNESDAY = date(2026, 10, 19), date(2026, 10, 20), date(2026, 10, 21)


def chains():
    return Chains({("NIFTY", DAY): chain_day(), ("NIFTY", MONDAY): chain_day(day=MONDAY),
                   ("NIFTY", WEDNESDAY): ChainUnavailable("nse raw quote file unreadable: gone")})  # fmt: skip


def backfill(tmp_path, live_from=None, method="c0" * 32, source=None):
    store, drive, receipts = drive_store(tmp_path)
    run = Backfill(source or chains(), DayBuilder(CALENDAR, RATE, CLOSES, method), store, CALENDAR, live_from)
    return run, drive, receipts


def test_a_range_is_written_once_with_skipped_days_counted_by_reason(tmp_path):
    run, drive, receipts = backfill(tmp_path)
    lines = run.run("backfill_3pm", ("NIFTY",), DAY, date(2026, 10, 22))
    (path,) = drive.files
    assert path.startswith("data/price_distribution/v1/backfill/backfill_3pm_c0c0c0c0/nifty_2026-10-16_2026-10-22_")
    payload = json.loads(gzip.decompress(drive.files[path]))
    assert [r["day"] for r in payload["records"]] == [DAY.isoformat(), MONDAY.isoformat()]
    assert all(r["made_at"] is None and r["label"] == "backfill_3pm" for r in payload["records"])
    assert "NIFTY backfill_3pm: 1 days skipped: no canonical 3 pm chain" in lines  # Thursday 22nd
    assert "NIFTY backfill_3pm: 1 days skipped: nse raw quote file unreadable: gone" in lines
    assert receipts.read(path) is not None


def test_it_stops_before_the_first_live_day(tmp_path):
    run, drive, _ = backfill(tmp_path, live_from=MONDAY)
    lines = run.run("backfill_3pm", ("NIFTY",), DAY, date(2026, 10, 22))
    assert lines[0] == "back-fill stops before the first live day 2026-10-19"
    (only,) = drive.files.values()
    assert [r["day"] for r in json.loads(gzip.decompress(only))["records"]] == [DAY.isoformat()]


def test_a_rerun_is_byte_identical_and_a_new_method_writes_a_new_path(tmp_path, monkeypatch):
    run, drive, _ = backfill(tmp_path)
    monkeypatch.setattr("time.time", lambda: 1_760_000_000.0)
    run.run("backfill_3pm", ("NIFTY",), DAY, MONDAY)
    first = dict(drive.files)
    monkeypatch.setattr("time.time", lambda: 1_790_000_000.0)  # a later run: gzip carries no time
    run.run("backfill_3pm", ("NIFTY",), DAY, MONDAY)  # same bytes: Drive's no-op, no conflict
    assert drive.files == first
    changed = Backfill(chains(), DayBuilder(CALENDAR, RATE, CLOSES, "d1" * 32), run.store, CALENDAR, None)
    changed.run("backfill_3pm", ("NIFTY",), DAY, MONDAY)
    assert len(drive.files) == 2 and all(drive.files[p] == first[p] for p in first)


def test_an_empty_range_writes_nothing(tmp_path):
    run, drive, _ = backfill(tmp_path, source=Chains({}))
    assert run.run("backfill_3pm", ("NIFTY",), TUESDAY, TUESDAY) == ["NIFTY backfill_3pm: no day to write"]
    assert not drive.files


def test_the_scorer_reads_live_and_backfill_records_from_the_cache_layout(tmp_path):
    """Through the real verified cache and the command's own prefix, as `pricedist score` reads (the rule-8 run
    found a trailing "/" refused here: a hand-copied cache had hidden it)."""
    run, drive, receipts = backfill(tmp_path)
    run.run("backfill_3pm", ("NIFTY",), DAY, MONDAY)
    report = DriveCache(drive, receipts, tmp_path / "cache").sync(CACHE_PREFIX)
    assert report.complete and len(report.downloaded) == 1
    assert [r["day"] for r in read_records(tmp_path / "cache" / "data")] == [DAY.isoformat(), MONDAY.isoformat()]


def test_new_inputs_for_the_same_range_go_to_a_new_path_not_a_conflict(tmp_path):
    run, drive, _ = backfill(tmp_path)
    run.run("backfill_3pm", ("NIFTY",), DAY, MONDAY)
    later = Backfill(chains(), DayBuilder(CALENDAR, RATE, CLOSES[:-1], "c0" * 32), run.store, CALENDAR, None)
    later.run("backfill_3pm", ("NIFTY",), DAY, MONDAY)  # another closes file: other bytes, other path
    assert len(drive.files) == 2


def test_written_days_with_problems_are_counted_by_kind(tmp_path):
    source = Chains({("NIFTY", DAY): chain_day(spot=None), ("NIFTY", MONDAY): chain_day(day=MONDAY, spot=None)})
    lines = backfill(tmp_path, source=source)[0].run("backfill_3pm", ("NIFTY",), DAY, MONDAY)
    assert "NIFTY backfill_3pm: 2 written days with: implied h1" in lines


def test_a_day_whose_build_fails_is_skipped_and_counted_the_rest_are_written(tmp_path):
    class Breaking(DayBuilder):
        def build(self, chain, label, made_at):
            if chain.day == MONDAY:
                raise ValueError("Out of range float values are not JSON compliant")
            return super().build(chain, label, made_at)

    store, drive, _ = drive_store(tmp_path)
    run = Backfill(chains(), Breaking(CALENDAR, RATE, CLOSES, "c0" * 32), store, CALENDAR, None)
    lines = run.run("backfill_3pm", ("NIFTY",), DAY, MONDAY)
    assert "NIFTY backfill_3pm: 1 days skipped: build failed (ValueError): Out of range float values are not JSON " \
           "compliant" in lines  # fmt: skip
    (only,) = drive.files.values()
    assert [r["day"] for r in json.loads(gzip.decompress(only))["records"]] == [DAY.isoformat()]
