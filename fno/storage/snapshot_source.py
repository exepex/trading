"""NSE reference lists whose file name has no date (story P6): the list of listed companies and the Nifty 500 list.
NSE replaces them in place, so each copy is archived under the day it was fetched:
`<dataset>/<YYYY>/<MM>/<DD>/<original file name>` (the original name kept, one folder per day)."""

from __future__ import annotations

from datetime import date, datetime

from .raw_source import NseArchiveSource

SNAPSHOT_FOLDER = "%Y/%m/%d"


class SnapshotSource(NseArchiveSource):
    FILENAME = ""  # the publisher's fixed file name

    @classmethod
    def filename_for(cls, day: date) -> str:
        return cls.FILENAME

    @classmethod
    def path_for(cls, day: date) -> str:
        return f"{cls.dataset}/{day:{SNAPSHOT_FOLDER}}/{cls.FILENAME}"

    @classmethod
    def day_for(cls, filename: str) -> date:
        raise ValueError(f"{filename}: a snapshot's day is its folder, not its name (use day_for_path)")

    @classmethod
    def day_for_path(cls, path: str) -> date:
        *_, year, month, day, filename = path.split("/")
        if filename != cls.FILENAME:
            raise ValueError(f"{path}: not a {cls.FILENAME} snapshot")
        return datetime.strptime(f"{year}/{month}/{day}", SNAPSHOT_FOLDER).date()


class EquityListSource(SnapshotSource):
    """Every company listed on NSE's capital market with its name (EQUITY_L.csv)."""

    dataset = "nse/equities/equity-list"
    first_day = date(2026, 10, 13)  # the first copy archived (P6)
    BASE_URL = "https://nsearchives.nseindia.com/content/equities/"
    FILENAME = "EQUITY_L.csv"


class Nifty500ListSource(SnapshotSource):
    """The Nifty 500's members with their industry (ind_nifty500list.csv)."""

    dataset = "nse/indices/nifty500-list"
    first_day = date(2026, 10, 13)
    BASE_URL = "https://nsearchives.nseindia.com/content/indices/"
    FILENAME = "ind_nifty500list.csv"
