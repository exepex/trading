"""Story A14c's read-ahead: files come back in the order asked whatever order the downloads finish in, never more than
`workers` downloads at once, a download error stops the reading at its day, and each thread has its own reader."""

import threading
import time
from datetime import date, timedelta

import pytest

from fno.config import load_app_config
from fno.nse_margins.prefetch import in_order, per_thread
from fno.nse_margins.wiring import build_stress_factor_run
from fno.risk.settings import RiskSettingsError

DAYS = [date(2026, 10, 1) + timedelta(days=i) for i in range(12)]


class SlowDrive:
    """Later days download faster, so a pool that handed files back as they finish would reorder them."""

    def __init__(self, fail_on: date | None = None):
        self.fail_on, self.running, self.most, self.asked = fail_on, 0, 0, []
        self.lock = threading.Lock()

    def __call__(self, day: date) -> tuple[str, bytes | None]:
        with self.lock:
            self.running += 1
            self.most = max(self.most, self.running)
            self.asked.append(day)
        time.sleep(0.002 * (len(DAYS) - DAYS.index(day)))
        with self.lock:
            self.running -= 1
        if day == self.fail_on:
            raise ConnectionError(f"Drive refused {day}")
        return f"nsccl.{day:%Y%m%d}.i1.zip", day.isoformat().encode()


@pytest.mark.parametrize("workers", [1, 3, 8, 20])
def test_files_come_back_in_the_order_asked_with_at_most_workers_running(workers):
    drive = SlowDrive()
    got = list(in_order(drive, DAYS, workers))
    assert [day for day, _ in got] == DAYS
    assert all(data == day.isoformat().encode() for day, (_, data) in got)
    assert drive.most <= workers and sorted(drive.asked) == DAYS


def test_a_download_error_stops_the_reading_at_its_day():
    drive, read = SlowDrive(fail_on=DAYS[4]), []
    with pytest.raises(ConnectionError, match="2026-10-05"):
        for day, _ in in_order(drive, DAYS, 3):
            read.append(day)
    assert read == DAYS[:4]
    assert len(drive.asked) <= 4 + 3  # nothing is asked beyond the read-ahead window


def test_a_reader_that_stops_early_leaves_no_download_running():
    drive = SlowDrive()
    for day, _ in in_order(drive, DAYS, 4):
        if day == DAYS[1]:
            break
    assert drive.running == 0 and len(drive.asked) <= 2 + 4


def test_workers_below_one_are_refused():
    with pytest.raises(ValueError, match="at least 1"):
        list(in_order(SlowDrive(), DAYS, 0))


def test_each_thread_builds_its_own_reader_once():
    built, lock = [], threading.Lock()

    def new_reader():
        with lock:
            built.append(threading.get_ident())
        return SlowDrive()

    list(in_order(per_thread(new_reader), DAYS, 4))
    assert 1 <= len(built) <= 4 and len(set(built)) == len(built)


def test_the_full_run_reads_eight_ahead_from_config_and_refuses_a_bad_count(tmp_path):
    run = build_stress_factor_run(load_app_config(), date(2026, 11, 8), day_file=SlowDrive(), root=tmp_path)
    assert run.sources.workers == 8
    bad = load_app_config(overrides={"risk": {"stressed_margin": {"recompute_workers": 0}}})
    with pytest.raises(RiskSettingsError, match="recompute_workers"):
        build_stress_factor_run(bad, date(2026, 11, 8), day_file=SlowDrive(), root=tmp_path)
