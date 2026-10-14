"""`python -m fno desk pack [--day YYYY-MM-DD]` (story E2): builds and writes the day's common market pack and Book 1's
private pack, printing each path and SHA-256 (commit them with the day's run). Books 2 and 3 get private packs when
their envelope (D4) and constitution (D5) exist. Research and paper only: nothing here places an order."""

from __future__ import annotations

from datetime import date

from ..constants import BOOK1_RULES

EXIT_REFUSED = 2
PACKED_BOOKS = (BOOK1_RULES,)  # books 2 and 3 wait for D4 and D5


def add_pack_command(actions) -> None:
    """`desk pack`, registered by the desk's one parser (`fno/desk/cli.py`)."""
    pack = actions.add_parser("pack", help="write the common market pack and Book 1's private pack for a day")
    pack.add_argument("--day", type=date.fromisoformat, help="the session day (default: today in IST)")
    pack.set_defaults(func=cmd_pack)


def cmd_pack(args) -> int:
    from ..composition import DESK_DECISION_TIME
    from ..config import ROOT
    from ..models import now_ist
    from .pack_items import PackError
    from .pack_store import PackStore
    from .pack_wiring import build_common_pack_builder, build_private_pack_builder

    day, store = args.day or now_ist().date(), PackStore(ROOT)
    try:
        common = build_common_pack_builder().build(day, DESK_DECISION_TIME)
        written = [(store.write_common(common), common.sha256)]
        for book in PACKED_BOOKS:
            private = build_private_pack_builder().build(book, day)
            written.append((store.write_private(private), private.sha256))
    except PackError as refused:
        print(f"refused: {refused}")
        return EXIT_REFUSED
    for path, sha256 in written:
        print(f"wrote {path.relative_to(ROOT)} sha256 {sha256}")
    print(f"refused items (after the cutoff or untimed): {len(common.body['refused'])}")
    return 0
