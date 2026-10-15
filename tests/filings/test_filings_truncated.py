"""Judge 51 addendum 5: NSE itself serves a truncated XBRL file (LAURUSLABS, 23 Oct 2025: 65,258 bytes, cut off
mid-tag, identical on two downloads). It is never stored, and it is recorded as a gap with its size and SHA-256, so
the company finishes instead of failing on every run. A second download that differs or fails is a download fault
(a failure, retried). An error page is a refusal, never a gap."""

import hashlib

import pytest

from fno.filings.xbrl import NotXbrl, TruncatedXbrl, read_facts
from fno.storage.raw_source import RawFileRefused, RawSourceUnavailable
from tests.filings.fakes import FakeIndex, FakeXbrlHost, at, filing
from tests.filings.test_filings_librarian import run
from tests.filings.xbrl_fixtures import results_xbrl

CUT = results_xbrl()[:-120]  # an XBRL instance cut off near its end, as NSE served LAURUSLABS's


class ChangingHost(FakeXbrlHost):
    """Serves each name's answers in turn (bytes, or an exception to raise)."""

    def __init__(self, answers: dict[str, list]):
        super().__init__({})
        self.answers = {name: list(values) for name, values in answers.items()}

    def fetch(self, path: str):
        name = path.rsplit("/", 1)[-1]
        self.fetched.append(name)
        answer = self.answers[name].pop(0) if len(self.answers[name]) > 1 else self.answers[name][0]
        if isinstance(answer, Exception):
            raise answer
        return answer


def index():
    return FakeIndex({"LAURUSLABS": [filing("LAURUSLABS", "CUT.xml", at(23))]})


def test_a_file_nse_serves_cut_off_twice_is_a_gap_with_its_size_and_sha256(tmp_path):
    host = FakeXbrlHost({"CUT.xml": CUT})
    report = run(tmp_path, index(), host, companies=("LAURUSLABS",))
    (gap,) = [g for g in report.gaps if "truncated" in g.reason]
    assert f"{len(CUT)} bytes, SHA-256 {hashlib.sha256(CUT).hexdigest()}" in gap.reason
    assert "the same twice" in gap.reason and "not XML" in gap.reason
    assert report.complete and report.finished == ["LAURUSLABS"] and report.saved == 0
    assert host.fetched == ["CUT.xml", "CUT.xml"] and not (tmp_path / "drive").exists()


@pytest.mark.parametrize(
    ("second", "said"),
    [
        (results_xbrl()[:-60], "a second download differed"),
        (RawFileRefused("NSE filings archive: CUT.xml: HTTP 403 after 1 try", 403, 1), "the second download failed"),
    ],
    ids=["differs", "refused"],
)
def test_a_second_download_that_differs_or_fails_is_a_failure(tmp_path, second, said):
    report = run(tmp_path, index(), ChangingHost({"CUT.xml": [CUT, second]}), companies=("LAURUSLABS",))
    assert not report.complete and report.failed == {"LAURUSLABS"} and said in report.failures[0]
    assert not [g for g in report.gaps if "truncated" in g.reason]


def test_an_error_page_is_still_a_failure_and_is_not_downloaded_twice(tmp_path):
    host = FakeXbrlHost({"CUT.xml": b"<html><body>Access Denied<br></body></html>"})
    report = run(tmp_path, index(), host, companies=("LAURUSLABS",))
    assert report.failed == {"LAURUSLABS"} and host.fetched == ["CUT.xml"]


def test_a_fixed_copy_from_nse_is_saved_by_the_next_run(tmp_path):
    first = run(tmp_path, index(), FakeXbrlHost({"CUT.xml": CUT}), companies=("LAURUSLABS",))
    assert first.saved == 0
    second = run(tmp_path, index(), FakeXbrlHost({"CUT.xml": results_xbrl()}), companies=("LAURUSLABS",))
    assert second.saved == 1 and not [g for g in second.gaps if "truncated" in g.reason]


def test_only_a_cut_off_xbrl_instance_counts_as_truncated():
    with pytest.raises(TruncatedXbrl, match="not XML"):
        read_facts(CUT)
    with pytest.raises(NotXbrl) as page:
        read_facts(b"<html><body>Access Denied<br></body></html>")
    assert not isinstance(page.value, TruncatedXbrl)


def test_a_run_stopped_only_by_its_deadline_with_such_a_gap_needs_nothing_from_the_owner(tmp_path):
    """Point (b): the daily red runs came from this file's failure, not from the deadline. A run that only reached its
    time budget already exits 0 (`problem_of` is empty), and now the truncated file no longer fails it."""
    from fno.filings.runs_cli import problem_of

    companies = ("LAURUSLABS", "TCS", "INFY")
    report = run(tmp_path, index(), FakeXbrlHost({"CUT.xml": CUT}), companies=companies, minutes=4)
    assert report.stopped.startswith("deadline") and len(report.checked) < len(companies)
    assert "LAURUSLABS" in report.finished and not report.failures
    assert problem_of(report, "manifest rows committed and pushed (0 file(s))") == ""


def test_nse_unavailable_on_the_second_download_stops_the_run(tmp_path):
    down = RawSourceUnavailable("NSE filings archive: CUT.xml: HTTP 503 after 4 tries", 503, 4)
    report = run(tmp_path, index(), ChangingHost({"CUT.xml": [CUT, down]}), companies=("LAURUSLABS",))
    assert (
        report.stopped.startswith("NSE stopped answering at LAURUSLABS") and "HTTP 503 after 4 tries" in report.stopped
    )
