"""`python -m fno news list` and `news quiet-spells` (story A19, scopes 8 and 10): readers of the captured parts
through receipts and the verified Drive cache. `list` prints headlines to the terminal of whoever runs it; no
workflow runs it."""

from __future__ import annotations

from datetime import datetime

from ..models import IST

ITEM = "{seen} | {publisher} | {title} | {url}"
SPELL = "{feed}: {kind}: longest quiet spell {hours:.1f} h"


def add_read_parsers(actions) -> None:
    listing = actions.add_parser("list", help="items first seen at or before a time (point in time)")
    listing.add_argument("--until", required=True, help="IST time, e.g. 2026-10-19T14:30")
    listing.add_argument("--since", help="IST time: only items first seen after it")
    listing.set_defaults(func=cmd_list)
    actions.add_parser("quiet-spells", help="each feed's longest gap between new items, by day type").set_defaults(
        func=cmd_quiet_spells
    )


def cmd_list(args, out=print, lines=None) -> int:
    from .reader import known_by

    until, since = _ist(args.until), _ist(args.since) if args.since else None
    for line in known_by(lines if lines is not None else _all_lines(), until, since):
        seen = datetime.fromisoformat(line["first_seen_at"]).astimezone(IST)
        out(ITEM.format(seen=f"{seen:%Y-%m-%d %H:%M}", publisher=line["publisher"], title=line["title"],
                        url=line["url"]))  # fmt: skip
    return 0


def cmd_quiet_spells(args, out=print, lines=None, rule=None) -> int:
    from .reader import quiet_spells
    from .wiring import build_stale_rule

    spells = quiet_spells(lines if lines is not None else _all_lines(), rule or build_stale_rule())
    for feed in sorted(spells):
        for kind, gap in sorted(spells[feed].items()):
            out(SPELL.format(feed=feed, kind=kind, hours=gap.total_seconds() / 3600))
    return 0


def _ist(text: str) -> datetime:
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo else moment.replace(tzinfo=IST)


def _all_lines() -> list[dict]:
    from .wiring import build_store

    store = build_store()
    return store.part_lines(store.part_receipts())
