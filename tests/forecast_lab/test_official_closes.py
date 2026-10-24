"""FL1-1d-2: the morning's official closes. G13b's tables first; the previous session's close, missing from them at
08:50, straight from the archived index-close file; neither: not archived yet."""

from datetime import date

from fno.forecast_lab.official_closes import ArchivedCloses
from fno.price_ranges.closes import IndexFileCloses
from fno.research_data.nifty_panel import DailyFiles
from tests.checks.builders import CALENDAR

THU, FRI = date(2026, 10, 22), date(2026, 10, 23)
FILE = (b"Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,Closing Index Value,Points Change,"
        b"Change(%),Volume,Turnover (Rs. Cr.),P/E,P/B,Div Yield\n"
        b"Nifty 50,23-10-2026,23016,23120.9,22649.9,22811.35,-77.6,-.34,1,1,1,1,1\n"
        b"Nifty Bank,23-10-2026,55707.85,55867.45,54696.45,54976.9,-511.2,-.92,1,1,1,1,1\n")  # fmt: skip


class Tables:
    def close(self, underlying, day):
        return 25000.0 if day == THU else None


def files(archived):
    def get(day):
        return f"ind_close_all_{day:%d%m%Y}.csv", (FILE if day in archived else None)

    return IndexFileCloses(DailyFiles("index-close", "nse/indices/index-close", THU, FRI, get), CALENDAR)


def test_the_tables_first_then_the_archived_file_then_nothing():
    closes = ArchivedCloses(Tables(), files({FRI}))
    assert closes.close("NIFTY", THU) == 25000.0
    assert (closes.close("NIFTY", FRI), closes.close("BANKNIFTY", FRI)) == (22811.35, 54976.9)
    assert ArchivedCloses(Tables(), files(set())).close("NIFTY", FRI) is None
