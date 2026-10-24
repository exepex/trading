"""A22's morning capture in a rehearsal (story REH1c), behind its `PreopenPart` port: each part answers with the raw
answer the day saved for it (`preopen/raw/<day>/<part>_<HHMMSS>.json`, its seen time in its name), the first seen at
or just after now, once the replay clock reaches that time; the reading is the live part's own reader on those bytes.
A moment with no recorded answer is the capture's own failure (`PartFailed`), never a live read."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta

from ..models import IST
from ..preopen.answers import read_index_preopen
from ..preopen.parts import Answer, GrowwIndexPreopen, PartFailed, PreopenPart
from ..storage.receipts import ReceiptFolder

NEAREST = timedelta(minutes=10)
RAW_FOLDER = "data/preopen/raw/{day:%Y}/{day:%m}/{day:%d}"
NOT_RECORDED = "rehearsal:NOT_RECORDED {part} at {at}: the day saved no answer near then"


class RecordedPreopenPart(PreopenPart):
    def __init__(self, live: PreopenPart, receipts: ReceiptFolder, read: Callable[[str], bytes | None],
                 now: Callable[[], datetime], sleep: Callable[[float], None]):  # fmt: skip
        self.live, self.name, self.window = live, live.name, live.window
        self.receipts, self.read_file, self.now, self.sleep = receipts, read, now, sleep

    def answer(self, day: date) -> Answer:
        now = self.now()
        found = self._nearest_after(day, now)
        if found is None:
            raise PartFailed(NOT_RECORDED.format(part=self.name, at=now.isoformat()))
        path, seen = found
        if (wait := (seen - self.now()).total_seconds()) > 0:
            self.sleep(wait)
        raw = self.read_file(path)
        if raw is None:
            raise PartFailed(NOT_RECORDED.format(part=self.name, at=now.isoformat()))
        return Answer(raw, self._reading(raw, day, seen), seen)

    def _reading(self, raw: bytes, day: date, seen: datetime):
        if isinstance(self.live, GrowwIndexPreopen):
            return read_index_preopen(raw, day, self.name)
        return self.live.read(raw, day, seen)

    def _nearest_after(self, day: date, now: datetime) -> tuple[str, datetime] | None:
        folder = RAW_FOLDER.format(day=day)
        prefix = f"{folder}/{self.name}_"
        times = []
        for receipt in self.receipts.under(folder):
            if receipt.path.startswith(prefix) and receipt.path.endswith(".json"):
                stamp = receipt.path.removeprefix(prefix).removesuffix(".json")
                seen = datetime.combine(day, time(int(stamp[:2]), int(stamp[2:4]), int(stamp[4:6])), IST)
                if now - timedelta(seconds=5) <= seen <= now + NEAREST:
                    times.append((seen, receipt.path))
        return (min(times)[1], min(times)[0]) if times else None
