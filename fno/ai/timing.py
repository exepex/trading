"""The AI books' clock (protocol v2 section 5, applied to Books 2 and 3): the commitment counts only if GitHub logged
its push by 15:15:00 IST (the same deadline as `ForecastRecordV2.on_time`); the reveal waits until a few seconds after
it, so no book's answer is readable before every commitment is in; the collection waits for reveals until 15:30. A run
that starts after 15:13 (the capture's last pull for the snapshot) can only give late answers: it fires no AI book."""

from __future__ import annotations

from datetime import date, datetime, time

from ..forecast.schema_v2 import GENERATION_DEADLINE
from ..models import IST

REVEAL_FROM = time(15, 15, 10)  # 10 s after the deadline: a little clock drift cannot open an answer early
REVEAL_DEADLINE = time(15, 30)
LATEST_START = time(15, 13)  # protocol v2 section 5: the capture pulls for the snapshot until 15:13 IST at most


def receipt_deadline(day: date) -> datetime:
    return datetime.combine(day, GENERATION_DEADLINE, tzinfo=IST)


def reveal_from(day: date) -> datetime:
    return datetime.combine(day, REVEAL_FROM, tzinfo=IST)


def reveal_deadline(day: date) -> datetime:
    return datetime.combine(day, REVEAL_DEADLINE, tzinfo=IST)


def latest_start(day: date) -> datetime:
    return datetime.combine(day, LATEST_START, tzinfo=IST)
