from datetime import datetime

import pytest

from fno.constants import FILING_RESULTS
from fno.filings.filing import FilingGap
from fno.filings.gaps import GapLog
from fno.filings.librarian import FilingsReport
from fno.filings.manifest import ArchivedFiling, FilingManifest
from fno.filings.progress import QUEUE, ProgressRecord
from fno.models import IST
from fno.storage.index_store import LocalIndexStore
from fno.storage.raw_store import RawFileConflict
from tests.filings.fakes import at, filing

SEEN = datetime(2026, 10, 13, 9, tzinfo=IST)


def row(sha: str) -> ArchivedFiling:
    return ArchivedFiling(filing("TCS", "A.xml", at(9)), SEEN, sha, "md5", 10, True, False)


def test_rows_are_appended_read_back_and_never_changed(tmp_path):
    manifest = FilingManifest(tmp_path)
    manifest.record(row("aa"))
    manifest.record(row("aa"))  # the same file again changes nothing
    with pytest.raises(RawFileConflict):
        manifest.record(row("bb"))
    (back,) = FilingManifest(tmp_path).rows(FILING_RESULTS).values()
    assert back == row("aa")
    assert len((tmp_path / "results-xbrl.csv").read_text().splitlines()) == 2


def test_gap_log_replaces_only_the_companies_checked(tmp_path):
    log = GapLog(tmp_path / "gaps.csv")
    log.replace(["A", "B"], [FilingGap("A", "results-xbrl", "x"), FilingGap("B", "results-xbrl", "y")])
    log.replace(["A"], [])
    assert log.read() == [FilingGap("B", "results-xbrl", "y")]


def test_progress_follows_the_queue_and_resumes_from_drive(tmp_path):
    store = LocalIndexStore(tmp_path)
    progress = ProgressRecord(store)
    first, second = QUEUE
    assert progress.step() == first and progress.since(first, SEEN.date()).isoformat() == "2023-10-01"
    progress.finish_companies(first, ["A"])
    progress.finish_step_if_done(first, ["A", "B"])
    progress.record_run(first, SEEN, SEEN, FilingsReport(companies=2, checked=["A"]))
    progress.save({"files": 1, "bytes": 10})
    again = ProgressRecord(store)  # the next run reads the record back
    assert again.fetched() == {"A"}
    assert again.remaining(first, ["A", "B"]) == ["B"] and again.step() == first
    again.finish_companies(first, ["B"])
    again.finish_step_if_done(first, ["A", "B"])
    assert again.step() == second and again.remaining(second, ["A", "B"]) == ["A", "B"]
    again.finish_companies(second, ["A", "B"])
    again.finish_step_if_done(second, ["A", "B"])
    assert again.step() is None and again.since(None, SEEN.date()) < SEEN.date()  # daily: a year of lists
    assert again.last_daily_run() is None
    again.record_run(None, SEEN, SEEN, FilingsReport(companies=2, checked=["A", "B"]))
    assert again.last_daily_run() == SEEN


def test_one_line_run_report_names_progress_or_the_problem(tmp_path):
    from fno.filings.runs_cli import problem_of, run_line

    progress, step = ProgressRecord(LocalIndexStore(tmp_path)), QUEUE[0]
    progress.finish_companies(step, ["A"] * 1)
    stopped = FilingsReport(companies=2, checked=["A"], saved=10, bytes_saved=2_000_000_000, stopped="deadline")
    assert problem_of(stopped, "manifest rows committed and pushed (1 file(s))") == ""
    line = run_line(step, progress, ["A", "B"], stopped, {"files": 12, "bytes": 3_000_000_000}, "")
    assert line == (
        "Omenix F&O filings archive, step 1 last 3 years: 1 of 2 companies done; this run 10 files, 2.00 GB, "
        "0 failures; archive 12 files, 3.00 GB"
    )
    failed = FilingsReport(companies=2, checked=["A"], failures=["A: NSE results list not read: timeout"])
    assert "NSE results list not read" in problem_of(failed, "manifest rows: nothing new to commit")
    assert problem_of(stopped, "manifest rows NOT committed: push failed: x").startswith("manifest rows NOT")
