"""Moving a repository file into its receipt-backed Drive series (O9b, section 2 step 1): the file's bytes become the
series' first file and the series, read back through the verified cache, must give the same bytes. Moving again is a
no-op when Drive already holds those bytes. A file that grew after its move (its writer still ran on the repository
copy until the merge) is caught up: a table gets the later rows as one new part, a report a new snapshot. A table in
Drive that is not a whole-line start of the file stops the move (the file and Drive disagree: a person decides,
nothing is overwritten)."""

from __future__ import annotations

import hashlib

from .receipted_rows import ReceiptedRowLog, ReceiptedSnapshots

MOVED = "{name}: moved to Drive and read back equal ({size} bytes, SHA-256 {sha})"
ALREADY = "{name}: already in Drive, equal ({size} bytes, SHA-256 {sha})"
CAUGHT_UP = "{name}: Drive held {drive} bytes; caught up and read back equal ({size} bytes, SHA-256 {sha})"
DIFFERS = "{name}: Drive already holds other bytes ({drive} bytes against the file's {size}); nothing written"
UNEQUAL = "{name}: read back unequal after the move ({drive} bytes against {size}); stop and look"


class MoveRefused(RuntimeError):
    """The file and its Drive series disagree: the move stops, nothing is overwritten."""


def move_into(series: ReceiptedRowLog | ReceiptedSnapshots, data: bytes, name: str) -> str:
    """One line saying what happened; MoveRefused when Drive holds, or gives back, other bytes."""
    facts = {"name": name, "size": len(data), "sha": hashlib.sha256(data).hexdigest()}
    current = series.current_bytes()
    if current == data:
        return ALREADY.format(**facts)
    part = series.catch_up(current, data)
    if part is None:
        raise MoveRefused(DIFFERS.format(drive=len(current), **facts))
    series.write_bytes(part)
    back = series.current_bytes()
    if back != data:
        raise MoveRefused(UNEQUAL.format(drive=len(back), **facts))
    return CAUGHT_UP.format(drive=len(current), **facts) if current else MOVED.format(**facts)
