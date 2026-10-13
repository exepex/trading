"""NSE reference lists whose file name has no date (story P6): the list of listed companies, the Nifty 500 list, the
symbol changes and the corporate actions.
NSE replaces them in place, so each copy is archived under the day it was fetched:
`<dataset>/<YYYY>/<MM>/<DD>/<original file name>` (the original name kept, one folder per day)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import quote

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


class SymbolChangeSource(SnapshotSource):
    """Every symbol change on NSE's capital market since 2003, with its effective date (symbolchange.csv): a renamed
    stock's earlier sessions are under its old symbol (TATAMOTORS became TMPV on 24 Oct 2025)."""

    dataset = "nse/equities/symbol-change"
    first_day = date(2026, 10, 13)
    BASE_URL = "https://nsearchives.nseindia.com/content/equities/"
    FILENAME = "symbolchange.csv"


class FiiDiiCashSource(SnapshotSource):
    """NSE's provisional FII/FPI and DII cash-market buy and sell values (JSON from its website). NSE serves only the
    latest session, so each day's copy is archived under the day it was fetched and the history builds from the first
    copy; the session it covers is inside the file (P8)."""

    dataset = "nse/flows/fii-dii-cash"
    first_day = date(2026, 10, 14)  # the first copy archived (P8)
    FILENAME = "fii-dii-cash.json"
    API = "https://www.nseindia.com/api/fiidiiTradeReact"

    @classmethod
    def url_for(cls, path: str) -> str:
        cls.day_for_path(path)  # refuses a path that is not one of this dataset's copies
        return cls.API


class NsdlFpiDailySource(SnapshotSource):
    """NSDL's latest daily FPI investment report (HTML): the FPI equity net over all routes, for the session it names.
    Served for the latest reporting day only, so archived per day fetched like NSE's FII/DII values (P8)."""

    dataset = "nsdl/fpi/fpi-daily"
    first_day = date(2026, 10, 14)
    FILENAME = "fpi-daily-latest.html"
    BASE_URL = "https://www.fpi.nsdl.co.in/web/Reports/"
    PAGE = "Latest.aspx"

    @classmethod
    def url_for(cls, path: str) -> str:
        cls.day_for_path(path)
        return cls.BASE_URL + cls.PAGE


class CorporateActionsSource(SnapshotSource):
    """NSE's list of equity corporate actions (splits, bonuses, demergers, dividends...) over the year to the day it is
    fetched, from NSE's website (JSON; its own name has no file, so the list is filed under a fixed name)."""

    dataset = "nse/equities/corporate-actions"
    first_day = date(2026, 10, 13)
    FILENAME = "corporate-actions-equities.json"
    API = "https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={start}&to_date={end}"
    WINDOW = timedelta(days=400)  # covers the screener's year and a week

    @classmethod
    def url_for(cls, path: str) -> str:
        day = cls.day_for_path(path)
        return cls.API.format(start=f"{day - cls.WINDOW:%d-%m-%Y}", end=f"{day:%d-%m-%Y}")


class CorporateActionsBySymbolSource(CorporateActionsSource):
    """One symbol's own corporate-action list from NSE's website, for symbols the range list leaves out (ETFs such as
    BANKNIFTY1), filed as `<dataset>/<YYYY>/<MM>/<DD>/<SYMBOL>.json`. NSE answers these without a date range (with
    one it answers [] for some symbols); the build applies only actions inside its window."""

    dataset = "nse/equities/corporate-actions-by-symbol"
    SYMBOL_API = "https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={symbol}"
    EXTENSION = ".json"

    @classmethod
    def path_for_symbol(cls, day: date, symbol: str) -> str:
        return f"{cls.dataset}/{day:{SNAPSHOT_FOLDER}}/{symbol}{cls.EXTENSION}"

    @classmethod
    def day_for_path(cls, path: str) -> date:
        *_, year, month, day, filename = path.split("/")
        if not filename.endswith(cls.EXTENSION):
            raise ValueError(f"{path}: not a symbol's corporate-action list")
        return datetime.strptime(f"{year}/{month}/{day}", SNAPSHOT_FOLDER).date()

    @classmethod
    def url_for(cls, path: str) -> str:
        return cls.SYMBOL_API.format(symbol=quote(path.rsplit("/", 1)[-1].removesuffix(cls.EXTENSION)))
