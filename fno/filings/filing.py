"""One company filing as an exchange lists it, and where its file lives in the archive (story A12).

`filed_at` is when the exchange made the filing public. NSE gives two times for a filing (its broadcast time and its
dissemination or creation time, seconds to minutes apart); the later one is kept, so a point-in-time reader never
uses a filing before it was surely public.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from ..constants import NSE_FILINGS_FOLDER


@dataclass(frozen=True)
class Filing:
    kind: str  # FILING_RESULTS or FILING_SHAREHOLDING
    symbol: str
    period_end: date
    filed_at: datetime  # IST, timezone-aware
    url: str  # the exchange's link to the filing's XBRL file
    consolidation: str = ""  # CONSOLIDATED or STANDALONE for results; empty for shareholding

    @property
    def filename(self) -> str:
        return self.url.rsplit("/", 1)[-1]

    @property
    def path(self) -> str:
        return filing_path(self.kind, self.symbol, self.filename)


def company_folder(kind: str, symbol: str) -> str:
    """`nse/equities/filings/<kind>/<SYMBOL>`: one folder per company and filing type."""
    return f"{NSE_FILINGS_FOLDER}/{kind}/{symbol}"


def filing_path(kind: str, symbol: str, filename: str) -> str:
    """`<company folder>/<original file name>`: NSE's own file name kept."""
    return f"{company_folder(kind, symbol)}/{filename}"


@dataclass(frozen=True)
class FilingGap:
    """A company and filing type the archive cannot hold in full, with the reason (never a silent skip)."""

    symbol: str
    kind: str
    reason: str
