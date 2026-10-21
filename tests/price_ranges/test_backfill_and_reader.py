"""G13b criteria 8-9: the back-fill (labelled, stops before the first live day, a rerun a no-op, a build failure
skips its day) and FL1's reader port (sealed live records with `sealed_at` or `late`, back-fill records, latest
scores), all from the Drive cache's local copy."""

import gzip
import json
from datetime import date, datetime, timedelta

from fno.models import IST
from fno.price_ranges.backfill import RangeBackfill
from fno.price_ranges.build import CAPTURE, RangeBuilder
from fno.price_ranges.folders import live_path, scores_path
from fno.price_ranges.reader import RangeForecasts, RangeScores, receipt_file
from fno.price_ranges.sealing import SealCheck
from tests.price_distribution.builders import DAY, RATE, Chains, chain_day, drive_store
from tests.price_ranges.builders import CALENDAR, builder, closes

MONDAY = date(2026, 10, 19)


def backfill(tmp_path, source=None, live_from=None, make=builder):
    store, drive, _ = drive_store(tmp_path)
    chains = source or Chains({("NIFTY", DAY): chain_day(), ("NIFTY", MONDAY): chain_day(day=MONDAY)})
    history = closes(last=date(2026, 10, 23))
    return RangeBackfill(chains, make(), lambda u: history, store, CALENDAR, live_from), drive


def test_a_range_is_written_once_labelled_and_a_rerun_is_a_no_op(tmp_path):
    run, drive = backfill(tmp_path)
    lines = run.run("backfill_3pm", CAPTURE, ("NIFTY",), DAY, date(2026, 10, 22))
    (data,) = drive.files.values()
    records = json.loads(gzip.decompress(data))["records"]
    assert [r["day"] for r in records] == ["2026-10-16", "2026-10-19"] and {r["label"] for r in records} == {
        "backfill_3pm"}  # fmt: skip
    assert "NIFTY backfill_3pm: 2 days skipped: no canonical 3 pm chain" in lines  # 21st and 22nd
    run.run("backfill_3pm", CAPTURE, ("NIFTY",), DAY, date(2026, 10, 22))
    assert len(drive.files) == 1


def test_it_stops_before_the_first_live_day_and_a_failing_day_is_skipped(tmp_path):
    run, drive = backfill(tmp_path, live_from=MONDAY)
    assert (
        run.run("backfill_3pm", CAPTURE, ("NIFTY",), DAY, MONDAY)[0]
        == "back-fill stops before the first live day 2026-10-19"
    )

    class Breaking(RangeBuilder):
        def build(self, underlying, day, *args):
            if day == MONDAY:
                raise ValueError("Out of range float values are not JSON compliant")
            return super().build(underlying, day, *args)

    run, drive = backfill(tmp_path / "b", make=lambda: Breaking(CALENDAR, RATE, "c0" * 32))
    lines = run.run("backfill_3pm", CAPTURE, ("NIFTY",), DAY, MONDAY)
    assert any(line.startswith("NIFTY backfill_3pm: 1 days skipped: build failed (ValueError)") for line in lines)


def test_the_reader_gives_fl1_sealed_or_late_live_records_backfill_records_and_the_latest_scores(tmp_path):
    root = tmp_path / "cache"
    for day in (DAY, MONDAY):
        file = root / "data" / live_path("NIFTY", day, "1545")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps({"day": day.isoformat(), "underlying": "NIFTY", "issue": "1545", "rows": []}))
    pushed = {receipt_file(live_path("NIFTY", DAY, "1545")): datetime(2026, 10, 16, 15, 50, tzinfo=IST)}

    def pushed_at(path):
        return pushed[path]  # MONDAY's has no push evidence: late

    reader = RangeForecasts(root, SealCheck(pushed_at, CALENDAR))
    sealed = reader.sealed("NIFTY", DAY, "1545")
    assert sealed.sealed_at == pushed[receipt_file(live_path("NIFTY", DAY, "1545"))] and not sealed.late
    assert (
        reader.sealed("NIFTY", MONDAY, "1545").late and reader.sealed("NIFTY", DAY + timedelta(days=1), "1545") is None
    )
    assert [s.late for s in reader.live()] == [False, True]
    scores = root / "data" / scores_path(datetime(2026, 10, 16, 15, 50, tzinfo=IST), "ab" * 6)
    scores.parent.mkdir(parents=True)
    rows = [{"underlying": "NIFTY", "label": "live", "target_day": "2026-10-19"},
            {"underlying": "NIFTY", "label": "backfill_eod", "target_day": "2026-10-12"},
            {"underlying": "BANKNIFTY", "label": "live", "target_day": "2026-10-19"}]  # fmt: skip
    scores.write_text(json.dumps({"schema": "g13b_scores_v1", "rows": rows}))
    assert RangeScores(root).latest()["schema"] == "g13b_scores_v1" and list(reader.backfill()) == []
    assert len(RangeScores(root).rows("NIFTY")) == 2 and RangeScores(root).rows("NIFTY", live_only=True) == rows[:1]
    assert RangeScores(root).scored_days("NIFTY", MONDAY) == [MONDAY]
    assert RangeScores(root).scored_days("NIFTY", DAY) == []
    assert receipt_file(live_path("NIFTY", DAY, "1545")).startswith("receipts/data/price_ranges/v1/live/2026/10/")
