"""A cue source in memory, and builders of the publishers' file layouts as seen on 15 Oct 2026."""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import requests

from fno.global_cues.archived_copies import COPY_TIME
from fno.global_cues.source import CueRequest, CueValue, GlobalCueSource, checked, positive
from fno.global_cues.table import CueTable
from fno.models import IST
from fno.storage.creation_times import CreationTimes
from fno.storage.row_log import CsvRowLog


class FakeSource(GlobalCueSource):
    """Files by name, `date,value` lines; a name mapped to an exception raises it on download."""

    cue, dataset, unit, date_zone = "fake", "test/cues/fake", "points", "UTC"

    def __init__(self, files: dict):
        self.files = files

    def requests(self, start: date, end: date) -> list[CueRequest]:
        return [CueRequest(name, f"https://example.test/{name}") for name in self.files]

    def download(self, session, request: CueRequest) -> bytes:
        found = self.files[request.name]
        if isinstance(found, Exception):
            raise found
        return found

    def available_at(self, value_date: date) -> datetime:
        return datetime.combine(value_date + timedelta(days=1), time(2, 30), tzinfo=IST)

    def parse(self, data: bytes) -> list[CueValue]:
        if not data.startswith(b"date,value"):
            raise ValueError("not the fake publisher's file")
        rows = [line.split(",") for line in data.decode().splitlines()[1:]]
        return checked([CueValue(date.fromisoformat(d), positive(v, d)) for d, v in rows], self.cue)


class FakeCreationTimes(CreationTimes):
    """A store's creation time: `after` the time in the copy's own path (an upload seconds after its fetch)."""

    def __init__(self, after: timedelta = timedelta(seconds=9)):
        self.after = after

    def created_at(self, path: str) -> datetime | None:
        stamp = "/".join(path.split("/")[-4:])[:17]
        return datetime.strptime(stamp, COPY_TIME).replace(tzinfo=IST) + self.after


def fake_file(*rows: tuple[str, float]) -> bytes:
    return ("date,value\n" + "\n".join(f"{d},{v}" for d, v in rows)).encode()


REFUSED = requests.ConnectionError("connection reset")


TREASURY = b'Date,"1 Mo","10 Yr","30 Yr"\n10/14/2026,4.11,5.19,5.52\n10/13/2026,4.10,,5.56\n10/09/2026,4.0,5.25,5.6\n'

EIA = (
    b"<title>Europe Brent Spot Price FOB (Dollars per Barrel)</title><table>"
    b"<tr> <td class='B6'>&nbsp;&nbsp;2025 Dec-29 to Jan- 2</td> <td class='B3'>61.10</td> <td class='B3'>62.00</td>"
    b" <td class='B3'></td> <td class='B3'></td> <td class='B3'>60.75</td> </tr>"
    b"<tr> <td class='B6'>&nbsp;&nbsp;2026 Oct- 5 to Oct- 9</td> <td class='B3'>125.51</td> <td class='B3'>125.44</td>"
    b" <td class='B3'></td> <td class='B3'></td> <td class='B3'></td> </tr></table>"
)

RBI = (
    b'<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="abc" />'
    b'<table><tr><td class="tableheader"><b>Date</b></td><td class="tableheader"> <b>USD (INR / 1 USD) </b></td></tr>'
    b'<tr><td height="20" >14/10/2026</td><td height="20" align="right">95.0317</td></tr>'
    b'<tr><td height="20" >13/10/2026</td><td height="20" align="right">95.2477</td></tr></table>'
)


def fbil(*rows) -> bytes:
    items = []
    for day, usd in rows:
        stamp = f"{day} 00:00:00"
        items.append({"processRunDate": stamp, "subProdName": "INR / 1 USD", "displayTime": stamp, "rate": usd})
        items.append({"processRunDate": stamp, "subProdName": "INR / 1 EUR", "displayTime": stamp, "rate": 108.4})
    return json.dumps(items).encode()


def csv_table(folder, cue: str, next_session) -> CueTable:
    """A cue table in a local folder, with the folder's shared revision log (the public cues' layout)."""
    folder = Path(folder)
    return CueTable(cue, CsvRowLog(folder / f"{cue}.csv"), CsvRowLog(folder / "revisions.csv"), next_session)


def cboe(*rows) -> bytes:
    """Cboe's SPX history layout with made-up closes (fake values: no real index level is in this repository)."""
    data = [{"date": d, "volume": "0.0", "open": "0", "high": c, "low": c, "close": f"{c:.6f}"} for d, c in rows]
    return json.dumps({"timestamp": "2026-10-15 00:09:18", "data": data}).encode()


def nasdaq(rows, total=None) -> bytes:
    """Nasdaq's quote-API layout with made-up closes (fake values)."""
    table = [{"date": d, "close": c, "volume": "--", "open": c, "high": c, "low": c} for d, c in rows]
    total = len(rows) if total is None else total
    return json.dumps({"data": {"symbol": "NDX", "totalRecords": total, "tradesTable": {"rows": table}}}).encode()
