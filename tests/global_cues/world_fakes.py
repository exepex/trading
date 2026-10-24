"""Story A17e: the world publishers' answer layouts as read on 21 Oct 2026, with made-up levels (no real index value is
in this repository: owner rule 50a79a43), and a session that answers one canned HTTP response and counts requests."""

import json
from datetime import UTC, date, datetime, time

import requests


def yahoo_chart(zone: str, rows, symbol: str = "^N225") -> bytes:
    """`rows`: (UTC timestamp, close or None) pairs."""
    result = {
        "meta": {"symbol": symbol, "exchangeTimezoneName": zone},
        "timestamp": [stamp for stamp, _ in rows],
        "indicators": {"quote": [{"close": [close for _, close in rows]}]},
    }
    return json.dumps({"chart": {"result": [result], "error": None}}).encode()


def utc(day: date, at: time) -> int:
    return int(datetime.combine(day, at, tzinfo=UTC).timestamp())


def csindex(*rows) -> bytes:
    data = [{"tradeDate": d, "indexCode": "000001", "close": c, "open": c} for d, c in rows]
    return json.dumps({"code": "200", "msg": "Success", "data": data}).encode()


def twse(*rows) -> bytes:
    return json.dumps([{"Date": d, "OpeningIndex": c, "ClosingIndex": c} for d, c in rows]).encode()


NIKKEI = (
    b'Date of Data,Close,Open,High,Low\r\n"2026/10/20","100.50","100.00","101.00","99.00"\r\n'
    b'"2026/10/21","101.25","100.50","102.00","100.00"\r\n"This material is a copyrightable work of Nikkei. It is '
    b"prohibited to copy, reproduce, reprint, or circulate all or part of this material in any form "
    b'without Nikkei\x81fs permission."\r\n'
)


def stoxx(symbol: str, *rows) -> bytes:
    return ("Date;Symbol;Indexvalue;\n" + "".join(f"{d};{symbol};{c};\n" for d, c in rows)).encode()


class CannedResponse(requests.Response):
    def __init__(self, status: int, body: bytes, location: str | None = None):
        super().__init__()
        self.status_code, self._content, self.url = status, body, "https://query1.finance.yahoo.com/v8/finance/chart/x"
        if location:
            self.headers["Location"] = location


class CountingSession(requests.Session):
    """Answers every GET with one canned response and records each call's arguments."""

    def __init__(self, response: CannedResponse):
        super().__init__()
        self.response, self.calls = response, []

    def get(self, url, **kwargs):
        self.calls.append((url, dict(self.headers), kwargs))
        return self.response
