"""Judge 66 / P8: flows copies are now filed under the session they cover, in their own series. Tonight's take of
14 Oct is not blocked by the run-dated 14/ copy (which covers 13 Oct); a copy of a later session than the run's day is
refused; a session keeps its first copy; the reader takes each session once, by-session first, never a later one."""

from datetime import date
from pathlib import Path

import pytest

from fno.market_read_models.frame_inputs import FlowsReader
from fno.storage import wiring
from fno.storage.content_checks import COVERED_SESSION, VALIDATORS
from fno.storage.manifest_folder import FingerprintingStore, ManifestFolder
from fno.storage.raw_store import LocalFolderStore
from fno.storage.session_filed_taker import SessionFiledTaker
from fno.storage.snapshot_source import (
    FiiDiiCashBySessionSource,
    FiiDiiCashSource,
    NsdlFpiDailyBySessionSource,
    NsdlFpiDailySource,
)
from fno.storage.snapshot_taker import TAKEN, SnapshotTaker
from fno.storage.wiring import RAW_SOURCES, build_session_calendar

FIXTURES = Path(__file__).parents[1] / "fixtures" / "flows"
CALENDAR = build_session_calendar()
D13, D14 = date(2026, 10, 13), date(2026, 10, 14)
CASH_13 = (FIXTURES / "fii-dii-cash_13102026.json").read_bytes()
CASH_14 = CASH_13.replace(b"13-Oct-2026", b"14-Oct-2026").replace(b"-1305.13", b"-900.00")
NSDL_13 = (FIXTURES / "fpi-daily-latest_13102026.html").read_bytes()


class Serving:
    """NSE's latest-day API serving `data` (the URL does not depend on the day)."""

    FILENAME, path_for = FiiDiiCashBySessionSource.FILENAME, FiiDiiCashBySessionSource.path_for

    def __init__(self, data):
        self.data, self.asked = data, []

    def fetch(self, path):
        self.asked.append(path)
        return self.data


def taker(store, data) -> SessionFiledTaker:
    source = FiiDiiCashBySessionSource
    return SessionFiledTaker(store, Serving(data), VALIDATORS[source], COVERED_SESSION[source])


def test_tonights_take_of_14_oct_is_filed_under_14_not_blocked_by_the_old_14_copy(tmp_path):
    store = LocalFolderStore(tmp_path)
    store.put(FiiDiiCashSource.path_for(D14), CASH_13)  # the run-dated 14/ copy, covering 13 Oct (as archived)
    line = taker(store, CASH_14).take(D14)
    assert line == TAKEN.format(path=FiiDiiCashBySessionSource.path_for(D14), size=len(CASH_14))
    assert store.get(FiiDiiCashBySessionSource.path_for(D14)) == CASH_14
    assert store.get(FiiDiiCashSource.path_for(D14)) == CASH_13  # the old copy is untouched


def test_a_copy_is_filed_under_the_session_it_covers_even_when_taken_the_next_day(tmp_path):
    store = LocalFolderStore(tmp_path)
    taker(store, CASH_13).take(D14)  # 14 Oct, before NSE's evening release: still 13 Oct's values
    assert store.get(FiiDiiCashBySessionSource.path_for(D13)) == CASH_13
    assert store.get(FiiDiiCashBySessionSource.path_for(D14)) is None  # the 14 Oct folder stays free


def test_a_copy_of_a_later_session_than_the_run_day_is_refused(tmp_path):
    store = LocalFolderStore(tmp_path)
    with pytest.raises(ValueError, match="after the run's day 2026-10-13; refused"):
        taker(store, CASH_14).take(D13)
    assert store.get(FiiDiiCashBySessionSource.path_for(D14)) is None


def test_a_session_keeps_its_first_copy(tmp_path):
    store = LocalFolderStore(tmp_path)
    taker(store, CASH_14).take(D14)
    revised = CASH_14.replace(b"-900.00", b"-950.00")
    assert "already archived" in taker(store, revised).take(D14)
    assert store.get(FiiDiiCashBySessionSource.path_for(D14)) == CASH_14


def test_the_reader_takes_each_session_once_by_session_first_never_a_later_folder(tmp_path):
    store = LocalFolderStore(tmp_path)
    for day in (D13, D14):  # the run-dated series as archived: 13/ and 14/, both covering 13 Oct
        store.put(FiiDiiCashSource.path_for(day), CASH_13)
        store.put(NsdlFpiDailySource.path_for(day), NSDL_13)
    store.put(FiiDiiCashBySessionSource.path_for(D14), CASH_14)  # tonight's copy
    store.put(NsdlFpiDailyBySessionSource.path_for(D13), NSDL_13)
    reader = FlowsReader(store, CALENDAR)
    on_13 = reader.on(D13)  # 13 Oct publishes from the run-dated series; the by-session 14/ is unread
    assert [(c.day, c.fii.net) for c in on_13.cash] == [(D13, -1305.13)] and reader.problems(D13, on_13) == []
    on_14 = reader.on(D14)
    assert [(c.day, c.fii.net) for c in on_14.cash] == [(D13, -1305.13), (D14, -900.0)]  # each session once
    by_session = {(c.dataset, c.session) for c in on_14.copies}
    assert ("nse/flows/fii-dii-cash-by-session", D14) in by_session
    assert ("nsdl/fpi/fpi-daily-by-session", D13) in by_session  # the by-session copy wins over the run-dated ones
    assert ("nsdl/fpi/fpi-daily", D13) not in by_session and len(on_14.nsdl) == 1
    assert reader.problems(D14, on_14) == []


def test_a_by_session_copy_gets_its_own_manifest_row(tmp_path):
    manifests = ManifestFolder(tmp_path / "manifests")
    store = FingerprintingStore(LocalFolderStore(tmp_path / "drive"), manifests, RAW_SOURCES)
    taker(store, CASH_14).take(D14)
    assert [f.day for f in manifests.read(FiiDiiCashBySessionSource)] == [D14]
    assert manifests.read(FiiDiiCashSource) == []  # never written into the run-dated series' manifest


def test_the_flows_datasets_are_taken_by_session_and_the_reference_lists_by_day(tmp_path, monkeypatch):
    monkeypatch.setattr(wiring, "build_owner_drive_store", lambda: LocalFolderStore(tmp_path))
    for name in ("fii-dii-cash-by-session", "fpi-daily-by-session"):
        assert isinstance(wiring.build_snapshot_taker(name), SessionFiledTaker)
    assert isinstance(wiring.build_snapshot_taker("equity-list"), SnapshotTaker)
