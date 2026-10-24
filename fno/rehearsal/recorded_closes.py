"""A4h's index-list read in a rehearsal (story REH1b), behind its `CloseListSource`: the answer NSE gave on the day,
read back from the real record. The real reader saved its raw answer seconds after asking, so the answer served is the
day's first recorded raw answer saved at or after now (within `NEAREST`), once the replay clock reaches its save time:
the 15:40 read gets the first answer, the 16:00 recheck the recheck. Any other moment is not recorded."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, timedelta

from ..close_read.source import CloseListSource
from ..storage.receipts import ReceiptFolder

NEAREST = timedelta(minutes=10)
RAW_SUFFIX = ".raw.json"
NOT_RECORDED = "rehearsal:NOT_RECORDED NSE's index list at {at}: no recorded answer saved within 10 minutes of it"


class RecordedAnswerMissing(RuntimeError):
    """No answer of the day was recorded near this moment, or its raw file is not in the record."""


class RecordedCloseList(CloseListSource):
    def __init__(self, receipts: ReceiptFolder, read: Callable[[str], bytes | None], now: Callable[[], datetime],
                 sleep: Callable[[float], None]):  # fmt: skip
        self.receipts, self.read, self.now, self.sleep = receipts, read, now, sleep

    def answer(self) -> tuple[dict, bytes]:
        now = self.now()
        found = self._nearest_after(now, now.date())
        if found is None:
            raise RecordedAnswerMissing(NOT_RECORDED.format(at=now.isoformat()))
        path, saved = found
        if (wait := (saved - self.now()).total_seconds()) > 0:
            self.sleep(wait)
        raw = self.read(path)
        if raw is None:
            raise RecordedAnswerMissing(NOT_RECORDED.format(at=now.isoformat()))
        return json.loads(raw), raw

    def _nearest_after(self, now: datetime, day: date) -> tuple[str, datetime] | None:
        prefix = f"data/closes/{day:%Y}/{day:%m}/{day.isoformat()}."
        saved = [(r.path, datetime.fromisoformat(r.written_at)) for r in self.receipts.under(prefix.rsplit("/", 1)[0])
                 if r.path.startswith(prefix) and r.path.endswith(RAW_SUFFIX)]  # fmt: skip
        later = sorted((at, path) for path, at in saved if now - timedelta(seconds=5) <= at <= now + NEAREST)
        return (later[0][1], later[0][0]) if later else None
