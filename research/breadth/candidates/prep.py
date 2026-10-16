"""Response 198 (exploratory): study 3's daily inputs cached once, so the candidate runs never rebuild the panel.

    python -I research/breadth/candidates/prep.py <scratch>/panel.csv <scratch>/daily.json

Writes, for 2024-01-01 to 2025-12-31 (study 1's fallback window): each scored day, the three registered-baseline pairs'
daily mean Brier differences (v4's sign) and whether NIFTY moved 2% or more from that day to the next (the outcome day
of d_t, as v4's `judgeable` counts 2% days)."""

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "studies"), str(HERE.parents[2])]

from brstudy import runner, study2  # noqa: E402
from brstudy.daily import daily_losses, next_value, scored_pairs  # noqa: E402

WINDOW = ("2024-01-01", "2025-12-31")
BIG_MOVE = 0.02


def nifty_big_days(rows: dict) -> dict:
    """day -> True when |ln(NIFTY(t+1) / NIFTY(t))| >= 0.02."""
    days = sorted(rows)
    out = {}
    for t, nxt in zip(days, days[1:], strict=False):
        later = next_value(rows[t], rows[nxt])
        if later:
            out[t] = abs(math.log(later / float(rows[t]["spot"]))) >= BIG_MOVE
    return out


def main(panel_csv: str, out: str) -> None:
    first, last = WINDOW
    panel = runner.load(Path(panel_csv))
    table = {u: {d: r for d, r in rows.items() if first <= d <= last} for u, rows in panel.items()}
    losses = daily_losses(scored_pairs(table)[0])
    big = nifty_big_days(table["NIFTY"])
    days = [r["day"] for r in losses]
    members = {"/".join(p): list(study2.differences(losses, p)) for p in runner.PRIMARY_PAIRS}
    document = {"days": days, "members": members, "nifty_big": [bool(big.get(d, False)) for d in days],
                "nifty_missing": [d for d in days if d not in big]}  # fmt: skip
    Path(out).write_text(json.dumps(document) + "\n")
    print(f"{len(days)} days; {sum(document['nifty_big'])} NIFTY 2% days; {len(document['nifty_missing'])} missing")


if __name__ == "__main__":
    main(*sys.argv[1:])
