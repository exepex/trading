"""Official Euro Stoxx 50 and DAX closes, and Cboe's VIX (story A17e).

- STOXX (which calculates the Euro Stoxx 50 and the DAX) publishes a rolling three-month file per index without a
  login; its full history needs a licence, so history comes from Yahoo. STOXX's server sends an incomplete TLS chain
  (its intermediate certificate is missing), so the download trusts SSL.com's public intermediate, kept beside this
  module, on top of the usual bundle: that completes the chain the server should have sent and bypasses nothing.
- VIX from Cboe's delayed-quote history, A17's S&P 500 file layout (`CboeSp500Source`'s parser).

Values are private (Drive only, owner rule 50a79a43): an error never shows a level.
"""

from __future__ import annotations

import os
import tempfile
from datetime import date, datetime
from functools import cache
from pathlib import Path

import certifi
import requests

from .markets import CBOE_VIX, EURO_STOXX, FRANKFURT
from .source import TIMEOUT_SECONDS, CueRequest, CueValue, GlobalCueSource, checked, positive
from .us_index_sources import CboeSp500Source

STOXX_FILE = "https://www.stoxx.com/document/Indices/Current/HistoricalData/h_3m{symbol}.txt"
STOXX_HEADER = "Date;Symbol;Indexvalue;"
STOXX_INTERMEDIATE = Path(__file__).parent / "certs" / "sslcom_tls_issuing_rsa_ca_r1.pem"
CA_BUNDLE_VARIABLE = "REQUESTS_CA_BUNDLE"  # a proxy's bundle where one is set (as in cloud sessions)
CBOE_VIX_FILE = "https://cdn.cboe.com/api/global/delayed_quotes/charts/historical/_VIX.json"


class StoxxSource(GlobalCueSource):
    unit, private, date_zone = "index points", True, FRANKFURT.zone
    max_age_days = 4  # a Thursday close on Monday after Good Friday and Easter

    def __init__(self, cue: str, symbol: str, name: str, market=EURO_STOXX):
        self.cue, self.symbol, self.market = cue, symbol, market
        self.dataset = f"stoxx/indices/{symbol}-3m"
        self.publisher = f"STOXX Ltd. (calculates the {name}), three-month history file"
        self.first_value_date = date(2026, 7, 22)  # the oldest date of the first file read (21 Oct 2026)

    def requests(self, start: date, end: date) -> list[CueRequest]:
        return [CueRequest(f"h_3m{self.symbol}.txt", STOXX_FILE.format(symbol=self.symbol))]

    def download(self, session: requests.Session, request: CueRequest) -> bytes:
        response = session.get(request.url, timeout=TIMEOUT_SECONDS, verify=_bundle_with_intermediate())
        response.raise_for_status()
        return response.content

    def parse(self, data: bytes) -> list[CueValue]:
        lines = data.decode("utf-8", errors="replace").strip().splitlines()
        if not lines or lines[0].strip() != STOXX_HEADER:
            raise ValueError(f"{self.cue}: not STOXX's history file (header)")
        values = []
        for line in lines[1:]:
            day, symbol, level = (line.split(";") + ["", "", ""])[:3]
            if symbol.upper() != self.symbol.upper():
                raise ValueError(f"{self.cue}: a row of another index ({symbol!r}): layout changed")
            values.append(CueValue(datetime.strptime(day, "%d.%m.%Y").date(), positive(level, day, True)))
        return checked(values, self.cue)

    def available_at(self, value_date: date) -> datetime:
        return self.market.available_at(value_date)


class CboeVixSource(CboeSp500Source):
    cue, dataset = "vix_us", "cboe/indices/vix-history"
    publisher = "Cboe Global Markets (owner of the VIX), delayed-quote history"
    first_value_date = date(2019, 1, 1)
    holiday_rows = True  # 31 US market holidays 2022-2026 have a row (tested 21 Oct 2026): readings skip them

    def requests(self, start: date, end: date) -> list[CueRequest]:
        return [CueRequest("vix-history.json", CBOE_VIX_FILE)]

    def available_at(self, value_date: date) -> datetime:
        return CBOE_VIX.available_at(value_date)


@cache
def _bundle_with_intermediate() -> str:
    """The usual trusted roots plus SSL.com's intermediate, as one file for this process."""
    roots = Path(os.environ.get(CA_BUNDLE_VARIABLE) or certifi.where()).read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False, encoding="utf-8") as bundle:
        bundle.write(roots + "\n" + STOXX_INTERMEDIATE.read_text(encoding="utf-8"))
    return bundle.name
