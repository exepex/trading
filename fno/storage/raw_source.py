"""Where raw files originally come from (an exchange archive, a data vendor). Each source knows only its own
naming and transport; callers see one interface."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import date

import requests

NOT_PUBLISHED = 404


class RawSourceUnavailable(RuntimeError):
    """The source could not be reached (after retries); try again later. Not the same as "no such file"."""


class RawFileSource(ABC):
    name: str = "source"
    dataset: str = ""  # archive folder of this source's files: "<publisher>/<market>/<dataset>"

    @abstractmethod
    def fetch(self, path: str) -> bytes | None:
        """The file at an archive path; None when the source does not publish it; RawSourceUnavailable on a failure."""

    @staticmethod
    def dated_path(dataset: str, day: date, filename: str) -> str:
        """`<dataset>/<YYYY>/<MM>/<original file name>`: one folder per month, original names kept."""
        return f"{dataset}/{day:%Y}/{day:%m}/{filename}"


class NseDailyFoSource(RawFileSource):
    """NSE's daily F&O file (UDiFF format, served for every date from January 2024), through a polite session."""

    name = "NSE archive"
    dataset = "nse/derivatives/fo-bhavcopy"
    BASE_URL = "https://nsearchives.nseindia.com/content/fo/"
    FILENAME = "BhavCopy_NSE_FO_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"
    RETRY_WAITS = (5, 15, 45)  # seconds before each retry of a dropped connection
    TIMEOUT_SECONDS = 60

    def __init__(self, session: requests.Session, sleep=time.sleep):
        self.session, self.sleep = session, sleep

    @classmethod
    def path_for(cls, day: date) -> str:
        return cls.dated_path(cls.dataset, day, cls.FILENAME.format(day=day))

    @classmethod
    def url_for(cls, path: str) -> str:
        return cls.BASE_URL + path.rsplit("/", 1)[-1]

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
