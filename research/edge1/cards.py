"""Protocol section 13's 24 idea cards, one per index and tradeable variant, then the 4 measurement cards (NS and NT
per index, `measurement: yes`, never screened), written from the protocol's own rules so none is typed by hand. G0
and G2 fields only: G1's gross, tail and cost and G3's sample plan come from run 1 and are
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
from edge1study.structures import NOT_TRADEABLE, TRADEABLE  # noqa: E402

IDEAS = ROOT / "research" / "ideas"
EXPERIMENT, QUESTION = "edge1-rule-based-option-trades-2026-10-22", "edge1-rule-based-index-option-trades"
STRUCTURES = {"SC2": "short iron condor: sell the call nearest spot x 1.02 and the put nearest spot x 0.98, buy wings "
                     "one width further out",
              "SC3": "short iron condor: sell the call nearest spot x 1.03 and the put nearest spot x 0.97, buy wings "
                     "one width further out",
              "SF": "short iron fly: sell the ATM call and put, buy wings one width either side",
              "NS": "naked short strangle: SC2's two shorts and no wings",
              "NT": "naked short straddle: SF's ATM body and no wings"}  # fmt: skip
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
| Instrument and structure | {index} monthly options, the engine's monthly cycle; {structure}; {legs_note} |
| Entry rule | {entry} |
| Exit rule | {exit} |
| Size | 1 lot of the cycle's own market lot (protocol section 8) |
| Worst loss in Rs | {worst} |
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
hypothesis: {hypothesis}
measurement: {measurement}
data_sets: [{data_sets}]
measures: "mean net per complete trade after C1's charges and the Rs 1 pad, one lot (protocol sections 7-11)"
```
"""


def card_id(index: str, code: str, rule: str) -> str:
    return f"EDGE1-{index}-{code}-{rule}"


def _yes(flag: bool) -> str:
    return "yes" if flag else "no"


def _legs_note(code: str) -> str:
    return (
        "never a naked short leg"
        if code in TRADEABLE
        else f"a measurement only, never screened or nominated ({NOT_TRADEABLE})"
    )


def _worst(code: str) -> str:
    if code in TRADEABLE:
        return "at most Rs 10,000 modelled at entry (the cap), plus charges and pads"
    return "unbounded; the report shows the worst trade per lot and the margin it needed (owner's Q1 answer)"


def card_text(index: str, code: str, rule: str, trial: int) -> str:
    return CARD.format(id=card_id(index, code, rule), question_text=QUESTION_TEXT, who_pays=WHO_PAYS, entry=ENTRY,
                       name=f"{index} {code} {rule}", trial=trial, question=QUESTION, index=index,
                       structure=STRUCTURES[code], exit=EXITS[rule], experiment=EXPERIMENT, code=code, rule=rule,
                       hypothesis=_yes(code in TRADEABLE), measurement=_yes(code not in TRADEABLE),
                       legs_note=_legs_note(code), worst=_worst(code), short=STRUCTURES[code].split(":")[0],
                       data_sets=", ".join(f'"{d}"' for d in DATA_SETS[index]))  # fmt: skip


def in_trial_order() -> list[tuple[str, str, str]]:
    """The 24 tradeable variants (NIFTY then BANKNIFTY), then the 4 measurements: section 13's consecutive trials."""
    every = [(index, code, rule) for index in INDICES for code, rule in variants()]
    return [v for v in every if v[1] in TRADEABLE] + [v for v in every if v[1] not in TRADEABLE]


def write_cards(first: int, folder: Path = IDEAS) -> list[Path]:
    written = []
    for trial, (index, code, rule) in enumerate(in_trial_order(), start=first):
        path = folder / f"{card_id(index, code, rule)}.md"
        path.write_text(card_text(index, code, rule, trial), encoding="utf-8")
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
