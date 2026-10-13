"""Reading the NIFTY panel back for research (story B1): what A3's writer wrote, and nothing filled in."""

from datetime import date

from fno.constants import PANEL_DAY_NO_FILE, PANEL_DAY_OK
from fno.research_data.panel_reader import FutureQuote, OptionQuote, read_nifty_panel
from fno.research_data.panel_rows import FUTURES, OPTIONS
from fno.research_data.panel_store import CsvGzPanelFolder, PanelDay

D1, D2, D3 = date(2024, 12, 31), date(2025, 1, 1), date(2025, 1, 2)
EXPIRY, WEEKLY = "2025-01-30", "2025-01-09"


def option(day, expiry, strike, kind, close, volume):
    return (day.isoformat(), expiry, strike, kind, close, "1.00", volume, "50", "23500.10", "14.50", "udiff", "regular")


def write_panel(folder):
    sink = CsvGzPanelFolder(folder)
    sink.begin(D1, D3)
    for day in (D1, D3):
        rows = {
            OPTIONS: [
                option(day, EXPIRY, "23500.00", "CE", "210.50", "12"),
                option(day, WEEKLY, "23500.00", "PE", "90.00", "0"),
            ],
            FUTURES: [(day.isoformat(), EXPIRY, "23580.00", "23581.00", "7", "900", "23500.10", "udiff", "regular")],
        }
        sink.add(PanelDay(day, {"session": "regular", "status": PANEL_DAY_OK}, rows))
    sink.add(PanelDay(D2, {"session": "regular", "status": PANEL_DAY_NO_FILE}, {}))
    sink.finish({"start": D1.isoformat(), "end": D3.isoformat()})


def test_reads_sessions_closes_options_and_futures_back(tmp_path):
    write_panel(tmp_path)
    panel = read_nifty_panel(tmp_path)
    assert [s.day for s in panel.sessions] == [D1, D2, D3]
    assert panel.session_on(D3).underlying == 23500.10 and panel.session_on(D3).vix == 14.50
    assert panel.options_on(D3, date(2025, 1, 30)) == [
        OptionQuote(date(2025, 1, 30), 23500.0, "CE", 210.5, 1.0, 12, 50)
    ]
    assert panel.future_on(D3, date(2025, 1, 30)) == FutureQuote(date(2025, 1, 30), 23580.0, 23581.0, 7, 900)
    assert panel.future_on(D3, date(2025, 2, 27)) is None


def test_a_left_out_session_stays_listed_without_closes(tmp_path):
    write_panel(tmp_path)
    left_out = read_nifty_panel(tmp_path).session_on(D2)
    assert (left_out.underlying, left_out.vix) == (None, None)


def test_years_and_keep_limit_what_is_held_but_not_the_closes(tmp_path):
    write_panel(tmp_path)
    panel = read_nifty_panel(tmp_path, years=[2025], keep=lambda day, expiry: expiry == date(2025, 1, 30))
    assert [s.day for s in panel.sessions] == [D2, D3]
    assert [q.expiry for q in panel.options[D3]] == [date(2025, 1, 30)]
    assert panel.session_on(D3).underlying == 23500.10
    assert [s.day for s in panel.sessions_through(D2)] == [D2]
