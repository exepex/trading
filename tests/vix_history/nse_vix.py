"""Builds month files in NSE's India VIX history format (the shape of NSE's real answers, 14 Oct 2026)."""

import json
from datetime import date

from fno.storage.raw_source import RawFileSource


def nse_row(day: date, o, h, lo, c, name="INDIA VIX") -> dict:
    return {
        "EOD_TIMESTAMP": f"{day:%d-%b-%Y}".upper(),
        "EOD_INDEX_NAME": name,
        "EOD_OPEN_INDEX_VAL": o,
        "EOD_HIGH_INDEX_VAL": h,
        "EOD_LOW_INDEX_VAL": lo,
        "EOD_CLOSE_INDEX_VAL": c,
        "EOD_PREV_CLOSE": o,
        "VIX_PTS_CHG": 0.0,
        "VIX_PERC_CHG": 0.0,
        "HI_TIMESTAMP_ORDER": f"{day.isoformat()}T00:00:00.000Z",
    }


def month_file(rows: list[dict]) -> bytes:
    return json.dumps({"data": rows}, separators=(",", ":")).encode()


def july_2010(close_on_20th=20.38) -> bytes:
    return month_file(
        [
            nse_row(date(2010, 7, 19), 19.7, 20.87, 19.36, 20.71),
            nse_row(date(2010, 7, 20), 20.71, 20.71, 19.61, close_on_20th),
        ]
    )


def august_2010() -> bytes:
    return month_file([nse_row(date(2010, 8, 2), 18.94, 19.5, 18.1, 18.3025)])


class FakeNseVix(RawFileSource):
    """NSE's month files in memory by archive path; counts what was fetched."""

    dataset = "nse/indices/india-vix-history"

    def __init__(self, files: dict[str, bytes]):
        self.files, self.fetched = dict(files), []

    def fetch(self, path: str) -> bytes | None:
        self.fetched.append(path)
        return self.files.get(path)
