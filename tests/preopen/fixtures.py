"""Answers in the layouts NSE and Groww served on 21 Oct 2026 (step 0), cut down, every number invented: no market
value enters the repository."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta

from fno.models import IST

DAY = date(2026, 10, 22)  # a regular Thursday session


def ist(hour: int, minute: int = 0, second: int = 0, day: date = DAY) -> datetime:
    return datetime.combine(day, time(hour, minute, second), IST)


def gift(stamp: str = "22-Oct-2026 08:39", level: float = 1234.5) -> bytes:
    block = {"instrumenttype": "FUTIDX", "symbol": "NIFTY", "expirydate": "27-Oct-2026", "optiontype": "-",
             "strikeprice": 0, "lastprice": level, "daychange": 1, "perchange": 0.1, "contractstraded": 4321,
             "timestmp": stamp, "id": "0/NIFTYFUTIDX27-Oct-2026--"}  # fmt: skip
    usd = {"symbol": "USDINR", "updated_time": "22-Oct-2026 08:30", "ltp": "11.11"}
    return json.dumps(
        {"data": {"marketCapitalization": {}, "indexList": [], "usdInr": usd, "giftNifty": block}}
    ).encode()


def fo_list(stamp: str = "22-Oct-2026 09:08:43", ieps: tuple = (101.5, 202.25, 0)) -> bytes:
    data = [{"metadata": {"symbol": f"S{i}", "series": "EQ", "lastPrice": iep, "previousClose": 1.0, "iep": iep,
                          "finalQuantity": 10},
             "detail": {"preOpenMarket": {"IEP": iep, "lastUpdateTime": stamp, "preopen": []}}}
            for i, iep in enumerate(ieps)]  # fmt: skip
    return json.dumps({"declines": 1, "unchanged": 0, "advances": 2, "timestamp": stamp, "data": data}).encode()


def candles(first: time = time(9, 0), count: int = 10, day: date = DAY, close_0909: float = 5555.5) -> bytes:
    """Groww's 1-minute rows: start time (IST, no offset), open, high, low, close, volume, open interest."""
    rows = []
    for n in range(count):
        start = datetime.combine(day, first) + timedelta(minutes=n)
        close = close_0909 if start.time() == time(9, 9) else 1000.0 + n
        rows.append([start.isoformat(), close, close, close, close, 0, None])
    return json.dumps({"candles": rows}, sort_keys=True, separators=(",", ":")).encode()
