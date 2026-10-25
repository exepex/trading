"""EDGE2 slippage note (descriptive, no trial, no strategy claim; orchestrator, 25 Oct 2026): what crossing half the
bid-ask spread costs at the recorded 15:00 captures, against C1's Rs 1 and Rs 2 pads.

Everything is read through existing, unchanged code: MS-P1b's verified `CaptureReader` (Groww captures, hash against
the sidecar), MS-SIM-b's `relative_half_spread` and `bucket_of` (story MS-SIM-b, read-only reuse), A20a's archived lot
file (`ArchivedLots`). NSE's public-chain captures (story O6) are parsed from their committed CSVs after their SHA-256
is checked against each sidecar. Writes `research/edge2/slippage/summary.json` (aggregates only).

    python research/edge2/slippage.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fno.school.contracts.roads import ROADS, ROADS_BY_CODE  # noqa: E402
from fno.school.simulator.constants import TICK  # noqa: E402
from fno.school.simulator.spreads.bucket import bucket_of  # noqa: E402
from fno.school.simulator.spreads.learner import relative_half_spread  # noqa: E402
from fno.school.simulator.spreads.recorded import Skipped, recorded_snapshots  # noqa: E402

FIRST_CAPTURE, LOT_FILE_FROM = date(2026, 10, 13), date(2026, 10, 21)
PADS = (1.0, 2.0)  # C1's decided and reported pads, rupees a unit a leg a side
NSE_FOLDER = ROOT / "research" / "data" / "quotes" / "nse" / "derivatives" / "quote-snapshots"
OUT = Path(__file__).parent / "slippage" / "summary.json"


def half_spread(quote) -> float | None:
    """Rupees a unit: half the bid-ask gap, floored at half a tick (MS-SIM-b's rule), for a valid two-sided quote."""
    relative = relative_half_spread(quote)
    return None if relative is None else max((quote.ask - quote.bid) / 2, TICK / 2)


def out_of_the_money(kind: str, strike: float, spot: float) -> bool:
    """A call at or above spot, a put at or below it (the legs the EDGE studies sell or buy as wings)."""
    return strike >= spot if kind.upper().endswith("CE") else strike <= spot


def lot_lookup():
    from fno.school.roads.lots import ArchivedLots
    from fno.school.roads.stored_files import StoredFilesOnly
    from fno.school.roads.wiring import build_archive_stores
    from fno.storage.raw_library import RawFileLibrary

    lots, cache = ArchivedLots(RawFileLibrary(build_archive_stores(), StoredFilesOnly())), {}

    def lot(underlying: str, session: date, expiry: date) -> int | None:
        """The session's own lot file; before the first copy (21 Oct), the first copy's lot for that expiry."""
        day = max(session, LOT_FILE_FROM)
        key = (underlying, day, expiry)
        if key not in cache:
            found = lots.lot(underlying, day, (expiry,))
            cache[key] = getattr(found, "units", None)
        return cache[key]

    return lot


def summarise(values: list[float]) -> dict | None:
    if not values:
        return None
    ordered = sorted(values)
    return {"n": len(values), "median": statistics.median(values), "p75": ordered[int(0.75 * (len(values) - 1))],
            "p95": ordered[int(0.95 * (len(values) - 1))]}  # fmt: skip


def groww_rows(sessions: list[date], lot) -> tuple[list[dict], list[str]]:
    from fno.school.roads.wiring import QUOTES_FOLDER
    from fno.school.simulator.practice.wiring import build_capture_reader

    skipped, rows = Skipped(), []
    for snap in recorded_snapshots(build_capture_reader(QUOTES_FOLDER), ROADS, sessions, skipped):
        underlying = ROADS_BY_CODE[snap.road].underlying
        for key, quote in snap.quotes.items():
            bucket = bucket_of(underlying, snap.spot, key.strike, snap.session, key.expiry)
            half = half_spread(quote)
            units = lot(underlying, snap.session, key.expiry)
            rows.append({"road": str(snap.road), "session": snap.session.isoformat(), "strike": key.strike,
                         "kind": str(key.kind), "expiry": key.expiry.isoformat(),
                         "bucket": None if bucket is None else f"{bucket.moneyness} | {bucket.dte} | "
                                   f"{'otm' if out_of_the_money(str(key.kind), key.strike, snap.spot) else 'itm'}",
                         "half": half, "lot": units, "touch_qty": None if half is None else
                         min(quote.bid_qty or 0, quote.ask_qty or 0)})  # fmt: skip
    return rows, skipped.lines()


def nse_rows() -> tuple[list[dict], list[str]]:
    """NIFTY's NSE captures, each CSV checked against its sidecar's SHA-256 before it is read."""
    rows, refused = [], []
    for path in sorted(NSE_FOLDER.glob("*/*/nifty_*_*.csv")):
        meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
        if hashlib.sha256(path.read_bytes()).hexdigest() != meta.get("csv_sha256"):
            refused.append(path.name)
            continue
        with path.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                bid, ask = float(r["bid"] or 0), float(r["ask"] or 0)
                ok = r["valid"].lower() == "true" and bid > 0 and ask >= bid
                half = max((ask - bid) / 2, TICK / 2) if ok else None
                rows.append({"session": path.stem.split("_")[1], "strike": float(r["strike"]), "kind": r["type"],
                             "expiry": r["expiry"], "half": half})  # fmt: skip
    return rows, refused


def per_bucket(rows: list[dict]) -> dict:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        if r["bucket"] is not None:
            groups[(r["road"], r["bucket"])].append(r)
    out = {}
    for (road, bucket), found in sorted(groups.items()):
        quoted = [r for r in found if r["half"] is not None]
        per_lot = [r["half"] * r["lot"] for r in quoted if r["lot"]]
        out[f"{road} | {bucket}"] = {
            "quotes": len(found), "missing_two_sided_share": 1 - len(quoted) / len(found),
            "half_spread_rs_per_unit": summarise([r["half"] for r in quoted]),
            "half_spread_rs_per_lot": summarise(per_lot),
            "share_above_pad": {f"rs_{p:g}": (sum(r["half"] > p for r in quoted) / len(quoted) if quoted else None)
                                for p in PADS},
            "touch_qty_in_lots": summarise([r["touch_qty"] / r["lot"] for r in quoted if r["lot"] and r["touch_qty"]]),
        }  # fmt: skip
    return out


def source_check(groww: list[dict], nse: list[dict]) -> dict:
    """NIFTY monthly strikes quoted two-sided by both sources on the same session: NSE's half-spread minus Groww's."""
    key = lambda r: (r["session"].replace("-", ""), r["strike"], r["kind"], r["expiry"])  # noqa: E731
    mine = {key(r): r["half"] for r in groww if r["road"].startswith("NIFTY-M") and r["half"] is not None}
    pairs = [(mine[key(r)], r["half"]) for r in nse if r["half"] is not None and key(r) in mine]
    return {"pairs": len(pairs), "groww_median": statistics.median(a for a, _ in pairs) if pairs else None,
            "nse_median": statistics.median(b for _, b in pairs) if pairs else None,
            "nse_minus_groww": summarise([b - a for a, b in pairs])}  # fmt: skip


def main() -> int:
    from fno.storage.wiring import build_session_calendar

    cal = build_session_calendar()
    sessions = [d for d in cal.sessions(FIRST_CAPTURE, date.today()) if d < date.today()]
    groww, skipped = groww_rows(sessions, lot_lookup())
    nse, refused = nse_rows()
    result = {"descriptive": True, "sessions": [d.isoformat() for d in sessions], "skipped_captures": skipped,
              "nse_refused": refused, "groww_quotes": len(groww), "nse_quotes": len(nse),
              "buckets": per_bucket(groww), "nifty_monthly_source_check": source_check(groww, nse)}  # fmt: skip
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(groww)} Groww quotes, {len(nse)} NSE quotes, {len(skipped)} skip lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
