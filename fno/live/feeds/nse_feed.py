"""Live F&O reference data from NSE's public website: lot sizes, ban list, holidays and open-interest moves."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime

from ...providers.public import PublicData, parse_nse_date

LOT_SIZES_URL = "https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv"
BAN_LIST_URL = "https://nsearchives.nseindia.com/content/fo/fo_secban.csv"
INDUSTRY_LIST_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
INDUSTRY_COLUMN, INDUSTRY_SYMBOL_COLUMN = "Industry", "Symbol"
COMPANY_NAME_COLUMN = "Company Name"
OI_SPURTS_PATH = "/api/live-analysis-oi-spurts-underlyings"
HOLIDAYS_PATH = "/api/holiday-master"
HOLIDAY_SEGMENT = "FO"
NOT_FOUND = 404
LOT_FILE_SYMBOL_COLUMN = 1
LOT_FILE_FIRST_MONTH_COLUMN = 2


@dataclass(frozen=True)
class OpenInterestMove:
    symbol: str
    oi_change_pct: float
    underlying_price: float
    traded_value: float  # rupees (lakhs in the feed are converted)


class NseLiveFeed:
    """Reads NSE reference and positioning data. Every method makes at most one request."""

    def __init__(self, client: PublicData | None = None):
        self.client = client or PublicData()

    def _archive_text(self, url: str) -> str:
        resp = self.client.session.get(url, timeout=20)
        resp.raise_for_status()
        return resp.text

    def archive_text_or_none(self, url: str) -> str | None:
        """An NSE archive file, or None when it does not exist (404: weekend, holiday, not published yet)."""
        resp = self.client.session.get(url, timeout=20)
        if resp.status_code == NOT_FOUND:
            return None
        resp.raise_for_status()
        return resp.text

    def lot_sizes(self) -> dict[str, int]:
        """Current-month lot size for every F&O underlying."""
        return parse_lot_sizes(self._archive_text(LOT_SIZES_URL))

    def ban_list(self) -> set[str]:
        """Securities in the F&O ban period today (no new positions allowed)."""
        return parse_ban_list(self._archive_text(BAN_LIST_URL))

    def industries(self) -> dict[str, str]:
        """NSE industry for each NIFTY 500 stock (covers almost every F&O stock)."""
        return parse_industries(self._archive_text(INDUSTRY_LIST_URL))

    def company_names(self) -> dict[str, str]:
        """NSE symbol -> company name for the NIFTY 500 (used to tag news headlines)."""
        return parse_company_names(self._archive_text(INDUSTRY_LIST_URL))

    def open_interest_moves(self) -> dict[str, OpenInterestMove]:
        return parse_oi_spurts(self.client.nse_json(OI_SPURTS_PATH))

    def trading_holidays(self) -> set[date]:
        data = self.client.nse_json(HOLIDAYS_PATH, {"type": "trading"})
        return {parse_nse_date(row["tradingDate"]) for row in data.get(HOLIDAY_SEGMENT, [])}


def parse_lot_sizes(text: str) -> dict[str, int]:
    sizes: dict[str, int] = {}
    rows = csv.reader(io.StringIO(text))
    next(rows, None)  # header
    for row in rows:
        if len(row) <= LOT_FILE_FIRST_MONTH_COLUMN:
            continue
        symbol = row[LOT_FILE_SYMBOL_COLUMN].strip()
        lot = row[LOT_FILE_FIRST_MONTH_COLUMN].strip()
        if symbol and lot.isdigit():
            sizes[symbol] = int(lot)
    return sizes


def parse_industries(text: str) -> dict[str, str]:
    return {
        row[INDUSTRY_SYMBOL_COLUMN].strip(): row[INDUSTRY_COLUMN].strip()
        for row in csv.DictReader(io.StringIO(text))
        if row.get(INDUSTRY_SYMBOL_COLUMN) and row.get(INDUSTRY_COLUMN)
    }


def parse_company_names(text: str) -> dict[str, str]:
    return {
        row[INDUSTRY_SYMBOL_COLUMN].strip(): row[COMPANY_NAME_COLUMN].strip()
        for row in csv.DictReader(io.StringIO(text))
        if row.get(INDUSTRY_SYMBOL_COLUMN) and row.get(COMPANY_NAME_COLUMN)
    }


def parse_ban_list(text: str) -> set[str]:
    """Lines look like '1,AMBUJACEM' after a title line."""
    banned = set()
    for line in text.splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[1]:
            banned.add(parts[1])
    return banned


def parse_oi_spurts(payload: dict) -> dict[str, OpenInterestMove]:
    moves = {}
    for row in payload.get("data", []):
        prev_oi, change = row.get("prevOI") or 0, row.get("changeInOI") or 0
        if not prev_oi:
            continue
        moves[row["symbol"]] = OpenInterestMove(
            symbol=row["symbol"],
            oi_change_pct=change / prev_oi * 100,
            underlying_price=float(row.get("underlyingValue") or 0),
            traded_value=float(row.get("total") or 0) * 1e5,  # feed reports rupees in lakhs
        )
    return moves


def feed_timestamp(payload: dict) -> datetime | None:
    stamp = payload.get("timestamp")
    try:
        return datetime.strptime(stamp, "%d-%b-%Y %H:%M:%S") if stamp else None
    except ValueError:
        return None
