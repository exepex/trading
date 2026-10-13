from datetime import date

from fno.constants import FILING_RESULTS
from fno.filings.coverage import FilingsCoverage, half_year_misses, half_year_shares, half_years, quarter_ends
from fno.filings.coverage_cli import filings_coverage_lines
from fno.filings.filing import FilingGap
from fno.filings.manifest import FilingManifest
from fno.storage.raw_store import AreaStore, LocalFolderStore
from tests.filings.fakes import StepClock, archive, at, filing
from tests.filings.xbrl_fixtures import results_xbrl

FOLDER = "nse/equities/filings/results-xbrl"
TODAY = date(2023, 11, 20)  # only the September 2023 quarter is due


def build(tmp_path):
    store = archive(tmp_path, StepClock())
    store.save(filing("A", "A1.xml", at(9)), results_xbrl())
    store.save(filing("B", "B1.xml", at(9), period=date(2025, 6, 30)), results_xbrl(half_year=False))
    gaps = [FilingGap("C", FILING_RESULTS, "NSE lists no results-xbrl filing made public since 2023-10-01")]
    return FilingsCoverage(LocalFolderStore(tmp_path / "drive"), FilingManifest(tmp_path / "manifests"), gaps)


def test_counts_companies_files_and_checks_each_copy(tmp_path):
    (result, *_) = build(tmp_path).run(["A", "B", "C"], TODAY, {"A", "B", "C"}, [FILING_RESULTS])
    assert (result.companies, result.covered, result.files, result.present) == (3, 2, 2, 2)
    assert result.ok and [g.symbol for g in result.gaps] == ["C"]
    missing = [line.split(": ", 1) for line in result.missing_periods]  # the only quarter due is September 2023
    assert [symbol for symbol, _ in missing] == ["A", "B", "C"] and "quarter ended 2023-09-30" in missing[0][1]


def test_a_changed_copy_is_damaged_and_an_unlisted_file_unfingerprinted(tmp_path):
    coverage = build(tmp_path)
    (tmp_path / "drive" / FOLDER / "A" / "2025" / "A1.xml").write_bytes(b"other bytes")
    (tmp_path / "drive" / FOLDER / "B" / "2025" / "PLANTED.xml").write_bytes(b"x")
    (tmp_path / "drive" / FOLDER / "B" / "OLD.xml").write_bytes(b"x")  # the trial's layout, before year folders
    (result,) = coverage.run(["A", "B", "C"], TODAY, {"A", "B", "C"}, [FILING_RESULTS])
    assert result.damaged == ["A/2025/A1.xml: MD5 differs"] and result.unfingerprinted == ["B/2025/PLANTED.xml"]
    assert result.outside_layout == ["B/OLD.xml"]
    lines = filings_coverage_lines([result], {})
    assert lines[-1].startswith("result: INCOMPLETE")


def test_area_store_lists_inside_its_area(tmp_path):
    (tmp_path / "raw" / "x").mkdir(parents=True)
    (tmp_path / "raw" / "x" / "f.xml").write_bytes(b"abc")
    assert AreaStore(LocalFolderStore(tmp_path), "raw").checksums("x") == {"f.xml": "900150983cd24fb0d6963f7d28e17f72"}
    assert LocalFolderStore(tmp_path).checksums("missing") == {}


def test_half_years_are_those_whose_deadline_passed():
    assert half_years(date(2026, 10, 13)) == [
        date(2026, 3, 31), date(2025, 9, 30), date(2025, 3, 31), date(2024, 9, 30), date(2024, 3, 31), date(2023, 9, 30)
    ]  # fmt: skip
    assert half_years(date(2026, 11, 20))[0] == date(2026, 9, 30)  # 45 days after September have passed


def test_half_year_share_needs_balance_sheet_and_cash_flow(tmp_path):
    build(tmp_path)
    shares = half_year_shares(FilingManifest(tmp_path / "manifests"), ["A", "B"], [date(2025, 9, 30)])
    assert shares == {date(2025, 9, 30): 0.5}
    misses = half_year_misses(FilingManifest(tmp_path / "manifests"), ["A", "B", "C"], date(2025, 9, 30))
    assert misses == {"B": "no results file", "C": "no results file"}


def test_quarters_due_follow_sebi_deadlines():
    assert quarter_ends(date(2024, 5, 30), "results-xbrl")[-1] == date(2023, 12, 31)  # March needs 60 days
    assert quarter_ends(date(2024, 5, 31), "results-xbrl")[-1] == date(2024, 3, 31)
    assert quarter_ends(date(2024, 4, 22), "shareholding-xbrl")[-1] == date(2024, 3, 31)  # 21 days


def test_a_company_not_fetched_yet_is_pending_never_a_gap_on_nse(tmp_path):
    """Judge, 13 Oct 2026: before the queue reaches a company, coverage must not say NSE has no filing for it."""
    (result,) = build(tmp_path).run(["A", "B", "C"], TODAY, {"A"}, [FILING_RESULTS])
    assert result.pending == ["B", "C"]
    assert [line.split(":")[0] for line in result.missing_periods] == ["A"]  # only a list read in full may say so
    lines = filings_coverage_lines([result], {})
    assert "results-xbrl: 2 companies not fetched yet (the work queue has not reached them)" in lines
    assert not any(line.startswith(("no file B", "no file C")) for line in lines)
