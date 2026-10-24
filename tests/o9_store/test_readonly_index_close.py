"""Readers of NSE's index-close files read the stores only (DR1 and DRY1 row b4, 24 Oct 2026): a day no store holds is
"not archived yet", never fetched from NSE and never archived to Drive. The librarian (index-closes.yml, the morning
routine) stays the one writer; the panel and the warm-up closes keep the writer's library."""

from datetime import date
from pathlib import Path

import pytest

from fno.storage import wiring
from fno.storage.raw_library import NOT_STORED, RawFile, StoredFilesLibrary
from fno.storage.raw_source import NseIndexCloseSource
from fno.storage.raw_store import LocalFolderStore

DAY, MISSING = date(2026, 10, 22), date(2026, 10, 23)
READERS = ("fno/forecast_lab/wiring.py", "fno/forecast_lab/page_wiring.py", "fno/price_ranges/wiring.py",
           "fno/close_read/wiring.py")  # fmt: skip


@pytest.fixture
def stored(tmp_path, monkeypatch):
    """One archived index-close file in a local store; NSE and every archive refuse to be reached."""
    store = LocalFolderStore(tmp_path)
    store.put(NseIndexCloseSource.path_for(DAY), b"Index Name,Closing Index Value\nNifty 50,25000\n")
    monkeypatch.setattr(wiring, "_reader_raw_stores", lambda env=None: [store])
    monkeypatch.setattr(NseIndexCloseSource, "fetch", lambda self, path: pytest.fail(f"fetched {path} from NSE"))
    monkeypatch.setattr(wiring, "build_nse_library", lambda *a, **k: pytest.fail("a fetching library was built"))
    return store


def test_the_library_gives_a_stored_file_and_names_a_missing_one_without_reaching_a_source(stored):
    library = StoredFilesLibrary([stored])
    assert library.get(NseIndexCloseSource.path_for(DAY)).data.startswith(b"Index Name")
    assert library.get(NseIndexCloseSource.path_for(MISSING)) == RawFile(None, NOT_STORED)


def test_the_readers_builder_reads_a_stored_day_and_never_fetches_a_missing_one(stored):
    files = wiring.build_stored_index_close_files()
    assert files.get(DAY)[1].startswith(b"Index Name") and files.get(MISSING)[1] is None


def test_g13s_close_table_update_reads_through_the_readers_builder(stored, monkeypatch):
    """G13's ask: the IndexFileCloses behind `pricerange closes` (and the issuer's, same builder) never archives."""
    from fno.price_ranges import wiring as g13

    monkeypatch.setattr(g13, "build_store", lambda *a, **k: None)
    monkeypatch.setattr(g13, "build_tables", lambda store: "tables")
    _, closes = g13.build_table_update()
    assert closes.files.get(DAY)[1] and closes.files.get(MISSING)[1] is None


def test_no_reader_wiring_builds_the_fetching_library():
    """FL1's ask for `build_composer` and the page (and the same for G13's issuer and A4h's Confirmer): each reader's
    composition root names only the reader's builder; the fetching one stays with the panel and the warm-up closes."""
    root = Path(__file__).resolve().parents[2]
    for module in READERS:
        text = (root / module).read_text(encoding="utf-8")
        assert "build_stored_index_close_files" in text and "build_index_close_files" not in text, module


def test_on_github_the_readers_only_store_is_the_owner_drives_raw_area(tmp_path, monkeypatch):
    """Judge 558 SF1: GitHub's jobs carry the four owner settings and no service account, so the owner's raw area is
    the reader's only store there; without it every reader would silently find no file."""
    from fno.constants import ENV_GDRIVE_SERVICE_ACCOUNT_JSON
    from fno.storage.raw_store import AreaStore

    owner_drive = LocalFolderStore(tmp_path)  # stands in for the owner's Drive (the real one signs in on use)
    monkeypatch.delenv(ENV_GDRIVE_SERVICE_ACCOUNT_JSON, raising=False)
    monkeypatch.setattr(wiring, "build_owner_drive", lambda env: owner_drive if env else None)
    owner = dict.fromkeys(wiring.OWNER_UPLOAD_SETTINGS, "set-for-the-test")
    (store,) = wiring._reader_raw_stores(owner)
    assert isinstance(store, AreaStore) and store.area == wiring.RAW_AREA and store.store is owner_drive
    assert wiring._reader_raw_stores({}) == []  # no settings at all: no store, never a guessed one
