"""The figures of protocol section 12 for one variant's trades (one index, one run, one pad): what was taken and why
not, the P&L, the risk, the proxy share and return on margin. Plain data for `selection.json` and `final.json`."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

import numpy as np

from .margin import EntryMargin
from .stats import complete, drawdown, finite, mean_net, taken, worst_month
from .trade import Trade

MARGIN_LABEL = "calculator only, unchecked"  # protocol section 9, revision 3: no independent margin source


def _mean(values: Sequence[float]) -> float | None:
    return finite(float(np.mean(values))) if values else None


def margin_figures(trades: Sequence[Trade], margins: Sequence[EntryMargin]) -> dict:
    """Return on margin per taken trade (net over initial margin), where a margin figure exists."""
    pairs = [(t, m) for t, m in zip(taken(trades), margins, strict=True) if m.initial]
    returns = [t.net / m.initial for t, m in pairs]
    reasons = Counter(m.reason for m in margins if m.initial is None)
    median = finite(float(np.median(returns))) if returns else None
    return {"label": MARGIN_LABEL, "trades_with_margin": len(pairs),
            "mean_margin": _mean([m.initial for _, m in pairs]), "mean_return_on_margin": _mean(returns),
            "median_return_on_margin": median, "no_margin": dict(sorted(reasons.items()))}  # fmt: skip


def figures(trades: Sequence[Trade], margins: Sequence[EntryMargin] | None = None) -> dict:
    took, done = taken(trades), complete(trades)
    incomplete = [t for t in took if t.incomplete_exit]
    worst = worst_month(done)
    out = {
        "cycles": len(trades),
        "taken": len(took),
        "complete": len(done),
        "incomplete_exits": len(incomplete),
        "incomplete_mean_net": mean_net(incomplete),
        "proxy_share": finite(len(incomplete) / len(took)) if took else None,
        "not_taken": dict(sorted(Counter(t.status for t in trades if not t.taken).items())),
        "total_net": finite(sum(t.net for t in done)),
        "mean_net": finite(mean_net(done)),
        "all_mean_net": finite(mean_net(took)),
        "win_share": finite(sum(t.net > 0 for t in done) / len(done)) if done else None,
        "mean_gross": _mean([t.gross for t in done]),
        "mean_charges": _mean([t.charges for t in done]),
        "mean_pads": _mean([t.pads for t in done]),
        "max_drawdown": finite(drawdown(done)),
        "worst_month": list(worst) if worst else None,
        "worst_trade": finite(min((t.net for t in done), default=0.0)),
        "exits_by": dict(sorted(Counter(t.exit_how for t in took).items())),
        "width_by_year": widths_by_year(took),
        "lot_by_year": lots_by_year(took),
    }
    if margins is not None:
        out["margin"] = margin_figures(trades, margins)
    return out


def widths_by_year(trades: Sequence[Trade]) -> dict[str, dict[str, int]]:
    found: dict[str, Counter] = {}
    for t in trades:
        found.setdefault(str(t.cycle.entry_day.year), Counter())[str(t.width)] += 1
    return {y: dict(sorted(c.items())) for y, c in sorted(found.items())}


def lots_by_year(trades: Sequence[Trade]) -> dict[str, list[int]]:
    found: dict[str, set] = {}
    for t in trades:
        found.setdefault(str(t.cycle.entry_day.year), set()).add(t.lot)
    return {y: sorted(v) for y, v in sorted(found.items())}
