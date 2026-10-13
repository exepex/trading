"""Story G3: Book 1's frozen method (criterion 2: the method file's hash in every record), the daily record (criterion
1: five probabilities or a recorded "no forecast", never imputed) and the deadline (criterion 3)."""

import hashlib
import subprocess
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from forecast_fixtures import CALENDAR

from fno.constants import BOOK1_RULES, FORECAST_QUESTIONS
from fno.forecast import book1_method
from fno.forecast.book1_method import book1_probabilities, method_label, method_sha256
from fno.forecast.capture import (
    EMPTY_PACK_SHA256,
    CaptureRefused,
    capture_book1,
    first_commit_time,
    live_path,
    on_time,
)
from fno.forecast.record_files import read_records
from fno.models import IST

Q1, Q2, Q3, Q4, Q5 = FORECAST_QUESTIONS
DAY = date(2026, 10, 13)


def test_book1_is_the_mean_of_the_questions_two_baselines():
    by = {
        "baseline_a_risk_neutral": {Q1: 0.40, Q2: 0.30},
        "baseline_b_base_rate": {Q1: 0.60, Q2: None, Q3: 0.50, Q4: None, Q5: 0.70},
        "baseline_c_model": {Q3: 0.30, Q4: None, Q5: 0.90},
    }
    assert book1_probabilities(by) == {Q1: pytest.approx(0.5), Q2: 0.30, Q3: pytest.approx(0.4), Q4: None,
                                       Q5: pytest.approx(0.8)}  # fmt: skip
    assert book1_probabilities({}) == dict.fromkeys(FORECAST_QUESTIONS)


def test_the_method_label_carries_the_method_files_hash():
    expected = hashlib.sha256(Path(book1_method.__file__).read_bytes()).hexdigest()
    assert method_sha256() == expected and method_label() == f"book1/v1/sha256:{expected}"


def test_a_trading_day_gets_five_recorded_no_forecasts_never_imputed(tmp_path):
    line = capture_book1(tmp_path, DAY, CALENDAR)
    records = read_records(live_path(tmp_path, DAY).read_text(encoding="utf-8"))
    assert [r.question for r in records] == list(FORECAST_QUESTIONS)
    assert all(r.book == BOOK1_RULES and r.probability is None for r in records)
    assert all(r.pack_sha256 == EMPTY_PACK_SHA256 == hashlib.sha256(b"").hexdigest() for r in records)
    assert all(r.method_or_version == f"{method_label()}/no-live-inputs" for r in records)
    assert all(r.cutoff == datetime(2026, 10, 13, 15, 0, tzinfo=IST) for r in records)
    assert "no forecast recorded" in line and "E2" in line


def test_records_are_written_once(tmp_path):
    capture_book1(tmp_path, DAY, CALENDAR)
    assert "already recorded" in capture_book1(tmp_path, DAY, CALENDAR)
    live_path(tmp_path, DAY).write_text("changed\n", encoding="utf-8")
    with pytest.raises(CaptureRefused):
        capture_book1(tmp_path, DAY, CALENDAR)


def test_a_closed_day_records_nothing(tmp_path):
    assert "not a trading day" in capture_book1(tmp_path, date(2026, 10, 11), CALENDAR)  # a Sunday
    assert not live_path(tmp_path, date(2026, 10, 11)).exists()


def test_the_deadline_is_1530_ist_on_the_forecast_day():
    deadline = datetime(2026, 10, 13, 15, 30, tzinfo=IST)
    assert on_time(DAY, deadline) and on_time(DAY, deadline - timedelta(minutes=29))
    assert not on_time(DAY, deadline + timedelta(seconds=1))
    assert not on_time(DAY, datetime(2026, 10, 13, 10, 1, tzinfo=UTC))  # 15:31 IST
    assert not on_time(DAY, None)


def test_first_commit_time_is_when_the_file_was_added(tmp_path):
    def git(*args, when="2026-10-13T15:12:00+05:30"):
        env = {"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when, "PATH": "/usr/bin:/bin"}
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, env=env)

    git("init", "-q")
    capture_book1(tmp_path, DAY, CALENDAR)
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "record")
    (tmp_path / "other").write_text("x")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "later",
        when="2026-10-14T09:00:00+05:30")  # fmt: skip
    committed = first_commit_time(tmp_path, live_path(tmp_path, DAY))
    assert committed == datetime(2026, 10, 13, 15, 12, tzinfo=IST) and on_time(DAY, committed)
    assert first_commit_time(tmp_path, tmp_path / "never.csv") is None
