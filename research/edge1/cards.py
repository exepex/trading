"""Protocol section 13's 24 idea cards, one per index and tradeable variant, written from the protocol's own rules so
none is typed by hand. G0 and G2 fields only: G1's gross, tail and cost and G3's sample plan come from run 1 and are
added before `factory screen`, never before run 1 is committed.

    python research/edge1/cards.py --first 71   # writes research/ideas/EDGE1-<index>-<structure>-<exit>.md
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from edge1study.runner import INDICES, variants  # noqa: E402
from edge1study.structures import TRADEABLE  # noqa: E402

IDEAS = ROOT / "research" / "ideas"
EXPERIMENT, QUESTION = "edge1-rule-based-option-trades-2026-10-22", "edge1-rule-based-index-option-trades"
STRUCTURES = {"SC2": "short iron condor: sell the call nearest spot x 1.02 and the put nearest spot x 0.98, buy wings "
                     "one width further out",
              "SC3": "short iron condor: sell the call nearest spot x 1.03 and the put nearest spot x 0.97, buy wings "
                     "one width further out",
              "SF": "short iron fly: sell the ATM call and put, buy wings one width either side"}  # fmt: skip
EXITS = {"T21": "the planned close, 21 calendar days before expiry (the engine's exit day)",
         "EXP": "held to expiry, cash-settled at NSE's final settlement price",
         "SL2": "the first fully traded close with mark >= 3 x credit (a loss of 2 x credit), else the T21 close",
         "TP50": "the first fully traded close with mark <= half the credit, else the T21 close"}  # fmt: skip
DATA_SETS = {"NIFTY": ["NIFTY monthly options | NSE daily closes | 2019-2023",
                       "NIFTY monthly options | NSE daily closes | 2024-2026"],
             "BANKNIFTY": ["BANKNIFTY monthly options | NSE daily closes | 2019 - 20 Oct 2026"]}  # fmt: skip
QUESTION_TEXT = (
    "has a simple rule-based NIFTY or BANKNIFTY monthly option trade made money after real costs? One "
    "Holm family across both indices (protocol section 11)"
)
WHO_PAYS = (
    "option buyers paying a variance risk premium for protection [reasoning only: the premium may be gone "
    "after costs; that is the question]"
)
ENTRY = (
    "the engine's entry day (30-45 days before expiry), at that day's NSE closes, only if every leg traded; the "
    "widest width whose worst loss fits the cap for the cycle's own lot"
)
CARD = """# Idea card: {id} {name}

Written by `research/edge1/cards.py` from `research/edge1/PROTOCOL.md` (frozen in `research/edge1/FREEZE.md`). Every
result is exploratory (spent data, protocol section 2).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | {id} v1 |
| Ledger trial | {trial} |
| Registered research question | {question}: {question_text} |
| Proposed by (role or AI) and date | options strategist (Claude, EDGE1 builder), 22 Oct 2026 |
| Who pays and why | {who_pays} |
| Forecast it rests on | none |
| Instrument and structure | {index} monthly options, the engine's monthly cycle; {structure}; never a naked short leg |
| Entry rule | {entry} |
| Exit rule | {exit} |
| Size | 1 lot of the cycle's own market lot (protocol section 8) |
| Worst loss in Rs | at most Rs 10,000 modelled at entry (the cap), plus charges and pads |
| Expected gross per trade, with source | run 1 (2019-2022), added before G1 |
| Needs a reaction faster than 60 minutes? | no: every rule reads daily closes |
| Frequency | 12 cycles a year at most; fewer when an entry is skipped |

```factory
id: {id}
version: 1
trial: {trial}
experiment: {experiment}
description: "EDGE1 {index} {code} {rule}: {short} (exploratory: spent data)"
question: {question}
hypothesis: yes
measurement: no
data_sets: [{data_sets}]
measures: "mean net per complete trade after C1's charges and the Rs 1 pad, one lot (protocol sections 7-11)"
```
"""


def card_id(index: str, code: str, rule: str) -> str:
    return f"EDGE1-{index}-{code}-{rule}"


def write_cards(first: int, folder: Path = IDEAS) -> list[Path]:
    written, trial = [], first
    for index in INDICES:
        for code, rule in variants():
            if code not in TRADEABLE:
                continue
            ident = card_id(index, code, rule)
            text = CARD.format(id=ident, question_text=QUESTION_TEXT, who_pays=WHO_PAYS, entry=ENTRY,
                               name=f"{index} {code} {rule}", trial=trial, question=QUESTION, index=index,
                               structure=STRUCTURES[code], exit=EXITS[rule], experiment=EXPERIMENT, code=code,
                               rule=rule, short=STRUCTURES[code].split(":")[0],
                               data_sets=", ".join(f'"{d}"' for d in DATA_SETS[index]))  # fmt: skip
            path = folder / f"{ident}.md"
            path.write_text(text, encoding="utf-8")
            written.append(path)
            trial += 1
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=int, required=True, help="the next free ledger trial number")
    for path in write_cards(parser.parse_args().first):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
