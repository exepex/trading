"""Story G10 completion, criteria 5 and 6: one label rule for a day without a release record (the writer's catch-up
and every reader); G8's three readers (`build_scoring`, `build_ai_slot_days`, `build_day_counts`) read the release
records from Drive through O9's verified cache, never a checkout folder, and a record that fails verification stops
them with the day named."""

from datetime import date, timedelta

import pytest

from fno.config import ROOT
from fno.constants import V4_DAY_A, V4_DAY_SYSTEM_LATE, V6_BIG_MOVE_1S
from fno.forecast_scoring.v4 import wiring
from fno.forecast_scoring.v4.days import PENDING, DayFileError, DayLabel, LiveDayLabels, V4DaySource, missing_label
from fno.forecast_scoring.v4.drive_records import DriveRecords
from fno.forecast_scoring.v4.release_days import ReleasedDays
from fno.storage import data_wiring
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.receipts import ReceiptFolder
from fno.v4_pack.paths import release_path
from fno.v4_pack.release import publish
from tests.v4_pack.test_release import FakeDrive

LIVE = date(2026, 10, 22)  # config.yaml daily.live_from.forecasts_v4
THU, FRI, MON, TUE = LIVE, date(2026, 10, 23), date(2026, 10, 26), date(2026, 10, 27)


def weekdays(first, last):
    return [first + timedelta(n) for n in range((last - first).days + 1) if (first + timedelta(n)).weekday() < 5]


@pytest.mark.parametrize(
    ("day", "live_from", "today", "expected"),
    [
        (date(2026, 10, 21), LIVE, MON, None),  # before the live date: the close-proxy cohort
        (LIVE, LIVE, MON, V4_DAY_SYSTEM_LATE),  # the live date itself, now past
        (FRI, LIVE, MON, V4_DAY_SYSTEM_LATE),  # yesterday's session
        (MON, LIVE, MON, PENDING),  # the report's own date
        (LIVE, LIVE, LIVE, PENDING),
        (MON, None, TUE, None),  # not live at all
    ],
)
def test_the_one_rule_for_a_day_without_a_record(day, live_from, today, expected):
    assert missing_label(day, live_from, today) == expected


class Records(V4DaySource):
    def __init__(self, found):
        self.found = found

    def labels(self):
        return self.found


def test_live_labels_add_system_late_for_every_past_live_session_without_a_record_and_count_today_pending():
    a_friday = {FRI: DayLabel(FRI, V4_DAY_A, "a" * 64, None)}
    labels = LiveDayLabels(Records(a_friday), weekdays, LIVE, MON)
    assert {d: lab.label for d, lab in labels.labels().items()} == {THU: V4_DAY_SYSTEM_LATE, FRI: V4_DAY_A}
    assert labels.pending() == 1
    assert LiveDayLabels(Records({}), weekdays, LIVE, LIVE).labels() == {} and LiveDayLabels(
        Records({}), weekdays, None, TUE).pending() == 0  # fmt: skip
    saturday = LiveDayLabels(Records({}), weekdays, LIVE, date(2026, 10, 24))
    assert saturday.pending() == 0 and set(saturday.labels()) == {THU, FRI}


def released(tmp_path, *days, late=()):
    """Release records written by the real `publish` into a fake Drive, receipts in `tmp_path/receipts`."""
    drive, receipts = FakeDrive(), ReceiptFolder(tmp_path / "receipts")
    store = DataStore(drive, "data", receipts, "v4-release", "run-1")
    for day in (*days, *late):
        publish(store, day, None)  # system_late records: no pack needed
    built = []

    def cache():
        built.append(1)
        return DriveCache(drive, receipts, tmp_path / "cache")

    return ReleasedDays(DriveRecords(receipts, cache, "data", "v4/days")), drive, built


def test_records_are_read_from_drive_across_a_year_folder(tmp_path):
    days, _, built = released(tmp_path, date(2026, 12, 31), date(2027, 1, 1))
    assert {d: lab.label for d, lab in days.labels().items()} == {
        date(2026, 12, 31): V4_DAY_SYSTEM_LATE, date(2027, 1, 1): V4_DAY_SYSTEM_LATE}  # fmt: skip
    assert built == [1]


def test_no_receipt_yet_means_no_records_and_no_drive(tmp_path):
    days, _, built = released(tmp_path)
    assert days.labels() == {} and built == []


def test_a_tampered_or_missing_record_stops_with_the_day_named(tmp_path):
    days, drive, _ = released(tmp_path, LIVE)
    drive.files[f"data/{release_path(LIVE)}"] = b'{"changed": true}'
    with pytest.raises(DayFileError, match="2026-10-22"):
        days.labels()
    del drive.files[f"data/{release_path(LIVE)}"]
    with pytest.raises(DayFileError, match="not returned by Drive"):
        days.labels()


@pytest.fixture
def drive_records(tmp_path, monkeypatch):
    """The real wiring, its receipts folder and Drive cache pointed at a fake Drive holding a system_late record for
    22 Oct, the report's date: so the label can only come from Drive (no rule infers anything on the live date)."""
    _, drive, _ = released(tmp_path, LIVE)
    receipts = ReceiptFolder(tmp_path / "receipts")
    monkeypatch.setattr(data_wiring, "receipt_folder", lambda: receipts)
    monkeypatch.setattr(data_wiring, "build_drive_cache", lambda env=None: DriveCache(drive, receipts, tmp_path / "c"))
    monkeypatch.setattr(wiring, "_today", lambda: LIVE)


def test_build_scoring_drops_the_system_late_day_from_drive(drive_records):
    values = wiring.build_scoring().forecasts.values(V6_BIG_MOVE_1S, "base_rate")
    assert LIVE not in values and FRI in values  # 23 Oct's committed live row stays


def test_build_ai_slot_days_never_requires_the_system_late_day(drive_records):
    assert LIVE not in wiring.build_ai_slot_days().sessions(LIVE, FRI)


def test_build_day_counts_counts_it_system_late(drive_records):
    counts = wiring.build_day_counts(LIVE)
    assert (counts.late, counts.pending) == (1, 0)


def test_no_checkout_label_folder_is_left():
    sources = "".join(p.read_text(encoding="utf-8") for p in (ROOT / "fno").rglob("*.py"))
    assert "v4_days" not in sources and "V4_DAYS_FOLDER" not in sources


def test_a_system_late_day_is_never_an_unchecked_deadline_day(drive_records, monkeypatch):
    """Review finding 2: a day out for every family needs no 15:10 verdict to let a look run."""
    monkeypatch.setattr(wiring, "_today", lambda: FRI)
    assert LIVE not in wiring.build_unchecked_days()
