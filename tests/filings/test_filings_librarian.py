from datetime import timedelta

from fno.constants import FILING_RESULTS
from fno.filings.filing import Filing
from fno.filings.librarian import FilingsLibrarian
from fno.filings.manifest import FilingManifest
from fno.http_pacing import SourceCoolingOff
from tests.filings.fakes import SINCE, FakeIndex, FakeXbrlHost, StepClock, archive, at, filing
from tests.filings.xbrl_fixtures import results_xbrl

FAR = timedelta(days=1)


def run(tmp_path, index, host, companies=("TCS",), minutes=None):
    clock = StepClock()
    librarian = FilingsLibrarian([index], host, archive(tmp_path, clock), clock, log=lambda line: None)
    deadline = clock.now + (FAR if minutes is None else timedelta(minutes=minutes))
    return librarian.run(list(companies), SINCE, deadline)


def test_saves_every_listed_file_with_its_manifest_row(tmp_path):
    index = FakeIndex({"TCS": [filing("TCS", "A.xml", at(9)), filing("TCS", "B.xml", at(10))]})
    host = FakeXbrlHost({"A.xml": results_xbrl(), "B.xml": results_xbrl(half_year=False)})
    report = run(tmp_path, index, host)
    assert report.complete and report.saved == 2
    stored = tmp_path / "drive" / "nse/equities/filings/results-xbrl/TCS/2025/A.xml"
    assert stored.read_bytes() == results_xbrl()
    rows = FilingManifest(tmp_path / "manifests").rows(FILING_RESULTS)
    row = rows["https://nsearchives.nseindia.com/corporate/xbrl/A.xml"]
    assert (
        row.filing.filed_at == at(9) and row.balance_sheet and row.cash_flow and row.size_bytes == stored.stat().st_size
    )
    assert rows["https://nsearchives.nseindia.com/corporate/xbrl/B.xml"].cash_flow is False


def test_a_stopped_run_restarts_only_what_is_missing(tmp_path):
    index = FakeIndex({s: [filing(s, f"{s}.xml", at(9))] for s in ("A", "B", "C")})
    host = FakeXbrlHost({f"{s}.xml": results_xbrl() for s in ("A", "B", "C")})
    first = run(tmp_path, index, host, companies=("A", "B", "C"), minutes=3)  # the deadline stops it part way
    assert first.stopped.startswith("deadline") and not first.complete and 0 < first.saved < 3
    host.fetched.clear()
    second = run(tmp_path, index, host, companies=("A", "B", "C"))
    assert second.complete and second.saved == 3 - first.saved and second.present == first.saved
    assert len(host.fetched) == 3 - first.saved  # nothing already archived is downloaded again


def test_gaps_are_listed_with_their_reason_never_skipped(tmp_path):
    no_file = Filing(FILING_RESULTS, "TCS", at(9).date(), at(9), "", "consolidated")
    index = FakeIndex({"TCS": [no_file, filing("TCS", "GONE.xml", at(10))]})
    report = run(tmp_path, index, FakeXbrlHost({}), companies=("TCS", "NEWCO"))
    reasons = sorted((g.symbol, g.reason) for g in report.gaps)
    assert [symbol for symbol, _ in reasons] == ["NEWCO", "TCS", "TCS", "TCS"]
    texts = " | ".join(reason for _, reason in reasons)
    assert "with no XBRL file" in texts and "answers 'not found'" in texts
    assert sum("lists no results-xbrl filing made public since 2023-10-01" in r for _, r in reasons) == 2
    assert report.complete  # gaps with reasons are not failures


def test_a_file_that_is_not_xbrl_is_never_saved_and_fails_the_run(tmp_path):
    index = FakeIndex({"TCS": [filing("TCS", "A.xml", at(9))]})
    report = run(tmp_path, index, FakeXbrlHost({"A.xml": b"<html>Access Denied</html>"}))
    assert report.failures and not report.complete and report.saved == 0
    assert not (tmp_path / "drive").exists()


def test_nse_refusing_us_stops_the_run_at_once(tmp_path):
    index = FakeIndex({}, error=SourceCoolingOff("www.nseindia.com refused requests (HTTP 403)"))
    report = run(tmp_path, index, FakeXbrlHost({}), companies=("A", "B"))
    assert "refused" in report.stopped and report.checked == [] and not report.complete


def test_a_list_nse_does_not_answer_is_a_failure_for_that_company_only(tmp_path):
    index = FakeIndex({}, error=RuntimeError("NSE returned an empty response"))
    report = run(tmp_path, index, FakeXbrlHost({}), companies=("A", "B"))
    assert len(report.failures) == 2 and report.checked == ["A", "B"] and not report.complete
