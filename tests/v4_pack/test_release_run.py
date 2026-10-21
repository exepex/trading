"""Story G10 part 2 (judge 282.2's condition): the release run's catch-up writes system_late for every scored session
since go-live without a release record in Drive (Drive decides, never the checkout); today's pack or, after 14:40,
system_late; a write-once refusal is named, never overwritten, never a crash."""

from datetime import date, datetime, timedelta

import pytest

from fno.models import IST
from fno.research_engine.implied_vol import Black76
from fno.research_engine.live_features import LiveAtmIvMinusRealised
from fno.storage.data_store import DataStore
from fno.storage.receipts import ReceiptFolder
from fno.v4_pack.builder import Built, PackBuilder
from fno.v4_pack.capture import CaptureSource, V4Capture
from fno.v4_pack.paths import pack_path, release_path
from fno.v4_pack.release import parse_release
from fno.v4_pack.release_run import NOT_LIVE, ReleaseRun
from tests.v4_pack.capture_fixture import DAY, meta, rows
from tests.v4_pack.test_release import FakeDrive

MON, TUE, WED = date(2026, 10, 19), date(2026, 10, 20), date(2026, 10, 21)  # WED is "today" in the catch-up tests


class Capture(CaptureSource):
    def __init__(self, found=None):
        self.found = found

    def capture(self, day):
        return self.found


class NoPack:
    def build(self, day, capture):
        return Built(None, ("no canonical v4 capture",))


def weekdays(first, last):
    return [
        first + timedelta(days=n) for n in range((last - first).days + 1) if (first + timedelta(days=n)).weekday() < 5
    ]


def run_for(tmp_path, now, live_from=MON, builder=None, capture=None, drive=None):
    drive = drive or FakeDrive()
    store = DataStore(drive, "data", ReceiptFolder(tmp_path / "receipts"), "v4-release", "run-1")
    release = ReleaseRun(store, lambda path: drive.get(path) is not None, capture or Capture(), builder or NoPack(),
                         weekdays, live_from, lambda: now)  # fmt: skip
    return release, drive


def at(day, hh, mm, ss=0):
    return datetime(day.year, day.month, day.day, hh, mm, ss, tzinfo=IST)


def label(drive, day):
    return parse_release(day.isoformat(), drive.files[f"data/{release_path(day)}"]).label


def test_before_go_live_nothing_is_written(tmp_path):
    release, drive = run_for(tmp_path, at(WED, 15, 0), live_from=None)
    assert release.run(WED) == [NOT_LIVE] and drive.files == {}
    release, drive = run_for(tmp_path, at(WED, 15, 0), live_from=date(2026, 10, 22))
    assert release.run(WED) == [NOT_LIVE] and drive.files == {}


def test_the_catch_up_settles_every_missed_session_since_go_live_and_drive_decides(tmp_path):
    drive = FakeDrive()
    drive.files[f"data/{release_path(TUE)}"] = b"released earlier, its receipt not in this checkout"
    release, drive = run_for(tmp_path, at(WED, 15, 0), drive=drive)
    lines = release.run(WED)
    assert lines[0] == "v4 release 2026-10-19: system_late (catch-up: no release record in Drive)"
    assert label(drive, MON) == "system_late" and not release.refused
    assert drive.files[f"data/{release_path(TUE)}"].startswith(b"released earlier")  # never overwritten
    assert lines[-1].startswith("v4 release 2026-10-21: system_late (no canonical v4 capture")  # after 14:40


def test_a_run_twice_writes_nothing_new(tmp_path):
    release, drive = run_for(tmp_path, at(WED, 15, 0))
    release.run(WED)
    before = dict(drive.files)
    assert release.run(WED)[-1] == "v4 release 2026-10-21: already released" and drive.files == before


def test_before_the_window_closes_a_missing_pack_waits_and_writes_nothing_for_today(tmp_path):
    release, drive = run_for(tmp_path, at(WED, 14, 40, 0), live_from=WED)
    assert release.run(WED) == ["v4 release 2026-10-21: no complete pack yet (no canonical v4 capture); not released "
                                "before 14:40"] and drive.files == {}  # fmt: skip


def test_a_write_once_refusal_is_named_and_the_run_goes_on(tmp_path):
    drive = FakeDrive()
    drive.files[f"data/{pack_path(DAY)}"] = b"another pack already here"
    builder = PackBuilder(
        LiveAtmIvMinusRealised(None, 0.065, Black76()), "m/sha256:" + "e" * 64, lambda: at(DAY, 14, 41)
    )
    capture = Capture(V4Capture("groww/derivatives/quote-snapshots-v4", "nifty_20261022_143100", meta(), tuple(rows())))
    release, drive = run_for(tmp_path, at(DAY, 14, 41), live_from=DAY, builder=builder, capture=capture, drive=drive)
    assert release.run(DAY) == ["v4 release 2026-10-22: REFUSED by the write-once store (RawFileConflict); nothing "
                                "overwritten"] and release.refused  # fmt: skip
    assert drive.files[f"data/{pack_path(DAY)}"] == b"another pack already here"


def test_a_complete_capture_releases_an_a_pack(tmp_path):
    builder = PackBuilder(
        LiveAtmIvMinusRealised(None, 0.065, Black76()), "m/sha256:" + "e" * 64, lambda: at(DAY, 14, 32)
    )
    capture = Capture(V4Capture("groww/derivatives/quote-snapshots-v4", "nifty_20261022_143100", meta(), tuple(rows())))
    release, drive = run_for(tmp_path, at(DAY, 14, 32), live_from=DAY, builder=builder, capture=capture)
    assert release.run(DAY) == ["v4 release 2026-10-22: A"] and label(drive, DAY) == "A"
    assert f"data/{pack_path(DAY)}" in drive.files


@pytest.mark.parametrize("today", [date(2026, 10, 24)])  # a Saturday: not a scored session
def test_a_closed_day_releases_nothing_for_itself(tmp_path, today):
    release, drive = run_for(tmp_path, at(today, 15, 0), live_from=date(2026, 10, 23))
    lines = release.run(today)
    assert lines == ["v4 release 2026-10-23: system_late (catch-up: no release record in Drive)"]


def test_the_iv30_method_names_g1_v2s_live_rule_and_hashes_its_files():
    from fno.v4_pack.wiring import IV30_METHOD, iv30_method

    name, _, digest = iv30_method().partition("/sha256:")
    assert name == IV30_METHOD and len(digest) == 64 and set(digest) <= set("0123456789abcdef")
