from datetime import datetime

import pytest

from fno.constants import FILING_RESULTS
from fno.filings.filing import FilingGap
from fno.filings.gaps import GapLog
from fno.filings.librarian import FilingsReport
from fno.filings.manifest import ArchivedFiling, FilingManifest
from fno.filings.runs import RunLog
from fno.models import IST
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


def test_run_log_knows_the_last_complete_run(tmp_path):
    runs = RunLog(tmp_path / "runs.csv")
    assert runs.last_complete(2) is None
    runs.append(SEEN, SEEN.replace(hour=10), FilingsReport(companies=2, checked=["A", "B"]))
    runs.append(SEEN, SEEN.replace(hour=11), FilingsReport(companies=2, checked=["A"]))  # incomplete
    runs.append(SEEN, SEEN.replace(hour=12), FilingsReport(companies=1, checked=["A"]))  # a trial over one symbol
    assert runs.last_complete(2) == SEEN.replace(hour=10)


def test_one_line_run_report_names_progress_or_the_problem():
    from fno.filings.runs_cli import _problem, _run_line

    stopped = FilingsReport(companies=501, checked=["A"] * 300, saved=11000, stopped="deadline reached")
    assert _problem(stopped) == ""  # the time limit needs nobody
    assert _run_line(stopped, "").endswith(
        "300 of 501 companies checked, 11000 files saved, 0 gaps with reasons; continues in the next run"
    )
    failed = FilingsReport(companies=2, checked=["A", "B"], failures=["A: NSE results list not read: timeout"])
    assert "A: NSE results list not read" in _run_line(failed, _problem(failed))
