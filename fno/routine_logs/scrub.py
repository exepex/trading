"""Removes every value the public-record scan would refuse (story O5's patterns) before a log leaves the container:
a routine's output can echo a token, an e-mail address or an account field, and a log in Drive is read by any
session."""

from __future__ import annotations

from ..record_scan.catalogue import ALLOWED_VALUES, record_patterns

REMOVED = "[removed: {kind}]"


def scrub(text: str) -> str:
    """The text with each found value replaced by `[removed: <kind>]` (the three F&O channel IDs stay)."""
    spans: list[tuple[int, int, str]] = []
    for pattern in record_patterns():
        for start, value in pattern.values_in(text):
            if value not in ALLOWED_VALUES:
                spans.append((start, start + len(value), pattern.name))
    kept, last = [], 0
    for start, end, kind in sorted(spans):
        if start < last:  # overlapping finds: the earlier one already covers it
            continue
        kept.append(text[last:start])
        kept.append(REMOVED.format(kind=kind))
        last = end
    kept.append(text[last:])
    return "".join(kept)
