"""Story A16b, criteria 1, 5, 7, 8, 9 and 11: an unreadable answer, the printed report (void share, void sessions by
reason, pre-open gaps), `backfill-verify`, no price in any repository file, and nothing of A16's touched."""

import csv
import io
import re
from datetime import date

from fno.intraday.backfill_report import report_lines
from fno.intraday.nse_range import NseDay
from tests.intraday_backfill.fakes import (
    START,
    FakeGroww,
    FakeNse,
    build,
    levels,
    session_data,
    t,
    verifier,
)

WEEK = [date(2026, 9, 28), date(2026, 9, 29), date(2026, 9, 30), date(2026, 10, 1)]
PRICE_COLUMNS = {"open", "high", "low", "close", "level", "index_level", "price", "spot", "ltp", "bid", "ask"}


def _run(tmp_path, overrides=None):
    fifteen, minutes, nse = session_data(WEEK, overrides)
    backfill = build(tmp_path, FakeGroww(fifteen, minutes), FakeNse(nse))
    return backfill, backfill.run(START, WEEK[3])


def test_an_unreadable_answer_names_the_window_and_archives_and_derives_nothing(tmp_path):
    bad = [[t(WEEK[0], 9, 15) + "+05:30", 1, 1, 1, 1, None, None]]  # a time with an offset is `candle_parse`
    backfill, report = _run(tmp_path, {("15m", WEEK[0]): bad})
    assert report.deferred[WEEK[0]] == "window 2026-09-28..2026-10-01: CandleParse" and not report.complete
    assert backfill.archive.rows() == [] and backfill.table.rows() == []


def test_the_report_gives_the_void_share_every_void_session_by_reason_and_the_pre_open_gaps(tmp_path):
    values = levels(WEEK[2])
    gap = NseDay(values[0] - 3.1, max(values) + 1, min(values) - 1)  # pre-open close 0.10 above NSE's open
    backfill, report = _run(tmp_path, {("15m", WEEK[1]): [], ("nse", WEEK[2]): gap})
    lines = report_lines(report, backfill.table.rows(), backfill.deferrals.counts())
    assert "sessions 4: 4 written now, 0 held before, 0 deferred" in lines
    assert ("void 3 of 4 (75.0%) - above 5%: propose a new version (design 5.2); by reason: "
            "{'missing_candles': 1, 'no_previous_close': 2}") in lines  # fmt: skip
    assert "void missing_candles: 2026-09-29" in lines and "void no_previous_close: 2026-09-28, 2026-09-30" in lines
    assert "provenance: {'backfilled': 4}" in lines
    assert "pre-open gap above 0.05 on 1 of 3 sessions with a 1-minute answer: 2026-09-30" in lines
    assert backfill.table.row(WEEK[1])["nse_open_gap"] == ""  # voided before the 1-minute check: blank, not counted
    assert backfill.table.row(WEEK[2])["nse_open_gap"] == "0.10"


def test_a_clean_report_shows_no_flag_and_no_void_lines(tmp_path):
    backfill, report = _run(tmp_path)
    lines = report_lines(report, backfill.table.rows()[1:], backfill.deferrals.counts())
    assert [x for x in lines if x.startswith("void ")] == ["void 0 of 3 (0.0%); by reason: none"]


def test_verify_passes_a_clean_back_fill(tmp_path):
    backfill, _ = _run(tmp_path)
    assert verifier(backfill).problems() == []


def test_verify_names_a_planted_change_to_a_row(tmp_path):
    backfill, _ = _run(tmp_path)
    path = backfill.table.path(WEEK[2])
    path.write_text(path.read_text().replace(backfill.table.row(WEEK[2])["rv_intraday"], "0.0000000001"))
    assert verifier(backfill).problems() == [f"{WEEK[2]}: differs from its copies in rv_intraday"]


def _drive_file(tmp_path, backfill, kind):
    return tmp_path / "drive" / "raw" / backfill.table.row(WEEK[2])[f"copy_{kind}"]


def test_verify_names_a_copy_whose_sha_differs_from_its_manifest(tmp_path):
    backfill, _ = _run(tmp_path)
    copy = _drive_file(tmp_path, backfill, "1m")
    copy.write_bytes(copy.read_bytes() + b"x")
    assert verifier(backfill).problems() == [
        f"{WEEK[2]}: not verified: {backfill.table.row(WEEK[2])['copy_1m']}: SHA-256 differs from its manifest row"
    ]


def test_verify_names_a_copy_missing_from_drive_and_a_row_whose_copy_has_no_manifest_row(tmp_path):
    backfill, _ = _run(tmp_path)
    _drive_file(tmp_path, backfill, "1m").unlink()
    path = backfill.table.path(WEEK[3])
    held = backfill.table.row(WEEK[3])["copy_1m"]
    path.write_text(path.read_text().replace(held, held.replace(".json.gz", "x.json.gz")))
    problems = verifier(backfill).problems()
    assert problems[0] == f"{WEEK[2]}: not verified: {backfill.table.row(WEEK[2])['copy_1m']}: not in Drive"
    assert problems[1] == f"{WEEK[3]}: {held.replace('.json.gz', 'x.json.gz')} has no manifest row"


def _cells(path):
    rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8"))))
    return rows[0], [dict(zip(rows[0], row, strict=True)) for row in rows[1:]]


def test_no_repository_file_holds_a_price(tmp_path):
    fifteen, _, _ = session_data(WEEK)
    _run(tmp_path)
    prices = {float(v) for rows in fifteen.values() for row in rows for v in row[1:5]}
    repository = [p for p in tmp_path.rglob("*") if p.is_file() and "drive" not in p.relative_to(tmp_path).parts]
    assert {p.suffix for p in repository} == {".csv"} and len(repository) == 6  # 4 rows and the two manifests
    for path in repository:
        header, rows = _cells(path)
        assert not PRICE_COLUMNS & set(header), path.name
        for row in rows:
            numbers = {k: float(v) for k, v in row.items() if re.fullmatch(r"-?\d+(\.\d+)?", v) and k != "size"}
            assert not prices & set(numbers.values()), path.name
            assert not [k for k, n in numbers.items() if abs(n) > 100], (path.name, numbers)


def test_the_run_writes_only_its_own_folder_and_never_a16_s_files(tmp_path):
    backfill, _ = _run(tmp_path)
    repo = tmp_path / "repo"
    assert {p.relative_to(repo).parts[0] for p in repo.rglob("*") if p.is_file()} == {"rv-candle"}
    assert backfill.table.pattern.startswith("rv-candle/") and not (repo / "rv").exists()
