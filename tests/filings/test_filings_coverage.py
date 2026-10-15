import hashlib
from datetime import date

import pytest

from fno.constants import FILING_RESULTS
from fno.filings.coverage import (
    LISTED_AFTER,
    FilingsCoverage,
    half_year_misses,
    half_year_shares,
    half_years,
    quarter_ends,
)
from fno.filings.coverage_cli import filings_coverage_lines
from fno.filings.filing import FilingGap
from fno.filings.listing_dates import read_listing_dates
from fno.filings.manifest import FilingManifest
from fno.storage.raw_store import AreaStore, LocalFolderStore, StoredCopyDamaged
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
    shares = half_year_shares(FilingManifest(tmp_path / "manifests"), ["A", "B"], [date(2025, 9, 30)], {})
    assert shares == {date(2025, 9, 30): 0.5}
    misses = half_year_misses(FilingManifest(tmp_path / "manifests"), ["A", "B", "C"], date(2025, 9, 30), {})
    assert misses == {"B": "no results file", "C": "no results file"}


# NSE's EQUITY_L.csv header as published (leading spaces included); the companies and dates are made up.
EQUITY_L = (
    b"SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE\n"
    b"A,A Ltd,EQ,06-OCT-2008,10,1,INE000A00001,10\n"
    b"B,B Ltd,EQ,20-NOV-2025,10,1,INE000B00001,10\n"
    b"C,C Ltd,EQ,03-MAY-1995,10,1,INE000C00001,10\n"
    b"D,D Ltd,EQ,01-NOV-2025,10,1,INE000D00001,10\n"
)


def test_a_company_counts_from_its_listing_unless_it_filed_anyway(tmp_path):
    """Judge 51 addendum 8: B listed after September 2025 had no results to file; D (an IPO) listed after it but filed
    the quarter, so it counts as covered; C, listed long before, is a real miss."""
    build(tmp_path)
    archive(tmp_path, StepClock()).save(filing("D", "D1.xml", at(9)), results_xbrl())
    listed = read_listing_dates(EQUITY_L, "EQUITY_L.csv")
    assert listed["B"] == date(2025, 11, 20) and listed["C"] == date(1995, 5, 3)
    manifest, end = FilingManifest(tmp_path / "manifests"), date(2025, 9, 30)
    assert half_year_shares(manifest, ["A", "B", "C", "D"], [end], listed) == {end: 2 / 3}
    assert half_year_misses(manifest, ["A", "B", "C", "D"], end, listed) == {"B": LISTED_AFTER, "C": "no results file"}
    assert half_year_shares(manifest, ["A", "B", "C", "D"], [date(2026, 3, 31)], listed)[date(2026, 3, 31)] == 0.0


def test_an_equity_list_without_the_listing_column_is_refused():
    with pytest.raises(ValueError, match="DATE OF LISTING"):
        read_listing_dates(b"SYMBOL,NAME OF COMPANY\nA,A Ltd\n", "EQUITY_L.csv")


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


def test_the_archived_list_is_checked_against_its_own_days_manifest_row(tmp_path, monkeypatch):
    """NSE's EQUITY_L.csv changed on 14 Oct 2026 (manifest): the 13 Oct copy the coverage reads must still pass."""
    from fno.filings import wiring
    from fno.storage.manifest_folder import Fingerprint, ManifestFolder
    from fno.storage.snapshot_source import EquityListSource

    drive = LocalFolderStore(tmp_path / "drive")
    path = EquityListSource.path_for(wiring.NIFTY500_SNAPSHOT_DAY)
    drive.put(path, EQUITY_L)
    folder = ManifestFolder(tmp_path / "manifests")
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    sha = hashlib.sha256(EQUITY_L).hexdigest()
    folder.write(EquityListSource, [Fingerprint(wiring.NIFTY500_SNAPSHOT_DAY, url, sha, len(EQUITY_L)),
                                    Fingerprint(date(2026, 10, 14), url, "f" * 64, 1)])  # fmt: skip
    monkeypatch.setattr(wiring.storage, "build_owner_drive", lambda: drive)
    monkeypatch.setattr(wiring, "_owner_raw_area", lambda: drive)
    monkeypatch.setattr(wiring.storage, "build_manifest_folder", lambda: folder)
    assert wiring.build_listing_dates()["D"] == date(2025, 11, 1)
    (tmp_path / "drive" / path).write_bytes(EQUITY_L + b"Z,Z Ltd,EQ,01-JAN-2020,10,1,INE000Z00001,10\n")  # damaged
    with pytest.raises(StoredCopyDamaged):
        wiring.build_listing_dates()
