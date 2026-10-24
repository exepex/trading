"""Story G10 completion, criterion 4: release by 14:45:00 (decision D1) or the day is system_late; a system_late today
fails the release (decision D3, one switch) unless the composition root excuses it (a rehearsal of a day with no
recorded capture); a capture that has ended without a pack is final; a rerun after a failed write retries it."""

from datetime import date

import pytest

from fno.research_engine.implied_vol import Black76
from fno.research_engine.live_features import LiveAtmIvMinusRealised
from fno.v4_pack import release_run
from fno.v4_pack.builder import PackBuilder
from fno.v4_pack.capture import V4Capture
from fno.v4_pack.paths import release_path
from tests.v4_pack.capture_fixture import DAY, meta, rows
from tests.v4_pack.test_release import FakeDrive
from tests.v4_pack.test_release_run import Capture, at, label, run_for


def complete(now):
    builder = PackBuilder(LiveAtmIvMinusRealised(None, 0.065, Black76()), "m/sha256:" + "e" * 64, lambda: now)
    return builder, Capture(
        V4Capture("groww/derivatives/quote-snapshots-v4", "nifty_20261022_143100", meta(), tuple(rows()))
    )


@pytest.mark.parametrize(("second", "expected"), [(0, "A"), (1, "system_late")])
def test_a_release_at_14_45_00_is_a_and_at_14_45_01_is_system_late(tmp_path, second, expected):
    now = at(DAY, 14, 45, second)
    builder, capture = complete(now)
    release, drive = run_for(tmp_path, now, live_from=DAY, builder=builder, capture=capture)
    lines = release.run(DAY)
    assert label(drive, DAY) == expected and release.failed == (expected == "system_late")
    if expected == "system_late":
        assert lines == ["v4 release 2026-10-22: system_late (released late: after 14:45)"]


def test_a_good_day_releases_a_at_about_14_35_and_does_not_fail(tmp_path):
    builder, capture = complete(at(DAY, 14, 35))
    release, drive = run_for(tmp_path, at(DAY, 14, 35), live_from=DAY, builder=builder, capture=capture)
    assert release.run(DAY) == ["v4 release 2026-10-22: A"] and not release.failed


def test_a_capture_that_ended_without_a_pack_is_final_before_14_40(tmp_path):
    release, drive = run_for(tmp_path, at(DAY, 14, 36), live_from=DAY, capture=Capture(ended=True))
    assert release.run(DAY) == ["v4 release 2026-10-22: system_late (no canonical v4 capture)"]
    assert label(drive, DAY) == "system_late" and release.failed and release.late_today


@pytest.mark.parametrize("now", [(14, 36), (14, 42), (14, 45)])
def test_no_ended_capture_until_14_45_writes_nothing_and_fails(tmp_path, now):
    """A hand run while the recorder may still write its marker never settles the day (review finding 4)."""
    release, drive = run_for(tmp_path, at(DAY, *now), live_from=DAY)
    assert release.run(DAY)[-1].endswith("not released before 14:45") and drive.files == {} and release.failed


def test_a_capture_never_ended_by_14_45_is_system_late_and_named(tmp_path):
    release, drive = run_for(tmp_path, at(DAY, 14, 45, 1), live_from=DAY)
    assert release.run(DAY) == ["v4 release 2026-10-22: system_late (capture still running at 14:45)"]
    assert label(drive, DAY) == "system_late" and release.failed


def test_d3_is_one_switch(tmp_path, monkeypatch):
    monkeypatch.setattr(release_run, "SYSTEM_LATE_FAILS", False)
    release, _ = run_for(tmp_path, at(DAY, 15, 0), live_from=DAY)
    release.run(DAY)
    assert release.late_today and not release.failed


def test_an_excused_system_late_is_written_with_its_note_and_is_no_failure(tmp_path):
    release, drive = run_for(tmp_path, at(DAY, 15, 0), live_from=DAY)
    release.excused = lambda day: "rehearsal: no v4 capture recorded for this day"
    assert release.run(DAY) == ["v4 release 2026-10-22: system_late (rehearsal: no v4 capture recorded for this day)"]
    assert label(drive, DAY) == "system_late" and not release.failed


class DownDrive(FakeDrive):
    def put(self, path, data):
        raise OSError("Drive down")


def test_a_rerun_after_a_failed_write_retries_it(tmp_path):
    builder, capture = complete(at(DAY, 14, 35))
    release, _ = run_for(tmp_path, at(DAY, 14, 35), live_from=DAY, builder=builder, capture=capture, drive=DownDrive())
    with pytest.raises(OSError):
        release.run(DAY)
    release, drive = run_for(tmp_path, at(DAY, 14, 38), live_from=DAY, builder=builder, capture=capture)
    assert release.run(DAY) == ["v4 release 2026-10-22: A"] and f"data/{release_path(DAY)}" in drive.files


def test_a_closed_day_writes_nothing_for_itself_and_does_not_fail(tmp_path):
    saturday = date(2026, 10, 24)
    release, drive = run_for(tmp_path, at(saturday, 15, 0), live_from=saturday)
    assert release.run(saturday) == [] and drive.files == {} and not release.failed


class SlowDrive(FakeDrive):
    """A pack upload that ends after 14:45:00 (it started at 14:44:59)."""

    def __init__(self, clock):
        super().__init__()
        self.clock = clock

    def put(self, path, data):
        super().put(path, data)
        if "/packs/" in path:
            self.clock.now = at(DAY, 14, 45, 30)


class Now:
    def __init__(self, moment):
        self.now = moment

    def __call__(self):
        return self.now


def test_a_pack_upload_ending_after_14_45_leaves_the_day_system_late_and_the_pack_unreleased(tmp_path):
    """Judge 584 m2: the release-by time is checked after the slow pack upload, right before the small record."""
    from fno.storage.data_store import DataStore
    from fno.storage.receipts import ReceiptFolder
    from fno.v4_pack.paths import pack_path
    from fno.v4_pack.release import parse_release
    from fno.v4_pack.release_run import ReleaseRun
    from tests.v4_pack.test_release_run import weekdays

    clock = Now(at(DAY, 14, 44, 59))
    drive = SlowDrive(clock)
    builder, capture = complete(clock.now)
    store = DataStore(drive, "data", ReceiptFolder(tmp_path / "receipts"), "v4-release", "run-1")
    release = ReleaseRun(store, lambda path: drive.get(path) is not None, capture, builder, weekdays, DAY, clock)
    assert release.run(DAY) == ["v4 release 2026-10-22: system_late (released late: after 14:45)"] and release.failed
    record = parse_release(DAY.isoformat(), drive.files[f"data/{release_path(DAY)}"])
    assert record.label == "system_late" and record.pack_path == "" and f"data/{pack_path(DAY)}" in drive.files
