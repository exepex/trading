"""REH1g (DRY2's KOSPI miss): every recorded source serves the answer the day saved from a minute before now to ten
minutes after it; an answer saved before now is no look-ahead. One rule, in one place."""

from datetime import datetime, timedelta

from fno.models import IST
from fno.rehearsal.serving import EARLIER, NEAREST, is_near

READ = datetime(2026, 10, 23, 8, 50, 40, 136560, tzinfo=IST)  # the rehearsal's KOSPI read


def test_the_kospi_copy_saved_six_seconds_before_the_read_is_served():
    assert is_near(READ, datetime(2026, 10, 23, 8, 50, 34, 20913, tzinfo=IST))


def test_the_window_is_a_minute_before_to_ten_minutes_after_and_no_wider():
    assert timedelta(seconds=60) == EARLIER and timedelta(minutes=10) == NEAREST
    assert is_near(READ, READ - EARLIER) and is_near(READ, READ + NEAREST)
    assert not is_near(READ, READ - EARLIER - timedelta(microseconds=1))
    assert not is_near(READ, READ + NEAREST + timedelta(microseconds=1))


def test_every_recorded_source_uses_the_one_rule():
    from pathlib import Path

    import fno.rehearsal as package

    for name in ("recorded_cues", "recorded_candles", "recorded_preopen", "recorded_closes"):
        text = (Path(package.__file__).parent / f"{name}.py").read_text()
        assert "is_near(now, " in text and "timedelta(seconds=5)" not in text and "NEAREST =" not in text
