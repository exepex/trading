"""The legacy F&O bhavcopy (2019 to 5 Jul 2024), in `extract.py`'s row format.

The legacy file has no spot column. Spot is the close of the underlying's near-month future (FUTSTK / FUTIDX): the
nearest expiry strictly after the day, so the contract is still listed the next session. The day's outcome compares
that same contract's next close (`next_spot`, filled by `panel.link_next`), so a monthly roll never shows as a move.
`futures` keeps every listed future's close (`expiry=close|...`) for that link. The market lot is not in the file and
stays 0 (the outcome screen reads strikes only)."""

import csv
import io
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .sizing_tools import extract

OPTIONS = {"OPTSTK": "stock", "OPTIDX": "index"}
FUTURES = {"FUTSTK", "FUTIDX"}
RUPEES_A_LAKH = 100_000


def iso(text: str) -> str:
    return datetime.strptime(text, "%d-%b-%Y").date().isoformat()


def bhavcopy_rows(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as archive:
        return list(csv.DictReader(io.TextIOWrapper(archive.open(archive.namelist()[0]), encoding="utf-8")))


def future_closes(rows: list[dict]) -> dict[str, dict[str, float]]:
    """Underlying -> expiry -> the future's close (traded or not: NSE's close of the day)."""
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        if r["INSTRUMENT"] in FUTURES and float(r["CLOSE"] or 0) > 0:
            out[r["SYMBOL"]][iso(r["EXPIRY_DT"])] = float(r["CLOSE"])
    return out


def near_month(closes: dict[str, float], day: str) -> tuple[str, float] | None:
    later = sorted(e for e in closes if e > day)
    return (later[0], closes[later[0]]) if later else None


def day_rows(day: str, rows: list[dict]) -> list[dict]:
    futures = future_closes(rows)
    chains = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    listed, kinds, turnover = defaultdict(lambda: defaultdict(set)), {}, defaultdict(float)
    for r in rows:
        if r["INSTRUMENT"] not in OPTIONS:
            continue
        u, expiry, strike = r["SYMBOL"], iso(r["EXPIRY_DT"]), float(r["STRIKE_PR"])
        kinds[u] = OPTIONS[r["INSTRUMENT"]]
        turnover[u] += float(r["VAL_INLAKH"] or 0) * RUPEES_A_LAKH
        if r["INSTRUMENT"] == "OPTSTK":
            listed[u][expiry].add(strike)
        if float(r["CONTRACTS"] or 0) > 0 and float(r["CLOSE"] or 0) > 0:
            chains[u][expiry][strike][r["OPTION_TYP"]] = float(r["CLOSE"])
    out = []
    for u, kind in kinds.items():
        near = near_month(futures.get(u, {}), day)
        if near:
            move = extract.implied_move(day, near[1], chains[u])
            out.append({"day": day, "underlying": u, "kind": kind, "spot": near[1], "lot": 0,
                        "turnover": turnover[u], "implied": "" if move is None else repr(move),
                        "strikes": extract.strike_sets(listed[u]), "proxy_expiry": near[0],
                        "futures": "|".join(f"{e}={c!r}" for e, c in sorted(futures[u].items()))})  # fmt: skip
    return out
