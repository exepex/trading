"""R2's one Groww bid/ask snapshot (PROTOCOL.md section 6.2, AMENDMENT_1.md D8): read-only quotes, never an order.

    python snapshot.py [--cache DIR]

Runs only between 14:00 and 15:00 IST on a session. The raw answers go to Drive's `raw` area (and the local cache,
outside the repository); the derived legs file stays in the cache for `study.py --snapshot`. Prints counts only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]

from r2study.bhav import option_legs, summarise  # noqa: E402
from r2study.inputs import InputCache  # noqa: E402
from r2study.sessions import Sessions  # noqa: E402
from r2study.snapshot_capture import candidates, capture, check_window, legs_file, raw_file  # noqa: E402
from r2study.wiring import UDIFF  # noqa: E402

from fno.config import load_config  # noqa: E402
from fno.constants import RESEARCH_USER_AGENT  # noqa: E402
from fno.models import now_ist  # noqa: E402
from fno.providers.groww import GrowwProvider, _payload  # noqa: E402
from fno.storage.raw_store import AreaStore  # noqa: E402
from fno.storage.wiring import RAW_AREA, build_drive_reader, build_owner_drive, build_session_calendar  # noqa: E402

EVENT_CALENDAR_API = "https://www.nseindia.com/api/event-calendar?index=equities"
QUOTE_GAP_SECONDS = 0.15  # stays under Groww's live-data rate limit
DRIVE_FOLDER = "groww/derivatives/stock-option-quotes"


class GrowwQuotes:
    """The capture's QuoteSource on Groww: expiries, chain symbols and single quotes, all read-only."""

    def __init__(self, provider: GrowwProvider):
        self.provider = provider

    def expiries(self, symbol: str) -> list[date]:
        return self.provider.expiries(symbol)

    def chain_symbols(self, symbol: str, expiry: date):
        chain = self.provider.chain(symbol, expiry)
        return chain.spot, {key: q.symbol for key, q in chain.quotes.items() if q.symbol}

    def quote(self, trading_symbol: str) -> dict:
        time.sleep(QUOTE_GAP_SECONDS)
        api = self.provider.api
        return _payload(
            api.get_quote(trading_symbol=trading_symbol, exchange=api.EXCHANGE_NSE, segment=api.SEGMENT_FNO)
        )


def event_calendar() -> tuple[list[dict], bytes]:
    session = requests.Session()
    session.headers.update({"User-Agent": RESEARCH_USER_AGENT, "Referer": "https://www.nseindia.com/"})
    response = session.get(EVENT_CALENDAR_API, timeout=60)
    response.raise_for_status()
    return json.loads(response.content), response.content


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", type=Path, default=HERE / ".cache")
    args = parser.parse_args(argv)
    start = now_ist()
    calendar = build_session_calendar()
    sessions = Sessions(calendar.sessions(start.date() - timedelta(days=30), start.date() + timedelta(days=120)))
    check_window(start, sessions)
    previous_day = sessions.before(start.date())
    found_file = InputCache(args.cache, build_drive_reader().get)
    found_file.fetch(UDIFF)
    name, data = found_file.read(UDIFF, previous_day)
    previous = summarise(previous_day, name, data)
    rows, calendar_bytes = event_calendar()
    found = candidates(rows, start.date(), sessions, previous)
    chains = option_legs(previous_day, name, data, {c.symbol for c in found})
    raw, legs = capture(GrowwQuotes(GrowwProvider(load_config())), found, sessions, previous, chains, now_ist)
    raw["event_calendar"] = calendar_bytes.decode("utf-8")
    raw_bytes, sha = raw_file(raw)
    stamp = start.strftime("%Y%m%d_%H%M%S")
    local = args.cache / "snapshot"
    local.mkdir(parents=True, exist_ok=True)
    (local / f"r2-snapshot_{stamp}.json").write_bytes(raw_bytes)
    (local / f"r2-legs_{stamp}.jsonl").write_bytes(legs_file(legs))
    owner = build_owner_drive()
    drive_path = f"{DRIVE_FOLDER}/{start:%Y/%m/%d}/r2-snapshot_{stamp}.json"
    if owner is not None:
        AreaStore(owner, RAW_AREA).put(drive_path, raw_bytes)
    two_sided = sum(1 for leg in legs if leg.bid and leg.ask)
    print(
        f"snapshot {raw['started']} to {raw['finished']}: {len(found)} stocks, {len(legs)} legs quoted "
        f"({two_sided} two-sided), {raw['not_quoted']} not quoted; raw sha256 {sha}; "
        f"Drive: {'raw/' + drive_path if owner else 'NOT saved (no owner sign-in)'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
