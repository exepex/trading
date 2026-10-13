from datetime import timedelta

import pytest

from fno.filings.manifest import FilingManifest
from fno.filings.results_table import ResultsTable
from fno.storage.raw_store import LocalFolderStore, StoredCopyDamaged
from tests.filings.fakes import StepClock, archive, at, filing
from tests.filings.xbrl_fixtures import results_xbrl

ORIGINAL, REVISED = results_xbrl(), results_xbrl().replace(b">1000<", b">1100<")


@pytest.fixture
def table(tmp_path):
    store = archive(tmp_path, StepClock())
    store.save(filing("TCS", "ORIGINAL.xml", at(9)), ORIGINAL)
    store.save(filing("TCS", "REVISED.xml", at(20)), REVISED)  # NSE lists a revision as a new filing (own link)
    return ResultsTable(FilingManifest(tmp_path / "manifests"), LocalFolderStore(tmp_path / "drive"))


def test_a_planted_early_read_never_sees_a_filing_before_it_was_public(table):
    assert table.as_of("TCS", at(9) - timedelta(seconds=1)) == []


def test_a_revised_filing_keeps_both_versions_and_each_moment_gets_its_own(table):
    (known_then,) = table.as_of("TCS", at(15))
    (known_now,) = table.as_of("TCS", at(21))
    assert known_then.figures.revenue == 1000 and known_then.url.endswith("ORIGINAL.xml")
    assert known_now.figures.revenue == 1100 and known_now.url.endswith("REVISED.xml")


def test_other_companies_and_standalone_rows_are_separate(table):
    assert table.as_of("INFY", at(21)) == [] and table.as_of("TCS", at(21), "standalone") == []


def test_a_changed_copy_in_the_store_is_refused(tmp_path, table):
    (tmp_path / "drive/nse/equities/filings/results-xbrl/TCS/REVISED.xml").write_bytes(ORIGINAL)
    with pytest.raises(StoredCopyDamaged):
        table.as_of("TCS", at(21))
