"""Where raw files originally come from (an exchange archive, a data vendor). Each source knows only its own
naming and transport; callers see one interface."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import date

import requests

from ..constants import MONTH_CODES

NOT_PUBLISHED = 404


class RawSourceUnavailable(RuntimeError):
    """The source could not be reached (after retries); try again later. Not the same as "no such file"."""


class RawFileSource(ABC):
    name: str = "source"
    dataset: str = ""  # archive folder of this source's files: "<publisher>/<market>/<dataset>"
    first_day: date | None = None  # first day the archive keeps files for (None: not dated)
    last_day: date | None = None  # last day it publishes them for (None: still publishing)

    @abstractmethod
    def fetch(self, path: str) -> bytes | None:
        """The file at an archive path; None when the source does not publish it; RawSourceUnavailable on a failure."""

    @staticmethod
    def dated_path(dataset: str, day: date, filename: str) -> str:
        """`<dataset>/<YYYY>/<MM>/<original file name>`: one folder per month, original names kept."""
        return f"{dataset}/{day:%Y}/{day:%m}/{filename}"


class NseArchiveSource(RawFileSource):
    """A dated file from NSE's public archive, through a polite session: retries dropped connections, reports a day
    without a file (holiday, weekend) as None. Subclasses give only the dataset, file name and URL."""

    name = "NSE archive"
    FILENAME = ""  # format string of the original file name for a day
    RETRY_WAITS = (5, 15, 45)  # seconds before each retry of a dropped connection
    TIMEOUT_SECONDS = 60

    def __init__(self, session: requests.Session, sleep=time.sleep):
        self.session, self.sleep = session, sleep

    @classmethod
    def filename_for(cls, day: date) -> str:
        return cls.FILENAME.format(day=day, mon=MONTH_CODES[day.month - 1])

    @classmethod
    def path_for(cls, day: date) -> str:
        return cls.dated_path(cls.dataset, day, cls.filename_for(day))

    @classmethod
    @abstractmethod
    def url_for(cls, path: str) -> str:
        """NSE's URL for an archive path."""

    def fetch(self, path: str) -> bytes | None:
        for wait in (*self.RETRY_WAITS, None):
            try:
                response = self.session.get(self.url_for(path), timeout=self.TIMEOUT_SECONDS)
            except requests.RequestException as exc:
                if wait is None:
                    raise RawSourceUnavailable(f"{self.name}: {path}: {exc}") from exc
                self.sleep(wait)
                continue
            if response.status_code == NOT_PUBLISHED:
                return None
            response.raise_for_status()
            return response.content
        raise AssertionError("unreachable")


class NseDailyFoSource(NseArchiveSource):
    """NSE's daily F&O file in the UDiFF format, served for every date from 1 January 2024."""

    dataset = "nse/derivatives/fo-bhavcopy"
    first_day = date(2024, 1, 1)
    BASE_URL = "https://nsearchives.nseindia.com/content/fo/"
    FILENAME = "BhavCopy_NSE_FO_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"

    @classmethod
    def url_for(cls, path: str) -> str:
        return cls.BASE_URL + path.rsplit("/", 1)[-1]


class NseLegacyFoSource(NseArchiveSource):
    """NSE's daily F&O file in the older format (served up to 5 July 2024), e.g. fo02JAN2019bhav.csv.zip. Its URL
    holds the year and month, read back from the archive path."""

    dataset = "nse/derivatives/fo-bhavcopy-legacy"
    first_day, last_day = date(2019, 1, 1), date(2024, 7, 5)  # the research needs nothing older than 2019
    BASE_URL = "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/"
    FILENAME = "fo{day:%d}{mon}{day:%Y}bhav.csv.zip"

    @classmethod
    def url_for(cls, path: str) -> str:
        filename = path.rsplit("/", 1)[-1]
        return f"{cls.BASE_URL}{filename[7:11]}/{filename[4:7]}/{filename}"


class NseIndexCloseSource(NseArchiveSource):
    """NSE's daily closing values of all its indices (NIFTY 50, NIFTY Bank, India VIX and the rest)."""

    dataset = "nse/indices/index-close"
    first_day = date(2019, 1, 1)
    BASE_URL = "https://nsearchives.nseindia.com/content/indices/"
    FILENAME = "ind_close_all_{day:%d%m%Y}.csv"

    @classmethod
    def url_for(cls, path: str) -> str:
        return cls.BASE_URL + path.rsplit("/", 1)[-1]
