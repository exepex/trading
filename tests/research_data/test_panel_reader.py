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


def test_reading_later_years_takes_earlier_closes_from_the_index_close_file_only(tmp_path):
    """Judge 28 minor: reading 2025 on gets 2024's closes from the index-close file, never 2024's option rows."""
    import csv

    from fno.research_data.panel_store import WARMUP_FIELDS, WARMUP_FILE

    write_panel(tmp_path)
    with (tmp_path / WARMUP_FILE).open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(WARMUP_FIELDS)
        writer.writerow(["2024-12-30", "regular", "23400.00", "14.10", "ind_close_all_30122024.csv", "x"])
        writer.writerow(["2024-12-31", "regular", "23450.00", "14.20", "ind_close_all_31122024.csv", "x"])
        writer.writerow(["2025-01-01", "regular", "99999.00", "99.00", "ind_close_all_01012025.csv", "x"])
    panel = read_nifty_panel(tmp_path, years=[2025])
    assert [(s.day, s.underlying, s.vix) for s in panel.sessions[:2]] == [
        (date(2024, 12, 30), 23400.0, 14.1),
        (date(2024, 12, 31), 23450.0, 14.2),  # from the file, not from D1's option rows (23500.10)
    ]
    assert panel.session_on(D2).underlying is None  # inside the years read, the panel's own record stands
    assert D1 not in panel.options and D1 not in panel.futures
