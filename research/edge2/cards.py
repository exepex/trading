"""F1's six idea cards (protocol section 10), written from the protocol's own rules so none is typed by hand. G0 and G2
fields only: G1's gross, tail and cost and G3's sample plan come from the discovery run.

    python research/edge2/cards.py --first 109   # writes research/ideas/EDGE2-F1-<structure>-<gate>.md
"""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IDEAS = ROOT / "research" / "ideas"
EXPERIMENT, QUESTION = "edge2-f1-weekly-vrp-gate-2026-10-25", "edge2-f1-weekly-vrp-gate"
QUESTION_TEXT = (
    "EDGE2 F1: has a defined-risk weekly index option position held to expiry, always or only when ATM implied "
    "volatility is rich against an EWMA forecast of realised, made money after real costs? One Holm family of 6 "
    "(WF, WC x G0, G12, G15); discovery NIFTY+BANKNIFTY (spent, exploratory), held-out FINNIFTY+MIDCPNIFTY read once; "
    "protocol research/edge2/F1_PROTOCOL.md"
)
STRUCTURES = {"WF": "weekly short iron fly: sell the ATM call and put, buy wings one width either side",
              "WC": "weekly short iron condor: sell the call and put one implied move out, buy wings one width "
                    "further"}  # fmt: skip
GATES = {"G0": "always (no gate)", "G12": "only when sigma_IV / sigma_RV >= 1.2", "G15": "only when sigma_IV / "
         "sigma_RV >= 1.5"}  # fmt: skip
DATA_SETS = [
    "NIFTY weekly options | NSE daily closes | Feb 2019 - 9 Oct 2026",
    "BANKNIFTY weekly options | NSE daily closes | 2019 - 13 Nov 2024",
    "FINNIFTY weekly options | NSE daily closes | first weekly - Nov 2024",
    "MIDCPNIFTY weekly options | NSE daily closes | first weekly - Nov 2024",
]
WHO_PAYS = (
    "hedgers and retail buyers of short-dated index options paying a variance risk premium [strong evidence the "
    "premium exists in index options; reasoning only that it survives costs on Indian weeklies]"
)
ENTRY = (
    "the close of the first session after the previous expiry, every leg traded, {gate}; the widest width whose "
    "worst loss fits the cap for the cycle's lot"
)
CARD = """# Idea card: {id}

Written by `research/edge2/cards.py` from `research/edge2/F1_PROTOCOL.md`. Exploratory: discovery on spent data,
held-out read once (protocol section 2).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | {id} v1 |
| Ledger trial | {trial} |
| Registered research question | {question}: {question_text} |
| Proposed by (role or AI) and date | volatility trader and options strategist (Claude, EDGE2 builder), 25 Oct 2026 |
| Who pays and why | {who_pays} |
| Forecast it rests on | none (the gate is an EWMA lambda 0.94 of index close returns, protocol section 5) |
| Instrument and structure | each index's nearest weekly expiry; {structure}; never a naked short leg |
| Entry rule | {entry} |
| Exit rule | held to expiry, cash-settled at the expiry day's index close |
| Size | 1 lot of the contract's market lot on the entry day |
| Worst loss in Rs | at most Rs 10,000 modelled at entry (the cap), plus charges and pads |
| Expected gross per trade, with source | discovery run, added before G1 |
| Needs a reaction faster than 60 minutes? | no: entry at a daily close, exit at settlement |
| Frequency | about 50 cycles a year an index while weeklies existed; fewer when gated or skipped |

```factory
id: {id}
version: 1
trial: {trial}
experiment: {experiment}
description: "EDGE2 F1 {code} {gate_code}: {short}, {gate} (exploratory)"
question: {question}
hypothesis: yes
measurement: no
data_sets: [{data_sets}]
measures: "mean net per trade after C1's charges and the Rs 1 pad, one lot, held to settlement (protocol sections 7-9)"
```
"""


def card_id(code: str, gate: str) -> str:
    return f"EDGE2-F1-{code}-{gate}"


def in_trial_order() -> list[tuple[str, str]]:
    return [(code, gate) for code in STRUCTURES for gate in GATES]


def card_text(code: str, gate: str, trial: int) -> str:
    return CARD.format(id=card_id(code, gate), trial=trial, question=QUESTION, question_text=QUESTION_TEXT,
                       structure=STRUCTURES[code], gate=GATES[gate], who_pays=WHO_PAYS,
                       entry=ENTRY.format(gate=GATES[gate]), experiment=EXPERIMENT, code=code,
                       gate_code=gate, short=STRUCTURES[code].split(":")[0],
                       data_sets=", ".join(f'"{d}"' for d in DATA_SETS))  # fmt: skip


def write_cards(first: int, folder: Path = IDEAS) -> list[Path]:
    written = []
    for trial, (code, gate) in enumerate(in_trial_order(), start=first):
        path = folder / f"{card_id(code, gate)}.md"
        path.write_text(card_text(code, gate, trial), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=int, required=True, help="the next free ledger trial number")
    for path in write_cards(parser.parse_args().first):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
