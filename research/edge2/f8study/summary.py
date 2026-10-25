"""F8's figures (protocol sections 7-8): the discovery spread report per side with the futility rule, and the
held-out filter test: mean net, one-sided p (one trade a week, plain SE), the random-side control (RC1) and Holm.
Rows: {"cycle", "side", "status", "gross", "charges", "pads", "net", "credit", "width"}."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence

from fno.scoreboard.uncertainty import holm

ALPHA, FUTILE_BELOW, GROSS_BAR, RC1_DRAWS, RC1_SEED = 0.05, -300.0, 260.0, 2000, 20261025


def taken(rows: Sequence[dict]) -> list[dict]:
    return [r for r in rows if r["status"] == "taken"]


def mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def figures(rows: Sequence[dict]) -> dict:
    done = taken(rows)
    nets = [r["net"] for r in done]
    m = mean(nets)
    se = math.sqrt(sum((x - m) ** 2 for x in nets) / (len(nets) - 1) / len(nets)) if len(nets) > 1 else None
    return {"cycles": len(rows), "taken": len(done),
            "skips": {k: sum(r["status"] == k for r in rows) for k in sorted({r["status"] for r in rows} - {"taken"})},
            "mean_gross": mean([r["gross"] for r in done]), "mean_charges": mean([r["charges"] for r in done]),
            "mean_pads": mean([r["pads"] for r in done]), "mean_net": m, "se": se,
            "p": 1.0 if m is None or not se else 0.5 * math.erfc(m / se / math.sqrt(2)),
            "win_share": sum(x > 0 for x in nets) / len(nets) if nets else None,
            "worst_trade": min(nets, default=None), "mean_width": mean([r["width"] for r in done if r["width"]]),
            "by_year": {y: mean([r["net"] for r in done if r["cycle"][:4] == y])
                        for y in sorted({r["cycle"][:4] for r in done})}}  # fmt: skip


def discovery_row(sides: Mapping[str, Sequence[dict]], pad2: Mapping[str, Sequence[dict]],
                  at_close: Mapping[str, Sequence[dict]]) -> dict:  # fmt: skip
    put, call = figures(sides["put"]), figures(sides["call"])
    average = None if put["mean_net"] is None or call["mean_net"] is None else (put["mean_net"] + call["mean_net"]) / 2
    return {"put": put, "call": call, "side_average_net": average,
            "side_average_net_pad2": mean([figures(pad2[s])["mean_net"] or 0.0 for s in ("put", "call")]),
            "side_average_net_at_close": mean([figures(at_close[s])["mean_net"] or 0.0 for s in ("put", "call")]),
            "futile": average is None or average < FUTILE_BELOW}  # fmt: skip


def random_side_p(both: Sequence[tuple[dict, dict]], calls: int, observed: float | None) -> float | None:
    """`both`: (put row, call row) for each cycle with a signal; random series keep `calls` call spreads."""
    if observed is None or not both:
        return None
    rng, hits, draws = random.Random(RC1_SEED), 0, 0
    for _ in range(RC1_DRAWS):
        picks = [1] * calls + [0] * (len(both) - calls)
        rng.shuffle(picks)
        m = mean([r["net"] for r in taken([pair[pick] for pair, pick in zip(both, picks, strict=True)])])
        if m is None:
            continue
        draws += 1
        hits += m >= observed
    return hits / draws if draws else None


def held_out_row(filtered: Sequence[dict], pad2: Sequence[dict], both: Sequence[tuple[dict, dict]]) -> dict:
    found = figures(filtered)
    calls = sum(r["side"] == "call" for r in filtered)
    found.update({"calls": calls, "mean_net_pad2": figures(pad2)["mean_net"],
                  "p_side": random_side_p(both, calls, found["mean_net"])})  # fmt: skip
    return found


def verdicts(rows: Mapping[str, dict]) -> list[str]:
    """Protocol section 8: Holm on p and on p_side across the variants read, Rs 2 pad positive, gross above the bar."""
    names = sorted(rows)
    on_p = holm([rows[n]["p"] for n in names], ALPHA)
    on_side = holm([1.0 if rows[n]["p_side"] is None else rows[n]["p_side"] for n in names], ALPHA)
    costs_paid = {n: (rows[n]["mean_net_pad2"] or 0) > 0 and (rows[n]["mean_gross"] or 0) > GROSS_BAR for n in names}
    return [n for n, a, b in zip(names, on_p, on_side, strict=True) if a and b and costs_paid[n]]
