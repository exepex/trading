"""REH1b: Groww's candles in a rehearsal are the answer the day fetched for the same window, from the record, checked
against its manifest row; a window the day never asked for is the back-fill's own failure, never a live call."""

import csv
import gzip
import hashlib
import json
from datetime import UTC, date, datetime, timedelta

import pytest

from fno.intraday.candle_source import CandleCallFailed
from fno.rehearsal.recorded_candles import RecordedCandles

PATH = "groww/indices/nifty-candles-15m/2026/nifty_15m_20261022_20261022_abc.json.gz"
FIELDS = ("kind", "start", "end", "path", "sha256", "size", "requested_at", "fetched_at")


class Clock:
    def __init__(self, at):
        self.at = at

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.at += timedelta(seconds=seconds)


@pytest.fixture
def record(tmp_path):
    raw = json.dumps({"candles": [[1, 2, 3]]}, sort_keys=True).encode()
    data = gzip.compress(raw, mtime=0)
    with (tmp_path / "nifty-15m.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        writer.writerow(["15m", "2026-10-22", "2026-10-22", PATH, hashlib.sha256(data).hexdigest(), len(data),
                         "2026-10-23T10:03:30+00:00", "2026-10-23T10:03:31+00:00"])  # fmt: skip
    return tmp_path, {PATH: data}, raw


def test_the_catch_up_gets_the_day_s_own_answer_byte_for_byte(record):
    folder, drive, raw = record
    clock = Clock(datetime(2026, 10, 23, 10, 3, tzinfo=UTC))  # 15:33 IST
    answer = RecordedCandles(folder, drive.get, clock, clock.sleep).candles(date(2026, 10, 22), date(2026, 10, 22))
    assert answer.raw == raw and answer.rows == [[1, 2, 3]]
    assert answer.received_at == datetime(2026, 10, 23, 10, 3, 31, tzinfo=UTC) and clock() >= answer.received_at


def test_a_window_the_day_never_asked_for_or_a_changed_copy_is_the_back_fill_s_own_failure(record):
    folder, drive, _ = record
    clock = Clock(datetime(2026, 10, 23, 10, 3, tzinfo=UTC))
    with pytest.raises(CandleCallFailed, match="rehearsal:NOT_RECORDED"):
        RecordedCandles(folder, drive.get, clock, clock.sleep).candles(date(2026, 10, 21), date(2026, 10, 22))
    with pytest.raises(CandleCallFailed, match="differs from its manifest row"):
        RecordedCandles(folder, {PATH: b"changed"}.get, clock, clock.sleep).candles(date(2026, 10, 22),
                                                                                  date(2026, 10, 22))  # fmt: skip
