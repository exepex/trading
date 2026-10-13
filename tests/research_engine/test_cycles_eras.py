"""Story B2's monthly identity in both NSE eras (fix of 13 Oct 2026, response 48 item 0): counting and listing dates
only. The 2019-2023 panel is read with no option rows kept (`keep` refuses them), so no 2019-2023 option price is
held, computed or printed before experiment 1's freeze; only session dates, closes' presence and futures' expiry dates
are used."""

from __future__ import annotations

from collections import Counter
from datetime import date

from fno.composition import build_cycles
from fno.research_data.panel_reader import read_nifty_panel
from fno.storage.wiring import PANEL_FOLDER

FAR_WEEKLY = date(2019, 4, 18)  # a weekly first listed on 15 Feb 2019, 62 days ahead: A5's 50-day rule took it


def no_option_rows(day: date, expiry: date) -> bool:
    return False


def test_every_year_has_one_cycle_per_monthly_expiry():
    """12 a year: 60 cycles with decision days in 2019-2023 (the January 2019 expiry's window opened in December 2018,
    before the panel, so it is not a cycle; December 2023's exits in January 2024) and 33 in 2024-26, as meeting 1.
    A5's horizon rule gave 216 in 2019-2023, most of them weeklies."""
    panel = read_nifty_panel(PANEL_FOLDER, None, no_option_rows)
    cycles = build_cycles(panel)
    by_year = Counter(c.decision_day.year for c in cycles)
    assert by_year == {2019: 12, 2020: 12, 2021: 12, 2022: 12, 2023: 12, 2024: 12, 2025: 12, 2026: 9}
    assert len({(c.expiry.year, c.expiry.month) for c in cycles}) == len(cycles)  # one per calendar month
    assert all(c.expiry in {q.expiry for q in panel.futures[c.decision_day]} for c in cycles)
    assert FAR_WEEKLY not in {c.expiry for c in cycles}


def test_the_far_listed_2019_weekly_had_no_future():
    panel = read_nifty_panel(PANEL_FOLDER, (2019,), lambda day, expiry: expiry == FAR_WEEKLY)
    first = min(day for day, quotes in panel.options.items() if quotes)
    assert (first, (FAR_WEEKLY - first).days) == (date(2019, 2, 15), 62)
    assert not any(q.expiry == FAR_WEEKLY for quotes in panel.futures.values() for q in quotes)
