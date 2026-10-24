"""G13 section 1 (judge-requested fallback, review finding 2): a source whose recorded chain cannot be read is passed
over and named, so NSE's chain is used when Groww's Drive file is unreadable; absent everywhere is None."""

from datetime import date
from pathlib import Path

import pytest

from fno.price_distribution.sources import ChainUnavailable, SnapshotChains
from fno.quotes.drive_only_store import RawQuoteStoreUnavailable
from fno.storage.raw_store import LocalFolderStore

ROOT = Path(__file__).resolve().parents[2]
DAY = date(2026, 10, 16)


class GrowwDown(LocalFolderStore):
    """The repository's files, but Groww's raw CSV (Drive only) cannot be read."""

    def get(self, path):
        if path.startswith("groww/") and path.endswith(".csv"):
            raise RawQuoteStoreUnavailable("Drive is down")
        return super().get(path)


def test_an_unreadable_groww_file_falls_back_to_nse_and_says_why():
    chain = SnapshotChains(GrowwDown(ROOT / "research" / "data" / "quotes")).chain("NIFTY", DAY)
    assert chain.source == "nse" and "groww raw quote file unreadable: Drive is down" in chain.source_note


def test_unreadable_everywhere_raises_and_absent_everywhere_is_none():
    with pytest.raises(ChainUnavailable, match="Drive is down"):
        SnapshotChains(GrowwDown(ROOT / "research" / "data" / "quotes"), ("groww",)).chain("NIFTY", DAY)
    assert SnapshotChains(LocalFolderStore(ROOT / "research" / "data" / "quotes")).chain("FINNIFTY", DAY) is None
