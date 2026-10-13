"""Story B3, judge 28 minor: a period's data opens only that period's option files (plus a year after, for late
exits); the look-back comes from the index-close file. The repository's file agrees with the panel where both exist."""

import csv
from datetime import date

from fno import composition
from fno.research_data.panel_reader import read_nifty_panel
from fno.research_data.panel_store import WARMUP_FILE
from fno.research_engine.experiment_1 import EXPERIMENT_1
from fno.storage.wiring import PANEL_FOLDER, build_session_calendar


def test_a_period_never_opens_an_earlier_years_option_file(monkeypatch):
    asked = {}
    monkeypatch.setattr(composition, "load_research_data", lambda years, keep: asked.update(years=list(years)))
    for period in EXPERIMENT_1.periods:
        composition.load_period_data(period)
        assert min(asked["years"]) == period.start.year and max(asked["years"]) == period.end.year + 1


def closes_file():
    with (PANEL_FOLDER / WARMUP_FILE).open(newline="") as f:
        return {date.fromisoformat(r["date"]): (float(r["underlying"]), float(r["vix"])) for r in csv.DictReader(f)}


def test_the_index_close_file_agrees_with_the_panel_on_2026():
    panel, file = read_nifty_panel(PANEL_FOLDER, [2026], keep=lambda day, expiry: False), closes_file()
    days = [s for s in panel.sessions if s.day.year == 2026 and s.underlying is not None]
    assert len(days) > 180 and all(file[s.day] == (s.underlying, s.vix) for s in days)


def test_every_2019_session_has_250_previous_vix_closes():
    """F2 is defined on any 2019 decision day: the day has a VIX close and 250 valid earlier ones (counts only; no
    2019 feature value is computed before experiment 1's freeze)."""
    with (PANEL_FOLDER / WARMUP_FILE).open(newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["session"] != "muhurat" and float(r["vix"]) > 0]
    vix_days = sorted(date.fromisoformat(r["date"]) for r in rows)
    calendar = build_session_calendar()
    for day in calendar.sessions(date(2019, 1, 1), date(2019, 12, 31)):
        if calendar.session_kind(day) != "muhurat":
            assert day in vix_days and sum(d < day for d in vix_days) >= 250, day
