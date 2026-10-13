"""The AI books' clock (protocol v2 section 5, applied to Books 2 and 3): the commitment counts only if GitHub logged
its push by 15:15:00 IST (the same deadline as `ForecastRecordV2.on_time`); the reveal waits until a few seconds after
it, so no book's answer is readable before every commitment is in; the collection waits for reveals until 15:30."""

from __future__ import annotations

from datetime import date, datetime, time

from ..forecast.schema_v2 import GENERATION_DEADLINE
from ..models import IST

REVEAL_FROM = time(15, 15, 10)  # 10 s after the deadline: a little clock drift cannot open an answer early
REVEAL_DEADLINE = time(15, 30)


def receipt_deadline(day: date) -> datetime:
    return datetime.combine(day, GENERATION_DEADLINE, tzinfo=IST)


def reveal_from(day: date) -> datetime:
    return datetime.combine(day, REVEAL_FROM, tzinfo=IST)


def reveal_deadline(day: date) -> datetime:
    return datetime.combine(day, REVEAL_DEADLINE, tzinfo=IST)
