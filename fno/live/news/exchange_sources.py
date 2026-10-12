"""Company filings straight from the exchanges: the origin of most single-stock news.

Read from the owner's PC only, about once a minute (a person refreshing the page does the same). NSE's and BSE's
website terms discourage automated use; if either refuses us, the pacer pauses it and the other sources carry on.
"""

from __future__ import annotations

from datetime import datetime

import requests

from ...models import IST
from ...providers.public import PublicData
from .models import NewsItem
from .source import NewsSource

NSE_SOURCE = "NSE filings"
NSE_ANNOUNCEMENTS_PATH = "/api/corporate-announcements"
NSE_ANNOUNCEMENTS_PARAMS = {"index": "equities"}
NSE_ATTACHMENT_FIELD = "attchmntFile"
NSE_TIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%d-%b-%Y %H:%M:%S")
BSE_SOURCE = "BSE filings"
BSE_ANNOUNCEMENTS_URL = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
BSE_HEADERS = {"Referer": "https://www.bseindia.com/", "Origin": "https://www.bseindia.com"}
BSE_DATE_FORMAT = "%Y%m%d"
REQUEST_TIMEOUT_SECONDS = 20
TITLE_TEMPLATE = "{company}: {subject}"


def _nse_time(row: dict) -> datetime | None:
    for field in ("sort_date", "an_dt", "exchdisstime"):
        text = (row.get(field) or "").strip()
        for fmt in NSE_TIME_FORMATS:
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=IST)
            except ValueError:
                continue
    return None


def parse_nse_announcements(payload) -> list[NewsItem]:
    rows = payload if isinstance(payload, list) else (payload or {}).get("data", [])
    items = []
    for row in rows:
        subject = (row.get("attchmntText") or row.get("desc") or "").strip()
        symbol = (row.get("symbol") or "").strip().upper()
        if not subject or not symbol:
            continue
        company = (row.get("sm_name") or symbol).strip()
        items.append(
            NewsItem(
                source=NSE_SOURCE,
                title=TITLE_TEMPLATE.format(company=company, subject=subject),
                url=(row.get(NSE_ATTACHMENT_FIELD) or "").strip(),
                published_at=_nse_time(row),
                summary=(row.get("desc") or "").strip(),
                symbols=(symbol,),
            )
        )
    return items


class NseAnnouncementsSource(NewsSource):
    name = NSE_SOURCE

    def __init__(self, client: PublicData):
        self.client = client

    def fetch(self, now: datetime) -> list[NewsItem]:
        return parse_nse_announcements(self.client.nse_json(NSE_ANNOUNCEMENTS_PATH, NSE_ANNOUNCEMENTS_PARAMS))


def _bse_symbol(page_url: str) -> tuple[str, ...]:
    """BSE company pages look like .../stock-share-price/<name>/<nse-like-symbol>/<code>/."""
    parts = [p for p in (page_url or "").split("/") if p]
    return (parts[-2].upper(),) if len(parts) >= 3 and not parts[-2].isdigit() else ()


def parse_bse_announcements(payload: dict) -> list[NewsItem]:
    items = []
    for row in (payload or {}).get("Table", []):
        subject = (row.get("HEADLINE") or row.get("NEWSSUB") or "").strip()
        if not subject:
            continue
        company = (row.get("SLONGNAME") or "").strip()
        stamp = (row.get("DissemDT") or row.get("NEWS_DT") or "").strip()
        try:
            published = datetime.fromisoformat(stamp).replace(tzinfo=IST) if stamp else None
        except ValueError:
            published = None
        items.append(
            NewsItem(
                source=BSE_SOURCE,
                title=TITLE_TEMPLATE.format(company=company, subject=subject) if company else subject,
                url=(row.get("NSURL") or "").strip(),
                published_at=published,
                summary=(row.get("CATEGORYNAME") or "").strip(),
                symbols=_bse_symbol(row.get("NSURL") or ""),
            )
        )
    return items


class BseAnnouncementsSource(NewsSource):
    name = BSE_SOURCE

    def __init__(self, session: requests.Session):
        self.session = session

    def fetch(self, now: datetime) -> list[NewsItem]:
        today = now.astimezone(IST).strftime(BSE_DATE_FORMAT)
        params = {
            "pageno": 1,
            "strCat": -1,
            "strPrevDate": today,
            "strScrip": "",
            "strSearch": "P",
            "strToDate": today,
            "strType": "C",
            "subcategory": -1,
        }
        resp = self.session.get(
            BSE_ANNOUNCEMENTS_URL, params=params, headers=BSE_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        return parse_bse_announcements(resp.json())
