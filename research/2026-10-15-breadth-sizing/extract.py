"""Step 1 of the BR1 sizing: one row per (session, underlying) from NSE's UDiFF F&O bhavcopies.

Columns: day, underlying, kind (index or stock), spot (`UndrlygPric`), implied (the ATM straddle's daily move, below),
lot (`NewBrdLotQty`), turnover (the day's option traded value, rupees), strikes (a stock's listed strikes on its two
nearest expiries, `expiry=k;k|expiry=k;k`: NSE replaces them all on a split, bonus or demerger, `sizing.py`).

Implied daily move: on the nearest expiry with at least 3 weekdays left, the strike nearest spot (within 2%) whose CE
and PE both traded; `(CE + PE) / (spot x sqrt(2 / pi) x sqrt(n))`, n = weekdays to expiry (holidays ignored: sizing
only, scoring uses the NSE calendar).

    python -I extract.py <folder of YYYY-MM-DD.zip> <out.csv>
"""

import csv
import io
import math
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

MIN_WEEKDAYS_LEFT = 3
MAX_STRIKE_GAP = 0.02
OPTION_TYPES = {"STO": "stock", "IDO": "index"}
COLUMNS = ("day", "underlying", "kind", "spot", "implied", "lot", "turnover", "strikes")
STRIKE_EXPIRIES = 2


def bhavcopy_rows(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as archive:
        return list(csv.DictReader(io.TextIOWrapper(archive.open(archive.namelist()[0]), encoding="utf-8")))


def implied_move(day: str, spot: float, chain: dict) -> float | None:
    """`chain`: expiry -> strike -> {CE: close, PE: close}, traded contracts only."""
    for expiry in sorted(chain):
        weekdays = int(np.busday_count(day, expiry))
        if weekdays < MIN_WEEKDAYS_LEFT:
            continue
        strikes = [k for k, legs in chain[expiry].items() if "CE" in legs and "PE" in legs]
        if not strikes:
            return None
        strike = min(strikes, key=lambda k: abs(k - spot))
        if abs(strike - spot) / spot > MAX_STRIKE_GAP:
            return None
        straddle = chain[expiry][strike]["CE"] + chain[expiry][strike]["PE"]
        return straddle / (spot * math.sqrt(2 / math.pi) * math.sqrt(weekdays))
    return None


def strike_sets(listed: dict) -> str:
    """`expiry -> set of strikes` of the nearest expiries, as `expiry=k;k|expiry=k;k`."""
    nearest = sorted(listed)[:STRIKE_EXPIRIES]
    return "|".join(f"{e}=" + ";".join(repr(k) for k in sorted(listed[e])) for e in nearest)


def day_rows(day: str, rows: list[dict]) -> list[dict]:
    info, chains = {}, defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    listed = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r["FinInstrmTp"] not in OPTION_TYPES:
            continue
        u = r["TckrSymb"]
        seen = info.setdefault(u, {"kind": OPTION_TYPES[r["FinInstrmTp"]], "spot": 0.0, "lot": 0, "turnover": 0.0})
        seen["spot"] = seen["spot"] or float(r["UndrlygPric"] or 0)
        seen["lot"] = seen["lot"] or int(float(r["NewBrdLotQty"] or 0))
        seen["turnover"] += float(r["TtlTrfVal"] or 0)
        if r["FinInstrmTp"] == "STO":
            listed[u][r["XpryDt"]].add(float(r["StrkPric"]))
        if float(r["TtlTradgVol"] or 0) > 0 and float(r["ClsPric"] or 0) > 0:
            chains[u][r["XpryDt"]][float(r["StrkPric"])][r["OptnTp"]] = float(r["ClsPric"])
    out = []
    for u, seen in info.items():
        if seen["spot"] > 0:
            move = implied_move(day, seen["spot"], chains[u])
            out.append({"day": day, "underlying": u, **seen, "implied": "" if move is None else repr(move),
                        "strikes": strike_sets(listed[u])})  # fmt: skip
    return out


def main(folder: Path, out: Path) -> None:
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, COLUMNS)
        writer.writeheader()
        for path in sorted(folder.glob("*.zip")):
            writer.writerows(day_rows(path.stem, bhavcopy_rows(path)))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
