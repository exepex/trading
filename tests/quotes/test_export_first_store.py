"""Story A4b, judge 111 addendum 2: the replay's quote store decides per file: the export's own file first (git gives
the committed bytes), else the Drive-only store, hash-checked; it never writes."""

import pytest

from fno.quotes.drive_only_store import RawQuoteMissing
from fno.quotes.export_first_store import ExportFirstQuoteStore
from fno.storage.raw_store import LocalFolderStore, ReadOnlyStoreError
from tests.quotes.drive_fakes import FakeDrive, split_store

PATH = "groww/derivatives/quote-snapshots/2026/10/nifty_20261015_145500.csv"
SIDECAR = PATH.replace(".csv", ".meta.json")


def _store(tmp_path, drive):
    return ExportFirstQuoteStore(LocalFolderStore(tmp_path), split_store(tmp_path, drive))


def test_the_export_s_file_comes_first_and_drive_is_not_asked(tmp_path):
    (tmp_path / PATH).parent.mkdir(parents=True)
    (tmp_path / PATH).write_bytes(b"from git")
    assert _store(tmp_path, None).get(PATH) == b"from git"  # no Drive settings needed for it


def test_a_file_the_export_lacks_comes_from_drive_and_stays_checked(tmp_path):
    import hashlib
    import json

    (tmp_path / SIDECAR).parent.mkdir(parents=True)
    (tmp_path / SIDECAR).write_text(json.dumps({"csv_sha256": hashlib.sha256(b"rows").hexdigest()}))
    drive = FakeDrive()
    drive.files[PATH] = b"rows"
    assert _store(tmp_path, drive).get(PATH) == b"rows"
    drive.files.clear()
    with pytest.raises(RawQuoteMissing):
        _store(tmp_path, drive).get(PATH)


def test_no_file_and_no_sidecar_is_absent_and_the_store_never_writes(tmp_path):
    store = _store(tmp_path, FakeDrive())
    assert store.get(PATH) is None
    with pytest.raises(ReadOnlyStoreError):
        store.put(PATH, b"x")
