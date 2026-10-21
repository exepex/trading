"""FL1-1c: each method's record from G13b's score rows (cells, 7/14/30-session windows, the trailing-20 trend) and the
stricter 20-session checks with their stated limits."""

from fno.forecast_lab.page.drift import method_problems, stale
from fno.forecast_lab.page.history import method_record

from .page_builders import DAY, days, point

SESSIONS = days(40)


def record(hits_90: int, hits_50: int, n: int = 20):
    """The last `n` sessions with the given hits, earlier ones all inside both bands."""
    flags = [(True, True)] * (len(SESSIONS) - n) + [(i < hits_50, i < hits_90) for i in range(n)]
    points = [point("rv20", d, inside=f) for d, f in zip(SESSIONS, flags, strict=True)]
    return method_record(points, SESSIONS, SESSIONS[-30:], best=False)


def test_cells_windows_and_the_trend_come_from_the_score_rows():
    r = record(hits_90=18, hits_50=10)
    assert len(r.cells) == 30 and [w.sessions for w in r.windows] == [7, 14, 30]
    assert r.windows[0].count == 7 and r.windows[-1].error_points == 5.0
    assert r.rolling_90[-1] == 18 / 20 and r.rolling_90[9] == 1.0 and r.rolling_90[0] is None  # needs 20 sessions


def test_the_stricter_checks_flag_the_90_band_under_80_and_the_50_band_outside_35_to_65():
    assert method_problems("NIFTY", "N1", record(16, 10), SESSIONS[-20:]) == []
    texts = [p.text for p in method_problems("NIFTY", "N1", record(15, 13), SESSIONS[-20:])]
    assert texts == ["90% band held 75% of the last 20 closes (normal: 80% or more)"]
    texts = [p.text for p in method_problems("NIFTY", "N1", record(20, 14), SESSIONS[-20:])]
    assert texts == ["50% band held 70% of the last 20 closes (normal: 35% to 65%)"]


def test_missing_scores_and_stale_data_are_problems():
    short = method_record([point("rv20", d) for d in SESSIONS[-10:]], SESSIONS, SESSIONS[-30:], best=False)
    (missing,) = method_problems("NIFTY", "N1", short, SESSIONS[-20:])
    assert missing.text == "only 10 of the last 20 sessions scored (missing data)"
    assert stale("NIFTY", SESSIONS[-2], DAY)[0].text.endswith("(stale)") and stale("NIFTY", DAY, DAY) == []
