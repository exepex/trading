"""Narrows the full F&O universe to the few underlyings worth a deeper (option-chain) look each scan."""

from __future__ import annotations

from dataclasses import dataclass

from .models import UnderlyingSnapshot


@dataclass(frozen=True)
class ShortlistRules:
    size: int = 12  # deep looks per scan (each costs an option-chain request)
    min_move_pct: float = 0.6  # ignore underlyings moving less than this today
    min_traded_value: float = 50e7  # rupees of F&O turnover today (50 crore) for liquid options

    @classmethod
    def from_config(cls, cfg: dict) -> ShortlistRules:
        return cls(**{k: v for k, v in (cfg or {}).items() if k in cls.__dataclass_fields__})


def activity_score(snap: UnderlyingSnapshot) -> float:
    """Big price move plus big open-interest change: where positions are being built today."""
    move = abs(snap.day_change_pct or 0.0)
    oi = abs(snap.oi_change_pct or 0.0)
    return move + 0.25 * oi


def build_shortlist(
    snapshots: dict[str, UnderlyingSnapshot],
    rules: ShortlistRules,
    excluded: set[str] = frozenset(),
    always_include: tuple[str, ...] = (),
) -> list[str]:
    """Most active liquid underlyings, plus any always-included (e.g. NIFTY) that are not excluded."""
    eligible = [
        s
        for s in snapshots.values()
        if s.symbol not in excluded
        and s.symbol not in always_include
        and abs(s.day_change_pct or 0.0) >= rules.min_move_pct
        and s.traded_value >= rules.min_traded_value
    ]
    ranked = sorted(eligible, key=activity_score, reverse=True)
    pinned = [sym for sym in always_include if sym in snapshots and sym not in excluded]
    return pinned + [s.symbol for s in ranked[: max(rules.size - len(pinned), 0)]]
