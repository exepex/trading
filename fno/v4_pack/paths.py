"""Where a day's pack and its release record live in Drive's data area (story G10 part 2, sections 1-2); GitHub holds
each one's receipt under `receipts/` (story O9)."""

from __future__ import annotations

from datetime import date

PACK_PATH = "v4/packs/{year}/{day}.json"
RELEASE_PATH = "v4/days/{year}/{day}.json"


def pack_path(day: date) -> str:
    return PACK_PATH.format(year=day.year, day=day.isoformat())


def release_path(day: date) -> str:
    return RELEASE_PATH.format(year=day.year, day=day.isoformat())
