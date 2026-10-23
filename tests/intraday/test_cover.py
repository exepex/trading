"""Story A16i: every mark has two fires, because a fire runs one hour past the --until it is given."""

from datetime import datetime, time, timedelta

import pytest

from fno.intraday.cover import SESSION_END, covered_until


@pytest.mark.parametrize(
    "given, expected",
    [("10:05", "11:05"), ("14:05", "15:05"), ("14:50", "15:35"), ("15:35", "15:35"), ("16:00", "16:00")],
)
def test_the_end_moves_one_hour_and_stops_at_the_session_end(given, expected):
    assert covered_until(time.fromisoformat(given)) == time.fromisoformat(expected)


def test_every_mark_of_the_session_has_two_fires():
    """The prompt's fires, as written (H:52, ending (H+2):05 and at 15:35 from 14:52), with the extra hour."""
    fires = []
    for hour in range(8, 15):
        prompt_end = time(15, 35) if hour >= 14 else time(hour + 2, 5)
        fires.append((time(hour, 52), covered_until(prompt_end)))
    start = datetime(2026, 1, 1, 9, 15)
    marks = [(start + timedelta(minutes=15 * n)).time() for n in range(26)]
    assert marks[-1] == SESSION_END.replace(minute=30)
    single = [m for m in marks if sum(f <= m <= u for f, u in fires) < 2]
    assert single == [
        time(9, 15),
        time(9, 30),
        time(9, 45),
    ]  # the first fire has no earlier fire: needs the owner's 08:22 fire
