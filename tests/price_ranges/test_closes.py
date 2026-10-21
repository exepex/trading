"""G13b criterion 5: official closes. "Nifty 50" and "Nifty Bank" are read from the archived index-close files, a
missing file or row is a counted gap (never filled), BANKNIFTY's Drive table is extended once per new close, and
`Outcomes.close` gives the same close the scorer and FL1 read."""

from datetime import date
from pathlib import Path

from fno.config import ROOT
from fno.forecast_v4_rules.series import closes_rows, regular_closes
from fno.price_ranges.closes import CommittedNiftyCloses, IndexFileCloses, Outcomes, TableCloses, table_rows
from fno.price_ranges.tables import CloseTables
from fno.storage.drive_cache import DriveCache
from tests.price_distribution.builders import drive_store
from tests.price_ranges.builders import CALENDAR, daily_files, index_close_file

MON, TUE, WED, THU = date(2026, 10, 19), date(2026, 10, 20), date(2026, 10, 21), date(2026, 10, 22)
FILES = {MON: ("ind_close_all_19102026.csv", index_close_file({"Nifty 50": 22888.95, "Nifty Bank": 51234.5})),
         WED: ("ind_close_all_21102026.csv", index_close_file({"Nifty 50": 23001.0}))}  # fmt: skip


def test_the_named_close_is_read_and_gaps_are_counted_never_filled():
    reader = IndexFileCloses(daily_files(FILES), CALENDAR)
    rows, gaps = reader.rows("BANKNIFTY", MON, THU)
    assert rows == [(MON, 51234.5, "ind_close_all_19102026.csv")]  # 20th a holiday: not even asked
    assert gaps == ["BANKNIFTY 2026-10-21: no 'Nifty Bank' row in ind_close_all_21102026.csv",
                    "BANKNIFTY 2026-10-22: no index-close file"]  # fmt: skip
    assert reader.rows("NIFTY", MON, WED)[0] == [(MON, 22888.95, FILES[MON][0]), (WED, 23001.0, FILES[WED][0])]


def test_nifty_comes_from_the_committed_closes_and_outcomes_read_the_same_series():
    text = (ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv").read_text(encoding="utf-8")
    committed = CommittedNiftyCloses(lambda: text)
    outcomes = Outcomes(TableCloses(lambda u: None, committed))
    first = regular_closes(closes_rows(text))[0]
    assert outcomes.close("NIFTY", first.day) == first.value and outcomes.close("NIFTY", date(2001, 1, 1)) is None
    assert outcomes.close("BANKNIFTY", first.day) is None  # no table yet: unresolved


def test_the_banknifty_table_is_extended_once_per_new_close(tmp_path):
    store, drive, receipts = drive_store(tmp_path)
    tables = CloseTables(store, receipts, DriveCache(drive, receipts, tmp_path / "cache"), first_day=MON)
    reader = IndexFileCloses(daily_files(FILES), CALENDAR)
    lines = tables.update("BANKNIFTY", reader, THU)
    assert lines[-1] == "BANKNIFTY closes: 1 new rows through 2026-10-19"
    assert table_rows(tables.latest_text("BANKNIFTY")) == [
        table_rows("date,close,index_file\n2026-10-19,51234.5,x\n")[0]
    ]
    assert tables.update("BANKNIFTY", reader, MON) == ["BANKNIFTY closes: no new row (table through 2026-10-19)"]
    assert len(drive.files) == 1
    assert Path(tables.cache.local(tables.latest_path("BANKNIFTY"))).is_file()
