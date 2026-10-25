"""F8's three idea cards (protocol section 9), written from the protocol's own rules. G0 and G2 fields only.

python research/edge2/f8_cards.py --first 121   # writes research/ideas/EDGE2-F8-<structure>.md
"""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IDEAS = ROOT / "research" / "ideas"
EXPERIMENT, QUESTION = "edge2-f8-fii-side-weekly-spread-2026-10-25", "edge2-f8-fii-side-weekly-spread"
QUESTION_TEXT = (
    "EDGE2 F8: does the sign of the FII net index-futures change, choosing a put or a call credit spread on NIFTY's "
    "weekly (entered at the next open, held to expiry), make money after real costs and more than random sides? One "
    "Holm family of 3 structures (P0W5, P5W5, P0W10); the filter tested only on held-out 2025-26 after a judge "
    "(post-hoc idea from F6); protocol research/edge2/F8_PROTOCOL.md"
)
STRUCTURES = {"P0W5": "short leg ATM, long leg 0.5% of the forward further out",
              "P5W5": "short leg 0.5% out of the money, long leg 0.5% beyond it",
              "P0W10": "short leg ATM, long leg 1.0% further out"}  # fmt: skip
WHO_PAYS = (
    "option buyers paying premium, with the side tilted by FII positioning [some evidence of F6's post-hoc lean; "
    "reasoning only that a spread can carry it]"
)
ENTRY = (
    "the open of the first session after the previous expiry, at each leg's opening trade; put spread after a rise "
    "in FII net index futures on the previous session, call spread after a fall"
)
DATA_SETS = [
    "NIFTY weekly options | NSE daily closes | Feb 2019 - 9 Oct 2026",
    "Participant open interest (A8) | NSE daily files | 2025 - 2026",
]
CARD = """# Idea card: {id}

Written by `research/edge2/f8_cards.py` from `research/edge2/F8_PROTOCOL.md`. Exploratory; the filter is tested only
on the held-out years 2025-26, after a judge (protocol sections 1 and 8).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | {id} v1 |
| Ledger trial | {trial} |
| Registered research question | {question}: {question_text} |
| Proposed by (role or AI) and date | options strategist and flow analyst (Claude, EDGE2 builder), 25 Oct 2026 |
| Who pays and why | {who_pays} |
| Forecast it rests on | none (the sign of the FII net index-futures change) |
| Instrument and structure | NIFTY weekly 2-leg credit spread: {structure}; never a naked short leg |
| Entry rule | {entry} |
| Exit rule | held to expiry, cash-settled at the expiry day's index close |
| Size | 1 lot of the contract's market lot on the entry session |
| Worst loss in Rs | at most Rs 10,000 modelled at entry (the cap), plus charges and pads |
| Expected gross per trade, with source | the held-out read; the gross bar is Rs 260 a lot (protocol section 6) |
| Needs a reaction faster than 60 minutes? | no: an opening entry held to settlement |
| Frequency | about 50 cycles a year |

```factory
id: {id}
version: 1
trial: {trial}
experiment: {experiment}
description: "EDGE2 F8 {code}: FII-side NIFTY weekly credit spread, {structure} (exploratory)"
question: {question}
hypothesis: yes
measurement: no
data_sets: [{data_sets}]
measures: "mean net per trade after C1's charges and the Rs 1 pad, one lot, held to settlement (protocol sections 6-8)"
```
"""


def card_id(code: str) -> str:
    return f"EDGE2-F8-{code}"


def card_text(code: str, trial: int) -> str:
    return CARD.format(id=card_id(code), trial=trial, question=QUESTION, question_text=QUESTION_TEXT,
                       who_pays=WHO_PAYS, structure=STRUCTURES[code], entry=ENTRY, experiment=EXPERIMENT, code=code,
                       data_sets=", ".join(f'"{d}"' for d in DATA_SETS))  # fmt: skip


def write_cards(first: int, folder: Path = IDEAS) -> list[Path]:
    written = []
    for trial, code in enumerate(STRUCTURES, start=first):
        path = folder / f"{card_id(code)}.md"
        path.write_text(card_text(code, trial), encoding="utf-8")
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
