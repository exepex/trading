"""The two runs (protocol sections 10-11) on plain `Market` objects, so the tests run them on synthetic data.

Run 1 measures every variant on 2019-22 (the panel sealed at RUN1_SEAL), applies G1 the way R1's CostWall computes it
(the 90% one-sided lower bound of mean gross, minus mean charges and pads, minus the tail not already in the gross),
and prints each G1 passer's expected run-2 count. Run 2 tests only run 1's passers, with Holm across both indices,
and applies the nomination rule."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from fno.factory.constants import BOUND_LEVEL
from fno.factory.cost_wall import Tail
from fno.factory.t_bound import lower_bound

from .margin import EntryMargin
from .report import figures
from .runner import (
    PADS,
    RUN1_FROM,
    RUN1_SEAL,
    RUN1_TO,
    RUN2_FROM,
    Market,
    cycles_of,
    run_variant,
    sealed,
    variant_name,
    variants,
)
from .stats import MIN_RUN1, MIN_TESTED, complete, g1_inputs, holm_family, mean_net, nominated, one_sided_p, taken
from .structures import TRADEABLE
from .stt_history import charges_on

RUN1_YEARS = 4.0
Margins = Callable[[str, Sequence], Sequence[EntryMargin] | None]  # (index, trades) -> margins, or None


def g1(trades) -> dict:
    found = g1_inputs(trades, RUN1_YEARS)
    if found is None or found.n < MIN_RUN1:
        return {"passed": False, "reason": "too few run-1 trades", "inputs": found.__dict__ if found else None}
    tail = Tail(found.tail_share, found.tail_mean_loss, True, None, None).extra_loss()
    bound = lower_bound(found.mean_gross, found.sd_gross, found.n, BOUND_LEVEL)
    net = bound - found.mean_cost - tail
    return {"passed": net > 0, "bound": bound, "cost": found.mean_cost, "tail": tail, "net_on_bound": net,
            "inputs": found.__dict__}  # fmt: skip


def stt_history(market: Market, cycles, code: str, rule: str, charges: dict) -> dict:
    """Section 9's side run: pad 1 with each order's own trade-date STT; reported, never decided on."""
    return figures(run_variant(market, cycles, code, rule, charges, PADS[0], charges_on(charges)))


def run1(markets: Mapping[str, Market], calendar, charges: dict, margins: Margins, run2_cycles: Mapping[str, int]):
    out = {}
    for index, market in markets.items():
        sealed_market = Market(index, sealed(market.panel, RUN1_SEAL), market.lots, market.settlement)
        cycles = cycles_of(sealed_market.panel, calendar, RUN1_FROM, RUN1_TO, RUN1_SEAL)
        for code, rule in variants():
            by_pad = {pad: run_variant(sealed_market, cycles, code, rule, charges, pad) for pad in PADS}
            base = by_pad[PADS[0]]
            entry = {"index": index, "structure": code, "exit": rule, "tradeable": code in TRADEABLE,
                     "pad1": figures(base, margins(index, base)), "pad2": figures(by_pad[PADS[1]]),
                     "pad1_stt_history": stt_history(sealed_market, cycles, code, rule, charges)}  # fmt: skip
            if code in TRADEABLE:
                entry["g1"] = g1(base)
                share = len(taken(base)) / len(base) if base else 0.0
                entry["expected_run2_trades"] = round(share * run2_cycles.get(index, 0), 1)
                entry["expected_untestable"] = entry["expected_run2_trades"] < MIN_TESTED
            out[variant_name(index, code, rule)] = entry
    return out


def run2(markets: Mapping[str, Market], calendar, charges: dict, margins: Margins, selection: Mapping[str, dict],
         last_days: Mapping[str, object]):  # fmt: skip
    tested, rows, k = {}, {}, 0
    for name, chosen in sorted(selection.items()):
        if chosen["tradeable"] and not chosen.get("g1", {}).get("passed"):
            continue  # section 11: run 2 measures only run 1's G1 passers (and the naked measurements)
        market = markets[chosen["index"]]
        cycles = cycles_of(market.panel, calendar, RUN2_FROM, last_days[chosen["index"]], last_days[chosen["index"]])
        by_pad = {pad: run_variant(market, cycles, chosen["structure"], chosen["exit"], charges, pad) for pad in PADS}
        base, wide = by_pad[PADS[0]], by_pad[PADS[1]]
        row = {"index": chosen["index"], "structure": chosen["structure"], "exit": chosen["exit"],
               "tradeable": chosen["tradeable"], "pad1": figures(base, margins(chosen["index"], base)),
               "pad2": figures(wide), "pad1_stt_history": stt_history(market, cycles, chosen["structure"],
                                                                         chosen["exit"], charges)}  # fmt: skip
        if chosen["tradeable"]:
            nets = [t.net for t in complete(base)]
            row |= {"p": one_sided_p(nets, k), "k": k, "n": len(nets), "mean_net": mean_net(complete(base)),
                    "mean_net_pad2": mean_net(complete(wide)) or 0.0, "all_mean_net": mean_net(taken(base)) or 0.0,
                    "all_mean_net_pad2": mean_net(taken(wide)) or 0.0,
                    "run1_mean_net": chosen["pad1"]["mean_net"] or 0.0}  # fmt: skip
            tested[name] = row["p"]
            k += 1
        rows[name] = row
    for name, significant in holm_family(tested).items():
        rows[name]["holm"] = significant
    candidates = {n: r for n, r in rows.items() if n in tested}
    return {"variants": rows, "tested": sorted(tested), "nominated": nominated(candidates)}
