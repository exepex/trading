"""F6's six idea cards (protocol section 8), written from the protocol's own rules. G0 and G2 fields only.

python research/edge2/f6_cards.py --first 115   # writes research/ideas/EDGE2-F6-<signal>-<horizon>.md
"""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IDEAS = ROOT / "research" / "ideas"
EXPERIMENT, QUESTION = "edge2-f6-participant-oi-futures-2026-10-25", "edge2-f6-participant-oi-futures"
QUESTION_TEXT = (
    "EDGE2 F6: does the FII or client net index-futures position in NSE's participant OI file predict the next 1 or 5 "
    "NIFTY futures sessions, traded from the next open, after real costs? One Holm family of 6 (FD, FL, CD x H1, H5); "
    "discovery to 2024 (exploratory), held-out 2025-26 read once after a judge; research only (futures on hold); "
    "protocol research/edge2/F6_PROTOCOL.md"
)
SIGNALS = {"FD": "FII net index-futures change, followed", "FL": "FII net index futures against its 20-session mean, "
           "followed", "CD": "client net index-futures change, faded"}  # fmt: skip
HORIZONS = {"H1": "from the next session's open to its close", "H5": "from the next session's open to the close five "
            "sessions after the signal"}  # fmt: skip
WHO_PAYS = (
    "the other side of FII positioning flow, or retail clients in the fade [some evidence that FII positioning and "
    "retail losses are real; reasoning only that a 1-5 session edge survives costs]"
)
WORST = "unbounded in principle (a future has no cap): reported per trade; research only, never traded under the hold"
DATA_SETS = [
    "Participant open interest (A8) | NSE daily files | 2019 - 2024",
    "Participant open interest (A8) | NSE daily files | 2025 - 2026",
    "NIFTY near-month future | NSE daily open and close (F&O files) | 2019 - 2024",
    "NIFTY near-month future | NSE daily open and close (F&O files) | 2025 - 2026",
]
CARD = """# Idea card: {id}

Written by `research/edge2/f6_cards.py` from `research/edge2/F6_PROTOCOL.md`. Exploratory; research only while
futures are on hold (protocol section 2).

## G0: the idea

| Field | Value |
|---|---|
| Id and version | {id} v1 |
| Ledger trial | {trial} |
| Registered research question | {question}: {question_text} |
| Proposed by (role or AI) and date | derivatives flow analyst and quant (Claude, EDGE2 builder), 25 Oct 2026 |
| Who pays and why | {who_pays} |
| Forecast it rests on | none ({signal}) |
| Instrument and structure | NIFTY future, the nearest expiry on or after the exit session; one lot long or short |
| Entry rule | day t's participant OI file (published after the close) decides; enter at session t+1's open |
| Exit rule | {horizon}, at that session's close |
| Size | 1 lot of the contract's market lot on the entry session |
| Worst loss in Rs | {worst} |
| Expected gross per trade, with source | discovery run, added before G1 |
| Needs a reaction faster than 60 minutes? | no: an open-to-close daily rule |
| Frequency | about 250 signals a year (one a session) |

```factory
id: {id}
version: 1
trial: {trial}
experiment: {experiment}
description: "EDGE2 F6 {code} {horizon_code}: {signal}, {horizon} (exploratory, research only)"
question: {question}
hypothesis: yes
measurement: no
data_sets: [{data_sets}]
measures: "mean net per trade after the futures charges and a 1-point pad, one lot (protocol sections 4-6)"
```
"""


def card_id(code: str, horizon: str) -> str:
    return f"EDGE2-F6-{code}-{horizon}"


def in_trial_order() -> list[tuple[str, str]]:
    return [(code, horizon) for code in SIGNALS for horizon in HORIZONS]


def card_text(code: str, horizon: str, trial: int) -> str:
    return CARD.format(id=card_id(code, horizon), trial=trial, question=QUESTION, question_text=QUESTION_TEXT,
                       who_pays=WHO_PAYS, worst=WORST, signal=SIGNALS[code], horizon=HORIZONS[horizon],
                       experiment=EXPERIMENT, code=code, horizon_code=horizon,
                       data_sets=", ".join(f'"{d}"' for d in DATA_SETS))  # fmt: skip


def write_cards(first: int, folder: Path = IDEAS) -> list[Path]:
    written = []
    for trial, (code, horizon) in enumerate(in_trial_order(), start=first):
        path = folder / f"{card_id(code, horizon)}.md"
        path.write_text(card_text(code, horizon, trial), encoding="utf-8")
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
