"""The official/Yahoo comparison per index (story A17e), like A17d's RBI/FBIL overlap: every date both have where the
closes differ by more than `TOLERANCE`, and every date inside both tables' shared span that only one has (a session
missing from one publisher). Dates and kinds only, never a value; the rows go to the official cue's private checks in
Drive and only the counts are printed (the values are private, owner rule 50a79a43)."""

from __future__ import annotations

from collections import Counter

PAIR_FIELDS = ("index", "date", "kind")
DIFFERS, ONLY_OFFICIAL, ONLY_YAHOO = "differs_over_0.1pct", "only_official", "only_yahoo"
TOLERANCE = 0.001  # 0.1 percent: rounding between publishers stays far below it (Nikkei, SSE: equal to the cent)


def pair_rows(index: str, official: list[dict[str, str]], yahoo: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    ours, theirs = _by_date(official), _by_date(yahoo)
    if not ours or not theirs:
        return []
    first, last = max(min(ours), min(theirs)), min(max(ours), max(theirs))
    shared = sorted(set(ours) & set(theirs))
    found = [(index, day, DIFFERS) for day in shared if abs(theirs[day] - ours[day]) > TOLERANCE * ours[day]]
    found += [(index, day, ONLY_OFFICIAL) for day in sorted(set(ours) - set(theirs)) if first <= day <= last]
    found += [(index, day, ONLY_YAHOO) for day in sorted(set(theirs) - set(ours)) if first <= day <= last]
    return sorted(found, key=lambda r: (r[1], r[2]))


def pair_summary(index: str, rows: list[tuple[str, str, str]], compared: int) -> str:
    kinds = dict(Counter(kind for _, _, kind in rows)) or "no difference"
    return f"{index} official against Yahoo: {compared} dates compared, {kinds}"


def compared_dates(official: list[dict[str, str]], yahoo: list[dict[str, str]]) -> int:
    return len(set(_by_date(official)) & set(_by_date(yahoo)))


def _by_date(rows: list[dict[str, str]]) -> dict[str, float]:
    return {r["value_date"]: float(r["value"]) for r in rows}
