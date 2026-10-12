"""Commands for the 3 pm quote recorder: `python -m fno quotes record` and `python -m fno quotes report`."""

from __future__ import annotations

import json


def add_quotes_parser(subparsers) -> None:
    quotes = subparsers.add_parser("quotes", help="record real 3 pm bid/ask quotes of NIFTY options (never orders)")
    actions = quotes.add_subparsers(dest="quotes_cmd", required=True)
    record = actions.add_parser("record", help="record today's snapshot in the 14:55-15:10 IST window")
    record.add_argument("--outside-window", action="store_true", help="testing only: one attempt now, never canonical")
    actions.add_parser("report", help="median and 90th-percentile half-spread by distance from the money")
    quotes.set_defaults(func=cmd_quotes)


def cmd_quotes(args) -> int:
    from ..composition import build_quote_recorder
    from ..config import load_app_config
    from ..storage.wiring import QUOTES_FOLDER
    from .report import canonical_snapshots, spread_report

    if args.quotes_cmd == "report":
        print(json.dumps(spread_report(canonical_snapshots(QUOTES_FOLDER)), indent=1))
        return 0
    result = build_quote_recorder(load_app_config(args.config)).record(outside_window=args.outside_window)
    print(f"{result.status}: {result.snapshot_id or '-'} ({result.rows} contracts, complete={result.complete})")
    return (
        0
        if result.status in ("recorded", "already recorded", "not a trading day")
        and (result.complete or result.status != "recorded" or args.outside_window)
        else 1
    )
