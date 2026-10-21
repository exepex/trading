"""The pack binding (story G10 part 2, section 4; judge 274): which records must name the released pack is fixed by
forecaster, never by a record's own `pack_sha256`. A pack-reading forecaster's record names exactly the released pack
(an empty or another SHA is refused before writing); every other forecaster commits before the pack exists, so its
record names none. Opt-in: every pack-reading writer calls `check_pack_binding`, with a test per writer (judge 274
add. 1)."""

from __future__ import annotations

from ..constants import BOOK2_HYBRID, BOOK3_AI

# The AI books read the pack; V4's and V5's forecasters join this list when they are built.
PACK_READERS = frozenset({BOOK2_HYBRID, BOOK3_AI})
NO_PACK = "{forecaster} {day}: no pack was released (system_late), so a pack reader has no record that day"
WRONG_PACK = "{forecaster} {day}: names pack {named!r}, the released pack is {released}"
NAMES_A_PACK = "{forecaster} {day}: commits before the pack exists, so it names no pack (got {named!r})"


class PackBindingRefused(ValueError):
    """A record whose pack SHA breaks the binding: nothing is written."""


def check_pack_binding(forecaster: str, day: str, named: str, released: str) -> None:
    """`named`: the record's `pack_sha256`; `released`: the release record's (empty on a system_late day)."""
    if forecaster not in PACK_READERS:
        if named:
            raise PackBindingRefused(NAMES_A_PACK.format(forecaster=forecaster, day=day, named=named))
        return
    if not released:
        raise PackBindingRefused(NO_PACK.format(forecaster=forecaster, day=day))
    if named != released:
        raise PackBindingRefused(WRONG_PACK.format(forecaster=forecaster, day=day, named=named, released=released))
