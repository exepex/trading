"""Story A4b: Groww's raw quote files go to the private store (Drive) only and are read back only when they hash to
their committed sidecar; sidecars, markers and NSE's public chain stay in the repository folder."""

import hashlib
import json
import subprocess

import pytest

from fno.config import ROOT
from fno.quotes.drive_only_store import RawQuoteHashMismatch, RawQuoteMissing, RawQuoteStoreUnavailable
from fno.quotes.recorder import DATASET, NSE_DATASET
from fno.storage import quote_wiring, wiring
from fno.storage.raw_store import LocalFolderStore
from tests.quotes.drive_fakes import SETTINGS, FakeDrive, split_store

FOLDER = f"{DATASET}/2026/10"
QUOTES, SIDECAR = f"{FOLDER}/nifty_20261013_145503.csv", f"{FOLDER}/nifty_20261013_145503.meta.json"
ROWS = b"snapshot_id,bid,ask\nnifty_20261013_145503,10,11\n"


def _sidecar(data: bytes = ROWS, **extra) -> bytes:
    return json.dumps({"csv_sha256": hashlib.sha256(data).hexdigest(), **extra}).encode()


def _saved(tmp_path, data: bytes = ROWS, **extra):
    drive = FakeDrive()
    store = split_store(tmp_path, drive)
    store.put(QUOTES, data)
    store.put(SIDECAR, _sidecar(data, **extra))
    return store, drive


def test_a_groww_quote_file_goes_to_the_private_store_only(tmp_path):
    store, drive = _saved(tmp_path)
    assert drive.files == {QUOTES: ROWS}
    assert not list(tmp_path.rglob("*.csv"))
    assert (tmp_path / SIDECAR).is_file() and store.get(QUOTES) == ROWS


def test_sidecars_markers_and_nse_files_stay_in_the_repository(tmp_path):
    drive = FakeDrive()
    store = split_store(tmp_path, drive)
    nse = f"{NSE_DATASET}/2026/10/nifty_20261013_145503.csv"
    for path in (nse, f"{FOLDER}/nifty_20261013.canonical", SIDECAR):
        store.put(path, b"x")
        assert (tmp_path / path).read_bytes() == b"x" and store.get(path) == b"x"
    assert drive.files == {}


def test_only_csv_files_of_the_groww_dataset_are_raw(tmp_path):
    store = split_store(tmp_path, FakeDrive())
    assert store.is_raw(QUOTES)
    assert not store.is_raw(SIDECAR) and not store.is_raw(f"{NSE_DATASET}/2026/10/a.csv")
    assert not store.is_raw(f"other/{DATASET}/2026/10/a.csv") and not store.is_raw(f"{FOLDER}/a.csv.part")


def test_a_one_byte_change_in_the_private_copy_is_refused(tmp_path):
    store, drive = _saved(tmp_path)
    drive.files[QUOTES] = ROWS.replace(b"11", b"12")
    with pytest.raises(RawQuoteHashMismatch, match="committed sidecar"):
        store.get(QUOTES)


def test_a_saved_file_missing_from_the_private_store_is_an_error_not_absent(tmp_path):
    store, drive = _saved(tmp_path)
    drive.files.clear()
    with pytest.raises(RawQuoteMissing):
        store.get(QUOTES)


def test_no_sidecar_or_an_unsaved_file_reads_as_absent(tmp_path):
    store = split_store(tmp_path, FakeDrive())
    assert store.get(QUOTES) is None  # no sidecar: no such attempt
    store.put(SIDECAR, _sidecar(raw_file_saved=False))
    assert store.get(QUOTES) is None  # the attempt's quote file was never saved


def test_an_empty_quote_file_with_its_hash_is_returned_empty(tmp_path):
    store, _ = _saved(tmp_path, b"")
    assert store.get(QUOTES) == b""


def test_without_drive_settings_raw_files_can_be_neither_saved_nor_read(tmp_path):
    store = split_store(tmp_path, None)
    with pytest.raises(RawQuoteStoreUnavailable, match="FNO_GDRIVE_OAUTH_REFRESH_TOKEN"):
        store.put(QUOTES, ROWS)
    assert not list(tmp_path.rglob("*.csv"))  # never falls back to the repository
    store.put(SIDECAR, _sidecar())
    with pytest.raises(RawQuoteStoreUnavailable):
        store.get(QUOTES)


def test_building_the_store_never_signs_in(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(quote_wiring, "build_owner_drive", lambda env: calls.append(1) or FakeDrive())
    store = wiring.build_quote_store(tmp_path)
    store.put(SIDECAR, b"{}")
    store.get(SIDECAR)
    assert calls == []  # sidecars and markers need no Drive
    store.put(QUOTES, ROWS)
    store.get(QUOTES.replace("145503", "150000"))
    assert calls == [1]  # signed in once, on the first raw quote file


def test_the_app_store_without_settings_names_them_never_their_values(tmp_path):
    secret = "planted-secret-value"
    store = quote_wiring.build_drive_only_quote_store(tmp_path, env={"FNO_GDRIVE_OAUTH_CLIENT_SECRET": secret})
    with pytest.raises(RawQuoteStoreUnavailable) as error:
        store.put(QUOTES, ROWS)
    assert SETTINGS in str(error.value) and secret not in str(error.value)


def test_the_app_store_puts_raw_files_in_drives_raw_area(tmp_path, monkeypatch):
    drive = FakeDrive()
    monkeypatch.setattr(quote_wiring, "build_owner_drive", lambda env: drive)
    store = wiring.build_quote_store(tmp_path)
    store.put(QUOTES, ROWS)
    assert drive.files == {f"raw/{QUOTES}": ROWS}
    assert isinstance(store.repository, LocalFolderStore) and store.repository.folder == tmp_path


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def test_no_groww_quote_file_is_tracked_in_the_repository():
    tracked = _git("ls-files", "research/data/quotes/groww").stdout.split()
    assert tracked and not [path for path in tracked if path.endswith(".csv")]


def test_git_ignores_groww_quote_files_but_not_nse_ones():
    groww = f"research/data/quotes/{FOLDER}/nifty_20261015_145500.csv"
    nse = f"research/data/quotes/{NSE_DATASET}/2026/10/nifty_20261015_145500.csv"
    assert _git("check-ignore", "-q", groww).returncode == 0
    assert _git("check-ignore", "-q", nse).returncode == 1
    assert _git("check-ignore", "-q", groww.replace(".csv", ".meta.json")).returncode == 1
