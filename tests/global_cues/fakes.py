"""A cue source in memory, and builders of the publishers' file layouts as seen on 15 Oct 2026."""

import json
from datetime import date

import requests

from fno.global_cues.source import CueRequest, CueValue, GlobalCueSource, checked, positive


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

    def parse(self, data: bytes) -> list[CueValue]:
        if not data.startswith(b"date,value"):
            raise ValueError("not the fake publisher's file")
        rows = [line.split(",") for line in data.decode().splitlines()[1:]]
        return checked([CueValue(date.fromisoformat(d), positive(v, d)) for d, v in rows], self.cue)


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
