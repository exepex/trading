"""F9's figures (protocol sections 5 and 7): per variant, the mean net of the decided trades (taken, every exit leg
traded) with a standard error clustered by event, the one-sided p, Holm across the four, the ordinary-day control
(RC1: random control days, the same number as the events traded) and the nomination; and the gamma report (each
event's gap and move, the worst events, by type). Rows are `trades.trade_row` dicts."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence

from fno.scoreboard.uncertainty import holm

ALPHA, MIN_EVENTS, GROSS_BAR, P_EVENT_MAX, NOMINATED_AT_MOST = 0.05, 30, 820.0, 0.10, 2
RC1_DRAWS, RC1_SEED = 2000, 20261025


def decided(rows: Sequence[dict]) -> list[dict]:
    return [r for r in rows if r["status"] == "taken" and not r.get("incomplete")]


def mean(values) -> float | None:
    values = list(values)
    return sum(values) / len(values) if values else None


def clustered(rows: Sequence[dict]) -> tuple[float | None, float | None, int]:
    if not rows:
        return None, None, 0
    m = mean(r["net"] for r in rows)
    sums: dict[str, float] = {}
    for r in rows:
        sums[r["event"]] = sums.get(r["event"], 0.0) + r["net"] - m
    g = len(sums)
    se = math.sqrt(sum(s * s for s in sums.values()) * g / (g - 1)) / len(rows) if g > 1 else None
    return m, se, g


def p_value(m, se, clusters) -> float:
    return 1.0 if m is None or not se or clusters < MIN_EVENTS else 0.5 * math.erfc(m / se / math.sqrt(2))


def event_control_p(control: Sequence[dict], events: int, observed: float | None) -> float | None:
    """Share of random sets of `events` control days whose decided trades' mean net is >= the observed mean."""
    days = sorted({r["event"] for r in control})
    if observed is None or not events or len(days) < events:
        return None
    by_day: dict[str, list[dict]] = {}
    for r in decided(control):
        by_day.setdefault(r["event"], []).append(r)
    rng, hits, draws = random.Random(RC1_SEED), 0, 0
    for _ in range(RC1_DRAWS):
        m = mean(r["net"] for d in rng.sample(days, events) for r in by_day.get(d, ()))
        if m is None:
            continue
        draws += 1
        hits += m >= observed
    return hits / draws if draws else None


def describe(rows: Sequence[dict], pad2: Sequence[dict], control: Sequence[dict]) -> dict:
    done = decided(rows)
    m, se, events = clustered(done)
    nets = [r["net"] for r in done]
    worst = min(done, key=lambda r: r["net"], default=None)
    return {
        "trades": len(rows), "decided": len(done), "events": events,
        "skips": {k: sum(r["status"] == k for r in rows) for k in sorted({r["status"] for r in rows} - {"taken"})},
        "incomplete_exits": sum(r["status"] == "taken" and bool(r.get("incomplete")) for r in rows),
        "mean_gross": mean(r["gross"] for r in done), "mean_charges": mean(r["charges"] for r in done),
        "mean_pads": mean(r["pads"] for r in done), "mean_net": m, "se": se, "p": p_value(m, se, events),
        "mean_net_pad2": mean(r["net"] for r in decided(pad2)),
        "control_mean_net": mean(r["net"] for r in decided(control)),
        "p_event": event_control_p(control, events, m),
        "win_share": sum(x > 0 for x in nets) / len(nets) if nets else None,
        "worst": None if worst is None else {k: worst[k] for k in ("index", "event", "kind", "net", "move_pct")},
        "by_type": {k: {"trades": sum(r["kind"] == k for r in done), "mean_net": mean(r["net"] for r in done
                    if r["kind"] == k)} for k in sorted({r["kind"] for r in done})},
        "by_index": {k: mean(r["net"] for r in done if r["index"] == k) for k in sorted({r["index"] for r in done})},
    }  # fmt: skip


def family(runs: Mapping[str, Mapping[str, list[dict]]]) -> dict[str, dict]:
    rows = {n: describe(r["pad1"], r["pad2"], r["control"]) for n, r in runs.items()}
    names = sorted(rows)
    for name, passed in zip(names, holm([rows[n]["p"] for n in names], ALPHA), strict=True):
        rows[name]["holm"] = passed
    return rows


def eligible(r: dict) -> bool:
    return (r["holm"] and r["p_event"] is not None and r["p_event"] <= P_EVENT_MAX
            and (r["mean_net_pad2"] or 0) > 0 and (r["mean_gross"] or 0) > GROSS_BAR)  # fmt: skip


def nominated(rows: Mapping[str, dict]) -> list[str]:
    return sorted((n for n, r in rows.items() if eligible(r)), key=lambda n: (rows[n]["p"], n))[:NOMINATED_AT_MOST]


def gamma_report(rows: Sequence[dict]) -> list[dict]:
    """One line per event and index: type, overnight gap and move (per cent), and the net of this variant."""
    return [{k: r.get(k) for k in ("event", "index", "kind", "gap_pct", "move_pct", "status", "net")}
            for r in sorted(rows, key=lambda r: (r["event"], r["index"]))]  # fmt: skip
