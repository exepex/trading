"""A4h's close read as the evening's `TodayCloses` (story FL1-1d; A4h merged 22 Oct): the day's record
(`closes/<yyyy>/<mm>/<day>.json`, else the 16:00 recheck), each read by its own receipt and verified (FL1-1e). A
value is used only when NSE stamped the list that day at or after 15:30, and only for an index whose list value is
its official close (NIFTY 50 and NIFTY BANK; never INDIA VIX). It stays labelled provisional until the next morning
confirms it."""

from __future__ import annotations

import json
from datetime import date, datetime

from ..close_read.constants import DATA_AREA, STAMP_FORMAT, STAMP_FROM
from ..close_read.records import recheck_path, record_path
from .ranges import TodayCloses
from .verified_file import Unverified, VerifiedFiles

LISTED = {"NIFTY": "NIFTY 50", "BANKNIFTY": "NIFTY BANK"}
NOT_READ = "A4h has no close read of {day} stamped after 15:30 (its 15:40 read, its 16:00 recheck)"
UNREADABLE = "A4h's record could not be read verified ({problems})"


class A4hTodayCloses(TodayCloses):
    def __init__(self, files: VerifiedFiles):
        self.files, self.problems = files, {}

    def _document(self, day: date) -> dict | None:
        """The day's first record that reads verified; a damaged one is remembered for `why_missing`."""
        for path in (record_path(day), recheck_path(day)):
            try:
                data = self.files.read(f"{DATA_AREA}/{path}")
            except Unverified as error:
                self.problems.setdefault(day, []).append(str(error))
                continue
            if data is not None:
                return json.loads(data)
        return None

    @staticmethod
    def _stamped(document: dict, day: date) -> bool:
        try:
            stamp = datetime.strptime(document.get("nse_stamp") or "", STAMP_FORMAT)
        except ValueError:
            return False
        return stamp.date() == day and stamp.time() >= STAMP_FROM

    def close(self, underlying: str, day: date) -> float | None:
        document = self._document(day)
        if document is None or not self._stamped(document, day):
            return None
        index = (document.get("indices") or {}).get(LISTED.get(underlying, ""), {})
        if index.get("official_close") is False:
            return None
        last = index.get("last")
        return float(last) if last is not None else None

    def why_missing(self, day: date) -> str:
        problems = self.problems.get(day)
        return UNREADABLE.format(problems="; ".join(problems)) if problems else NOT_READ.format(day=day)
