"""Which signals actually predict price? Hit rate and information coefficient per rule, from graded views."""

from __future__ import annotations

import math
from dataclasses import dataclass

COMBINED = "combined view"


@dataclass(frozen=True)
class RuleAccuracy:
    rule: str
    votes: int  # votes strong enough to count
    hit_rate: float  # share of votes whose sign matched the later move
    information_coefficient: float  # correlation between score and later return, -1..+1
    mean_edge_pct: float  # average later return in the direction voted


def correlation(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (sx * sy) if sx and sy else 0.0


def accuracy_for(name: str, pairs: list[tuple[float, float]], min_abs_score: float) -> RuleAccuracy:
    """pairs: (score, later return %)."""
    decided = [(s, r) for s, r in pairs if abs(s) >= min_abs_score and r != 0]
    hits = sum((s > 0) == (r > 0) for s, r in decided)
    return RuleAccuracy(
        rule=name,
        votes=len(decided),
        hit_rate=hits / len(decided) if decided else 0.0,
        information_coefficient=correlation([s for s, _ in pairs], [r for _, r in pairs]),
        mean_edge_pct=sum(math.copysign(r, s) for s, r in decided) / len(decided) if decided else 0.0,
    )


def rule_accuracy(outcomes: list[dict], horizon_minutes: int, min_abs_score: float = 0.2) -> list[RuleAccuracy]:
    """Per-rule accuracy over view outcomes at one horizon, best information coefficient first."""
    by_rule: dict[str, list[tuple[float, float]]] = {}
    combined: list[tuple[float, float]] = []
    for outcome in outcomes:
        if outcome["horizon_minutes"] != horizon_minutes:
            continue
        later = outcome["forward_return_pct"]
        combined.append((outcome["score"], later))
        for rule, score in outcome["votes"].items():
            by_rule.setdefault(rule, []).append((score, later))
    results = [accuracy_for(rule, pairs, min_abs_score) for rule, pairs in by_rule.items()]
    results.sort(key=lambda r: r.information_coefficient, reverse=True)
    return [accuracy_for(COMBINED, combined, min_abs_score), *results]


def suggested_weights(results: list[RuleAccuracy], min_votes: int = 50) -> dict[str, float]:
    """Weights proportional to positive information coefficient; rules with too few votes keep weight 1."""
    out = {}
    for r in results:
        if r.rule == COMBINED:
            continue
        out[r.rule] = 1.0 if r.votes < min_votes else round(max(r.information_coefficient, 0.0) * 10, 2)
    return out


def format_report(results: list[RuleAccuracy], horizon_minutes: int, min_votes: int = 50) -> str:
    lines = [f"Signal accuracy, price {horizon_minutes} minutes later", ""]
    lines.append(f"{'rule':22s} {'votes':>6s} {'hit rate':>9s} {'IC':>7s} {'edge %':>8s}  verdict")
    for r in results:
        if r.votes < min_votes:
            verdict = "too few votes yet"
        elif r.information_coefficient >= 0.05 and r.hit_rate > 0.52:
            verdict = "predictive"
        elif r.information_coefficient <= -0.03:
            verdict = "works backwards: review"
        else:
            verdict = "noise so far"
        lines.append(
            f"{r.rule:22s} {r.votes:6d} {r.hit_rate * 100:8.1f}% {r.information_coefficient:+7.3f} "
            f"{r.mean_edge_pct:+8.3f}  {verdict}"
        )
    return "\n".join(lines)
