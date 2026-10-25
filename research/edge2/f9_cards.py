"""F9's four idea cards and its fixed event list (protocol sections 3 and 9), written before any price is read.

python research/edge2/f9_cards.py --first 124   # research/ideas/EDGE2-F9-<structure>-<exit>.md and f9_events.csv
"""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IDEAS = ROOT / "research" / "ideas"
EVENTS_IN, EVENTS_OUT = ROOT / "research" / "data" / "events" / "events.csv", Path(__file__).parent / "f9_events.csv"
EVENT_COLUMNS = ("date", "type", "announced_on", "source_url", "announcement_source_url")
EXPERIMENT, QUESTION = "edge2-f9-event-iv-crush-2026-10-25", "edge2-f9-event-iv-crush"
QUESTION_TEXT = (
    "EDGE2 F9: has a defined-risk short NIFTY or BANKNIFTY monthly iron fly or condor, opened at the close before a "
    "scheduled RBI policy decision, Union Budget or election result and closed after it, made money after real costs "
    "and more than on ordinary days? One Holm family of 4 (FLY, CONDOR x E0, E1); exploratory (spent closes); held-out "
    "FINNIFTY and MIDCPNIFTY monthlies read once after a judge; protocol research/edge2/F9_PROTOCOL.md"
)
STRUCTURES = {"FLY": "short iron fly: sell the ATM call and put, buy wings one width either side",
              "CONDOR": "short iron condor: sell the call and put one event-free session's implied move out, buy wings "
                        "one width beyond"}  # fmt: skip
EXITS = {"E0": "the close of the event day's session", "E1": "the close of the session after the event day"}
INSTRUMENT = "NIFTY and BANKNIFTY monthly options, the nearest expiry at least 5 sessions after the exit"
WHO_PAYS = (
    "hedgers buying protection before scheduled announcements (the event premium) [some evidence abroad; not measured "
    "on Indian index options here]"
)
DATA_SETS = [
    "NIFTY monthly options | NSE daily closes | 2019-2023",
    "NIFTY monthly options | NSE daily closes | 2024-2026",
    "BANKNIFTY monthly options | NSE daily closes | 2019 - 20 Oct 2026",
    "Event calendar (A6) | dates | 2019-2026",
]
CARD = """# Idea card: {id}

Written by `research/edge2/f9_cards.py` from `research/edge2/F9_PROTOCOL.md`. Exploratory (spent closes); events
fixed in `research/edge2/f9_events.csv` before any price was read.

## G0: the idea

| Field | Value |
|---|---|
| Id and version | {id} v1 |
| Ledger trial | {trial} |
| Registered research question | {question}: {question_text} |
| Proposed by (role or AI) and date | volatility trader and options strategist (Claude, EDGE2 builder), 25 Oct 2026 |
| Who pays and why | {who_pays} |
| Forecast it rests on | none (the A6 event calendar) |
| Instrument and structure | {instrument}; {structure}; never a naked short leg |
| Entry rule | the close of the last session before the event day, every leg traded; exposed to the overnight gap |
| Exit rule | {exit} |
| Size | 1 lot of the contract's market lot on the entry session |
| Worst loss in Rs | at most Rs 10,000 modelled at entry (the cap), plus charges and pads |
| Expected gross per trade, with source | the discovery run; the gross bar is Rs 820 a lot (protocol section 6) |
| Needs a reaction faster than 60 minutes? | no: close to close |
| Frequency | about 8 scheduled events a year, 2 trades each |

```factory
id: {id}
version: 1
trial: {trial}
experiment: {experiment}
description: "EDGE2 F9 {code} {exit_code}: event IV crush, {short}, exit {exit} (exploratory)"
question: {question}
hypothesis: yes
measurement: no
data_sets: [{data_sets}]
measures: "mean net per trade after C1's charges and the Rs 1 pad on 4 legs in and out, one lot (protocol sections 4-7)"
```
"""


def card_id(code: str, exit_code: str) -> str:
    return f"EDGE2-F9-{code}-{exit_code}"


def in_trial_order() -> list[tuple[str, str]]:
    return [(code, exit_code) for code in STRUCTURES for exit_code in EXITS]


def card_text(code: str, exit_code: str, trial: int) -> str:
    return CARD.format(id=card_id(code, exit_code), trial=trial, question=QUESTION, question_text=QUESTION_TEXT,
                       who_pays=WHO_PAYS, instrument=INSTRUMENT, structure=STRUCTURES[code], exit=EXITS[exit_code],
                       experiment=EXPERIMENT,
                       code=code, exit_code=exit_code, short=STRUCTURES[code].split(":")[0],
                       data_sets=", ".join(f'"{d}"' for d in DATA_SETS))  # fmt: skip


def write_events(source: Path = EVENTS_IN, target: Path = EVENTS_OUT) -> int:
    """Every scheduled A6 event, in date order, with its type, announcement date and sources."""
    with source.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["scheduled"] == "yes"]
    with target.open("w", encoding="utf-8", newline="") as f:
        out = csv.DictWriter(f, EVENT_COLUMNS, extrasaction="ignore", lineterminator="\n")
        out.writeheader()
        out.writerows(sorted(rows, key=lambda r: r["date"]))
    return len(rows)


def write_cards(first: int, folder: Path = IDEAS) -> list[Path]:
    written = []
    for trial, (code, exit_code) in enumerate(in_trial_order(), start=first):
        path = folder / f"{card_id(code, exit_code)}.md"
        path.write_text(card_text(code, exit_code, trial), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=int, required=True, help="the next free ledger trial number")
    for path in write_cards(parser.parse_args().first):
        print(path.relative_to(ROOT))
    print(f"{EVENTS_OUT.relative_to(ROOT)}: {write_events()} scheduled events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
