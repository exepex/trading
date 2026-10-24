"""G13b's self-review findings (response 290), each with its test: seals recorded once while GitHub's 7-day log has
them (1); a close-table or closes failure never costs NIFTY's issue (2); a late index-close file fills its day (3);
back-fills never count twice and methods are never pooled (4); regular sessions only (6); the 2% line in log terms
(8); late rows counted as ok rows only (9); a calendar gap at the stale check is a reason, never a crash (11)."""

import gzip
import json
import math
from datetime import date, datetime, time, timedelta

from fno.health.model import EvidenceNotCommitted
from fno.models import IST
from fno.price_ranges.bhavcopy_chains import BhavcopyChains
from fno.price_ranges.build import CAPTURE
from fno.price_ranges.closes import IndexFileCloses, table_rows
from fno.price_ranges.folders import seal_path
from fno.price_ranges.forecasters import RangeInputs
from fno.price_ranges.reader import RangeForecasts, receipt_file
from fno.price_ranges.scores import group_scores, resolved
from fno.price_ranges.sealing import SealCheck
from fno.price_ranges.seals import EXPIRED, Seals, seal_recent
from fno.price_ranges.tables import CloseTables
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.drive_cache import DriveCache
from tests.price_distribution.builders import DAY, Chains, chain_day, drive_store
from tests.price_ranges.builders import CALENDAR, builder, closes, daily_files, index_close_file
from tests.price_ranges.test_issuer import issuer

PUSHED = datetime(2026, 10, 16, 15, 52, tzinfo=IST)


class Pushes:
    """The push evidence as a fake: it knows only what it is given (no commit adds anything else), and counts the
    questions."""

    def __init__(self, known=None):
        self.known, self.asked = dict(known or {}), 0

    def __call__(self, path):
        self.asked += 1
        if path not in self.known:
            raise EvidenceNotCommitted("no commit adding it")
        return self.known[path]


def seals(tmp_path, pushes, now):
    store, drive, _ = drive_store(tmp_path)
    return Seals(SealCheck(pushes, CALENDAR), store, receipt_file, lambda: now), drive


def test_a_known_push_is_stored_once_and_never_asked_again(tmp_path):
    from fno.price_ranges.folders import live_path

    pushes = Pushes({receipt_file(live_path("NIFTY", DAY, "1545")): PUSHED})
    found, drive = seals(tmp_path, pushes, PUSHED + timedelta(days=1))
    assert found.record("NIFTY", DAY, "1545").startswith("NIFTY 2026-10-16 1545: seal stored (sealed at")
    assert found.record("NIFTY", DAY, "1545") is None and pushes.asked == 1
    later = Seals(SealCheck(Pushes(), CALENDAR), found.store, receipt_file, lambda: PUSHED + timedelta(days=40))
    assert later.seal("NIFTY", DAY, "1545").sealed_at == PUSHED  # weeks later, GitHub's log no longer has it
    assert f"data/{seal_path('NIFTY', DAY, '1545')}" in drive.files


def at_16(day):
    return datetime.combine(day, time(16), IST)


def test_a_receipt_never_committed_waits_inside_the_week_then_is_stored_late(tmp_path):
    found, drive = seals(tmp_path, Pushes(), at_16(DAY + timedelta(days=7)))
    assert "seal pending" in found.record("NIFTY", DAY, "1545") and not drive.files
    expired, drive = seals(tmp_path / "b", Pushes(), at_16(DAY + timedelta(days=8)))
    assert "seal stored (late)" in expired.record("NIFTY", DAY, "1545")
    stored = json.loads(next(iter(drive.files.values())))
    assert stored["late"] and stored["reason"].startswith(EXPIRED.split("{")[0])


def test_seal_recent_covers_the_last_eight_days_of_live_issues(tmp_path):
    asked = []
    found, _ = seals(tmp_path, Pushes(), at_16(DAY))
    found.record = lambda u, d, issue: asked.append((u, d)) or None
    seal_recent(found, lambda u, d, issue: True, ("NIFTY",), "1545", DAY + timedelta(days=8))
    assert [d for _, d in asked] == [DAY + timedelta(days=8 - k) for k in range(1, 9)]


def test_a_failing_close_table_update_never_costs_niftys_issue(tmp_path):
    built, drive, _ = issuer(tmp_path)

    def broken(day):
        raise RuntimeError("the Drive cache could not verify the close tables")

    built.before = broken
    code, lines = built.issue(DAY)
    assert code == 1 and "close tables or seals not updated (RuntimeError)" in lines[-1]
    assert len(drive.files) == 2  # both underlyings still issued


def test_a_failing_closes_read_is_that_underlyings_retry_only(tmp_path):
    built, drive, _ = issuer(tmp_path)
    history = closes()

    def closes_of(underlying):
        if underlying == "BANKNIFTY":
            raise RuntimeError("the Drive cache could not verify the close tables")
        return history

    built.closes = closes_of
    code, lines = built.issue(DAY)
    assert code == 1 and "BANKNIFTY build failed (RuntimeError)" in lines[-1] and len(drive.files) == 1


def test_a_special_session_is_not_issued(tmp_path):
    special = date(2026, 11, 1)
    calendar = CsvSessionCalendar("date,kind,description,source_url\n"
                                  "2026-11-01,special,Test special,https://example.invalid\n")  # fmt: skip
    built, drive, _ = issuer(tmp_path, now=datetime(2026, 11, 1, 15, 45, tzinfo=IST), live_from=DAY)
    built.calendar = calendar
    assert built.issue(special) == (0, ["not a trading day"]) and not drive.files


def test_a_late_index_close_file_fills_its_day_on_the_next_update(tmp_path):
    mon, tue, wed = date(2026, 10, 19), date(2026, 10, 21), date(2026, 10, 22)  # the 20th is a holiday
    store, drive, receipts = drive_store(tmp_path)
    tables = CloseTables(store, receipts, DriveCache(drive, receipts, tmp_path / "cache"), first_day=mon)
    files = {mon: ("a.csv", index_close_file({"Nifty Bank": 51_000.0})),
             wed: ("c.csv", index_close_file({"Nifty Bank": 51_200.0}))}  # fmt: skip
    tables.update("BANKNIFTY", IndexFileCloses(daily_files(files), CALENDAR), wed)
    files[tue] = ("b.csv", index_close_file({"Nifty Bank": 51_100.0}))  # archived late
    assert tables.update("BANKNIFTY", IndexFileCloses(daily_files(files), CALENDAR), wed)[-1].startswith(
        "BANKNIFTY closes: 1 new rows")  # fmt: skip
    assert [r.day for r in table_rows(tables.latest_text("BANKNIFTY"))] == [mon, tue, wed]


def test_overlapping_backfills_count_once_and_methods_are_scored_apart(tmp_path):
    root = tmp_path / "cache"
    folder = root / "data" / "price_ranges" / "v1" / "backfill" / "backfill_eod_c0c0c0c0"
    folder.mkdir(parents=True)
    rec = {"label": "backfill_eod", "method_sha256": "c0" * 32, "underlying": "NIFTY", "day": "2026-10-16",
           "issue": "1545", "rows": []}  # fmt: skip
    for name, last in (("a.json.gz", "2026-10-16"), ("b.json.gz", "2026-10-19")):
        doc = {"schema": "g13b_backfill_v1", "last": last, "records": [rec]}
        (folder / name).write_bytes(gzip.compress(json.dumps(doc).encode()))
    assert len(list(RangeForecasts(root, None).backfill())) == 1
    row = {"forecaster": "rv20", "horizon": "N1", "status": "ok", "target_day": "2026-10-19", "s_ref": 100.0,
           "p_up": 0.5, "lq05": -0.02, "lq25": -0.01, "lq50": 0.0, "lq75": 0.01, "lq95": 0.02}  # fmt: skip
    records = [({**rec, "rows": [row]}, True), ({**rec, "method_sha256": "d1" * 32, "rows": [row]}, True)]
    assert len(group_scores(resolved(records, lambda u, d: 100.0)[0])) == 2


def test_late_rows_are_ok_rows_only():
    rows = [{"status": "ok"}, {"status": "missing"}, {"status": "not_eligible"}]
    assert resolved([({"rows": rows}, False)], lambda u, d: None) == ([], 1)


def test_the_two_percent_line_is_in_log_terms():
    from fno.price_distribution.chain import SpreadFilter
    from fno.price_distribution.valuation import value_day
    from fno.price_ranges.forecasters import ImpliedRange
    from tests.price_distribution.builders import NEAR, NEXT, RATE

    valuation = value_day(chain_day(), SpreadFilter(), RATE)
    out = ImpliedRange().forecast(RangeInputs(DAY, 22_990.0, 0.0, (), valuation, {NEAR: 6, NEXT: 25}), 1)
    near = valuation.usable()[0]
    found, forward = near.distribution.distribution, near.forward
    share, median = 1 / 6, math.log(found.quantile(0.5)[0] / forward)
    centre = share * (math.log(forward / 22_990.0) + median)

    def cdf(y):
        return found.cdf(forward * math.exp(median + (y - centre) / math.sqrt(share)))

    assert out.p_big_move == cdf(-0.02) + 1 - cdf(0.02)


def test_a_calendar_gap_at_the_stale_check_is_a_reason_not_a_crash():
    early = date(2026, 1, 1)  # the test calendar starts in 2026: the session before it is unknown
    record = builder().build("NIFTY", early, "1545", chain_day(day=early), closes(last=date(2025, 12, 31)), CAPTURE,
                             "live", None)  # fmt: skip
    by = {(r["forecaster"], r["horizon"]): r for r in record["rows"]}
    assert by[("rv20", "N1")]["status"] == "missing" and "calendar" in by[("rv20", "N1")]["reason"]
    assert Chains  # imported for the issuer helper's fakes


def test_the_back_fill_skips_a_special_session(tmp_path):
    from tests.price_ranges.test_backfill_and_reader import backfill

    special = date(2026, 11, 1)
    calendar = CsvSessionCalendar("date,kind,description,source_url\n"
                                  "2026-11-01,special,Test special,https://example.invalid\n")  # fmt: skip
    run, drive = backfill(tmp_path, source=Chains({("NIFTY", special): chain_day(day=special)}))
    run.calendar = calendar
    assert run.run("backfill_3pm", CAPTURE, ("NIFTY",), special, special) == ["NIFTY backfill_3pm: no day to write"]
    assert not drive.files


def test_the_bhavcopy_future_is_its_settlement_price_not_its_last_trade():
    from tests.price_ranges.test_bhavcopy_chains import DAY as FO_DAY
    from tests.price_ranges.test_bhavcopy_chains import NAME, fo_file

    lines = fo_file().decode().splitlines()
    header = lines[0].split(",")
    close, kind = header.index("ClsPric"), header.index("FinInstrmTp")
    for i, line in enumerate(lines[1:], 1):
        cells = line.split(",")
        if cells[kind] == "IDF":
            cells[close] = "50999.00"  # the last trade differs from the day's settlement
            lines[i] = ",".join(cells)
    data = ("\n".join(lines) + "\n").encode()
    chain = BhavcopyChains([daily_files({FO_DAY: (NAME, data)}, "udiff")]).chain("BANKNIFTY", FO_DAY)
    assert all(e.future == 51_000.0 for e in chain.expiries)
