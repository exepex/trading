"""R2's one Groww bid/ask snapshot (PROTOCOL.md section 6.2, AMENDMENT_1.md D8): read-only quotes, never an order.

    python snapshot.py --ready         check the inputs before 14:00 (no Groww call)
    python snapshot.py [--cache DIR]   take the snapshot (14:00-15:00 IST only)

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
from r2study.inputs import checked, manifest_rows  # noqa: E402
from r2study.sessions import Sessions  # noqa: E402
from r2study.snapshot_capture import COUNTS, candidates, capture, check_window, legs_file, raw_file  # noqa: E402
from r2study.wiring import CALENDAR_END, LATER_DAYS, UDIFF  # noqa: E402

from fno.config import load_config  # noqa: E402
from fno.constants import RESEARCH_USER_AGENT  # noqa: E402
from fno.models import now_ist  # noqa: E402
from fno.providers.groww import GrowwProvider, _payload  # noqa: E402
from fno.storage.raw_store import AreaStore  # noqa: E402
from fno.storage.wiring import RAW_AREA, build_drive_reader, build_owner_drive, build_session_calendar  # noqa: E402

EVENT_CALENDAR_API = "https://www.nseindia.com/api/event-calendar?index=equities"
QUOTE_GAP_SECONDS = 0.15  # stays under Groww's live-data rate limit
DRIVE_FOLDER = "groww/derivatives/stock-option-quotes"
MAX_NO_PREVIOUS_ROW_SHARE = 0.20  # amendment 2 item 10: above this the capture is not used


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
    """NSE's upcoming board meetings; refuses an answer that is not a list of rows with a symbol and a date."""
    session = requests.Session()
    session.headers.update({"User-Agent": RESEARCH_USER_AGENT, "Referer": "https://www.nseindia.com/"})
    response = session.get(EVENT_CALENDAR_API, timeout=60)
    response.raise_for_status()
    rows = json.loads(response.content)
    if (
        not isinstance(rows, list)
        or not rows
        or not all(isinstance(r, dict) and "symbol" in r and "date" in r for r in rows)
    ):
        raise ValueError("NSE's event calendar did not answer with rows of symbol and date")
    return rows, response.content


def previous_session_file(sessions: Sessions, today: date) -> tuple[date, str, bytes]:
    """The last session's current-format F&O file from Drive, checked against its manifest row."""
    day = sessions.before(today)
    rows = manifest_rows(UDIFF.name)
    if day not in rows:
        raise RuntimeError(f"{day}: the F&O file is not archived yet (no manifest row)")
    return day, UDIFF.filename_for(day), checked(build_drive_reader().get(UDIFF.path_for(day)), rows[day], str(day))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache", type=Path, default=HERE / ".cache")
    parser.add_argument("--ready", action="store_true", help="check the inputs only (no window, no Groww call)")
    args = parser.parse_args(argv)
    start = now_ist()
    calendar = build_session_calendar()
    ahead = min(start.date() + timedelta(days=LATER_DAYS), CALENDAR_END)
    sessions = Sessions(calendar.sessions(start.date() - timedelta(days=30), ahead))
    owner = build_owner_drive()
    if owner is None:
        raise RuntimeError("no owner Drive sign-in: the raw quotes could not be kept (amendment 2 item 11)")
    previous_day, name, data = previous_session_file(sessions, start.date())
    previous = summarise(previous_day, name, data)
    rows, calendar_bytes = event_calendar()
    found = candidates(rows, start.date(), sessions, previous)
    print(f"ready: previous session {previous_day}, {len(found)} F&O stocks with results in the next 10 sessions")
    if args.ready or not found:
        return 0 if found else 1
    check_window(now_ist(), sessions)
    chains = option_legs(previous_day, name, data, {c.symbol for c in found})
    raw, legs = capture(GrowwQuotes(GrowwProvider(load_config())), found, sessions, previous, chains, now_ist)
    raw["event_calendar"] = calendar_bytes.decode("utf-8")
    raw_bytes, sha = raw_file(raw)
    stamp = start.strftime("%Y%m%d_%H%M%S")
    local = args.cache / "snapshot"
    local.mkdir(parents=True, exist_ok=True)
    (local / f"r2-snapshot_{stamp}.json").write_bytes(raw_bytes)
    (local / f"r2-legs_{stamp}.jsonl").write_bytes(legs_file(legs))
    drive_path = f"{DRIVE_FOLDER}/{start:%Y/%m/%d}/r2-snapshot_{stamp}.json"
    AreaStore(owner, RAW_AREA).put(drive_path, raw_bytes)
    two_sided = sum(1 for leg in legs if leg.bid and leg.ask and leg.bid <= leg.ask)
    counts = ", ".join(f"{key} {raw[key]}" for key in COUNTS)
    print(
        f"snapshot {raw['started']} to {raw['finished']}: {len(found)} stocks, {len(legs)} legs quoted "
        f"({two_sided} two-sided); {counts}; raw sha256 {sha}; Drive: raw/{drive_path}"
    )
    if legs and raw["no_previous_row"] / len(legs) > MAX_NO_PREVIOUS_ROW_SHARE:
        print("STOP: too many legs without a previous-session row (expiry mismatch?): terciles would be unreliable")
        return 2
    return 0 if legs else 1


if __name__ == "__main__":
    raise SystemExit(main())
