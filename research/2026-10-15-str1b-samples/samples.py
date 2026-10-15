"""Story STR1b-1 real-output sample (quality rule 6), a dry run of the committed code: no post, no order, no live data.
The margin at entry per lot at the owner's factor 1.45 on NSE's real 14 Oct 2026 rows (A14's builder on
`nsccl.20261014.i1.zip`; tests/risk/fixtures/margins_2026-10-14.csv), before STR1b (uncapped) and now; then the refusal
of an STR1 version by the activation gate. Run: python research/2026-10-15-str1b-samples/samples.py"""

import csv
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fno.risk.inputs import TradeTerms  # noqa: E402
from fno.risk.margin_age import DaysOld  # noqa: E402
from fno.risk.margins import MarginTable, MultiplierMargin  # noqa: E402
from fno.risk.settings import StressedMarginSettings  # noqa: E402

ROWS = ROOT / "tests" / "risk" / "fixtures" / "margins_2026-10-14.csv"
DAY, K, LOT = date(2026, 10, 14), 1.45, 65
SHOWN = [("LC", 0), ("LP", 300), ("CDS", 200), ("PDS", 300), ("CCS", 100), ("PCS", 100), ("SF", 100), ("SC", 300),
         ("BF", 300)]  # fmt: skip


def capital_table() -> None:
    margin = MultiplierMargin(MarginTable(ROWS, DaysOld(7), LOT), StressedMarginSettings("multiplier", K, "owner", DAY,
                                                                                         30, None))  # fmt: skip
    rows = {(r["structure"], float(r["width"])): r for r in csv.DictReader(ROWS.open(encoding="utf-8"))}
    print(
        "Margin at entry per lot, 14 Oct 2026 real rows, factor 1.45 (Rs): code width | before | now | broker | reserve"
    )
    for code, width in SHOWN:
        r = rows[(code, float(width))]
        scan, nov, exposure = (float(r[f"{k}_per_lot_rs"]) for k in ("scan", "nov", "exposure"))
        before = max(0.0, K * scan - nov) + exposure
        terms = TradeTerms(code, float(width), 1)
        now, broker = margin.margin_at_entry(terms, DAY), margin.broker_margin(terms, DAY)
        print(f"  {code:3} {width:>3} | {before:>10,.2f} | {now:>10,.2f} | {broker:>10,.2f} | {now - broker:>9,.2f}")


def refused_version() -> None:
    from tests.playbook.builders import changer, commit_all, document, filled_evidence, repository, write

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        doc = document(evidence=filled_evidence(repository(root)))
        doc["structure"] = dict(doc["structure"], code="PCS", widths=[200, 100])
        write(root / "playbook", doc)
        commit_all(root, "candidate")
        for status in ("research", "paper"):
            try:
                changer(root).change("sc-test", 1, status, "owner", DAY)
            except Exception as refused:  # noqa: BLE001 - the sample prints the refusal as the desk would see it
                print(f"Status change to {status} refused: {refused}")


if __name__ == "__main__":
    capital_table()
    refused_version()
