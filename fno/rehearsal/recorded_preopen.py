"""A22's morning capture in a rehearsal (story REH1c), behind its `PreopenPart` port: each part answers with the raw
answer the day saved for it (`preopen/raw/<day>/<part>_<HHMMSS>.json`, its seen time in its name), the one seen
nearest to now and never the same answer twice (`serving.ServedOnce`: a 30-second retry gets the day's next answer,
not the last one again), once the replay clock reaches that time; the reading is the live part's own reader on those
bytes. The bytes must hash to the receipt's SHA-256 (judge 563 SF1), as every recorded source checks its record. A
moment with no recorded answer, or a copy that differs from its receipt, is the capture's own failure (`PartFailed`),
never a live read."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import date, datetime, time

from ..models import IST
from ..preopen.answers import read_index_preopen
from ..preopen.parts import Answer, GrowwIndexPreopen, PartFailed, PreopenPart
from ..storage.receipts import ReceiptFolder
from .serving import ServedOnce

RAW_FOLDER = "data/preopen/raw/{day:%Y}/{day:%m}/{day:%d}"
NOT_RECORDED = "rehearsal:NOT_RECORDED {part} at {at}: the day saved no answer near then"
DAMAGED = "rehearsal: the recorded answer {path} is missing from Drive or differs from its receipt"


class RecordedPreopenPart(PreopenPart):
    def __init__(self, live: PreopenPart, receipts: ReceiptFolder, read: Callable[[str], bytes | None],
                 now: Callable[[], datetime], sleep: Callable[[float], None]):  # fmt: skip
        self.live, self.name, self.window = live, live.name, live.window
        self.receipts, self.read_file, self.now, self.sleep = receipts, read, now, sleep
        self.served = ServedOnce()

    def answer(self, day: date) -> Answer:
        now = self.now()
        found = self._nearest(day, now)
        if found is None:
            raise PartFailed(NOT_RECORDED.format(part=self.name, at=now.isoformat()))
        path, seen, sha256 = found
        if (wait := (seen - self.now()).total_seconds()) > 0:
            self.sleep(wait)
        raw = self.read_file(path)
        if raw is None or hashlib.sha256(raw).hexdigest() != sha256:
            raise PartFailed(DAMAGED.format(path=path))
        return Answer(raw, self._reading(raw, day, seen), seen)

    def _reading(self, raw: bytes, day: date, seen: datetime):
        if isinstance(self.live, GrowwIndexPreopen):
            return read_index_preopen(raw, day, self.name)
        return self.live.read(raw, day, seen)

    def _nearest(self, day: date, now: datetime) -> tuple[str, datetime, str] | None:
        folder = RAW_FOLDER.format(day=day)
        prefix = f"{folder}/{self.name}_"
        saved = {r.path: r.sha256 for r in self.receipts.under(folder)
                 if r.path.startswith(prefix) and r.path.endswith(".json")}  # fmt: skip
        picked = self.served.pick(now, ((_seen(day, path.removeprefix(prefix)), path) for path in saved))
        if picked is None:
            return None
        seen, path = picked
        return path, seen, saved[path]


def _seen(day: date, name: str) -> datetime:
    """The seen time in an answer's name (`HHMMSS.json`)."""
    return datetime.combine(day, time(int(name[:2]), int(name[2:4]), int(name[4:6])), IST)
