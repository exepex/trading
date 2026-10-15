"""The interface every global cue sits behind (story A17), and the shapes it returns.

A source names the files to download for a range of value dates, downloads one, and reads its bytes into dated values
(ValueError when the bytes are not the publisher's file: an error page, a cut answer, a changed layout). It knows its
own publisher, units, the time zone its dates are in and how late it publishes, so the README and the as-of rule can
state them. Adding a source is one new class plus one line in `wiring.py`.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

import requests

TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class CueRequest:
    name: str  # the archived file's name (the publisher's own where it has one)
    url: str
    form: tuple[tuple[str, str], ...] = ()  # fields posted to the URL, for a publisher that answers a form


@dataclass(frozen=True)
class CueValue:
    value_date: date  # the publisher's date for the value, in its own time zone (`GlobalCueSource.date_zone`)
    value: float


class GlobalCueSource(ABC):
    cue: str = ""  # the table's name, e.g. "sp500"
    dataset: str = ""  # raw archive folder: "<publisher>/<market>/<dataset>"
    publisher: str = ""
    unit: str = ""
    date_zone: str = ""  # the time zone the publisher's dates are in
    first_value_date: date = date(2007, 1, 1)  # how far back the back-fill asks

    @abstractmethod
    def requests(self, start: date, end: date) -> list[CueRequest]:
        """The files that hold every value dated from start to end."""

    def download(self, session: requests.Session, request: CueRequest) -> bytes:
        """The file's bytes (requests.RequestException on a failure); a plain GET unless the publisher needs more."""
        response = session.get(request.url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.content

    @abstractmethod
    def parse(self, data: bytes) -> list[CueValue]:
        """Every value in the file (ValueError when it is not the publisher's file)."""


def positive(text, what: str) -> float:
    """A published level as a number: refuses anything that is not a finite number above zero."""
    try:
        value = float(str(text).replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"{what}: {text!r} is not a number") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{what}: {text!r} is not a positive number")
    return value


def checked(values: list[CueValue], what: str) -> list[CueValue]:
    """Values in date order; refuses an empty file and a date given twice."""
    if not values:
        raise ValueError(f"{what}: no values in the file")
    days = [v.value_date for v in values]
    if len(set(days)) != len(days):
        raise ValueError(f"{what}: a date is given twice")
    return sorted(values, key=lambda v: v.value_date)
