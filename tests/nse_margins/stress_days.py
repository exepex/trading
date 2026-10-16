"""Planted daily SPAN files for story A14c's tests: one file per weekday with the span builder's SF arrays scaled by a
chosen factor, so a held SF 100's whole margin on day d is 1,950 x scale(d) + 52,000 a lot (scan 30 a unit x scale x
65, plus exposure 2 x 2% x 20,000 x 65; the premium nets out of what C2 counts)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from datetime import date, timedelta

from fno.nse_margins.calculator import NseIndexOptionExposure, SpanMarginCalculator
from fno.nse_margins.held_rise import HeldRiseTracker
from fno.research_engine.structures import ShortIronFly

from .span_builder import EXPIRY, LOT, SF_ARRAYS, default_options, risk, span_zip

FIRST = date(2026, 10, 1)  # entries 1-23 Oct take the 23 Nov expiry (30+ days); exit Mon 2 Nov (21+ days before)
EXPIRY2 = date(2026, 12, 28)  # entries from 26 Oct take it; exit Mon 7 Dec
BASE_MARGIN = 1950 + 52_000  # SF 100 at scale 1


def weekday(day: date) -> bool:
    return day.weekday() < 5


def margin(scale: float) -> float:
    return 1950 * scale + 52_000


def day_bytes(day: date, scale: float, created: str | None = None) -> bytes:
    options = default_options()
    options.update({c: risk({k: v * scale for k, v in arrays.items()}) for c, arrays in SF_ARRAYS.items()})
    stamp = created or f"{day - timedelta(days=1):%Y%m%d}2128"
    futures = (date(2026, 10, 27), EXPIRY, EXPIRY2)
    return span_zip(member=f"nsccl.{day:%Y%m%d}.i1.spn", created=stamp, futures=futures,
                    series={EXPIRY: options, EXPIRY2: options})  # fmt: skip


def planted(last: date, scales: Mapping[date, float] | None = None) -> dict[date, bytes]:
    """A file for every weekday from FIRST through `last` (scale 1 unless `scales` says otherwise)."""
    files, day = {}, FIRST
    while day <= last:
        if weekday(day):
            files[day] = day_bytes(day, (scales or {}).get(day, 1.0))
        day += timedelta(days=1)
    return files


def manifest(files: Mapping[date, bytes]) -> dict[date, str]:
    return {day: hashlib.sha256(data).hexdigest() for day, data in files.items()}


def sf_tracker() -> HeldRiseTracker:
    return HeldRiseTracker((ShortIronFly(),), lambda _: (100.0,), SpanMarginCalculator(NseIndexOptionExposure(), LOT),
                           weekday)  # fmt: skip


def day_file(files: Mapping[date, bytes]) -> Callable[[date], tuple[str, bytes | None]]:
    return lambda day: (f"nsccl.{day:%Y%m%d}.i1.zip", files.get(day))
