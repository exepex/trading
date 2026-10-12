"""A separate writer process for the E1 multi-process tests (not a test module itself).

    python tests/books/account_worker.py '<json spec>'

Spec: root, book, fills (list of [fill_id, trade_id, side, price, units]), start_at (epoch seconds to wait for, so
several workers try at the same moment), hold (seconds to keep the lock after writing), lease (seconds), and die:
"" (normal), "holding" (killed while holding the lock, before writing), "before_view" (killed after the second fill's
ledger line, before its positions view) or "half_line" (killed after writing half of the second fill's line).
Exit code 0 = wrote, 3 = account busy (wrote nothing). Prints a JSON line with what happened.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fno.accounting.ledgers import Order  # noqa: E402
from fno.books.account import AccountWriter  # noqa: E402
from fno.books.fills import Fill  # noqa: E402
from fno.books.lock import AccountBusy  # noqa: E402
from fno.composition import open_account_writer  # noqa: E402
from fno.models import IST  # noqa: E402

CHARGES = {"brokerage_per_order": 20.0, "stt_sell_pct": 0.15, "exchange_txn_pct": 0.03503, "sebi_per_crore": 10.0,
           "ipft_per_crore": 50.0, "stamp_duty_buy_pct": 0.003, "gst_pct": 18.0}  # fmt: skip


def make_fill(fill_id: str, trade_id: str, side: str, price: float, units: int) -> Fill:
    when = datetime(2026, 10, 13, 15, 5, tzinfo=IST)
    return Fill.priced(fill_id, trade_id, when, f"NIFTY-{trade_id}-{side}", Order(side, price, units, 0.5), CHARGES)


def die() -> None:
    os.kill(os.getpid(), signal.SIGKILL)


def arm(mode: str) -> None:
    """Make the second ledger append (or the view after it) kill this process, as a crash would."""
    appends = {"n": 0}
    append, write_positions = AccountWriter._append_ledger_row, AccountWriter._write_positions

    def counting_append(self, row):
        appends["n"] += 1
        if mode == "half_line" and appends["n"] == 2:
            path = self.account.file("cash_ledger.csv")
            text = ",".join(row.values())
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(text[: len(text) // 2])
                fh.flush()
                os.fsync(fh.fileno())
            die()
        append(self, row)

    def maybe_die_view(self):
        if mode == "before_view" and appends["n"] == 2:
            die()
        write_positions(self)

    AccountWriter._append_ledger_row = counting_append
    AccountWriter._write_positions = maybe_die_view


def main(spec: dict) -> int:
    time.sleep(max(0.0, spec.get("start_at", 0) - time.time()))
    arm(spec.get("die", ""))
    try:
        with open_account_writer(spec["book"], Path(spec["root"]), spec.get("lease", 600.0)) as writer:
            if spec.get("die") == "holding":
                die()
            applied = [writer.apply_fill(make_fill(*f)) for f in spec["fills"]]
            time.sleep(spec.get("hold", 0.0))
    except AccountBusy as busy:
        print(json.dumps({"pid": os.getpid(), "busy": str(busy)}))
        return 3
    print(json.dumps({"pid": os.getpid(), "applied": applied}))
    return 0


if __name__ == "__main__":
    sys.exit(main(json.loads(sys.argv[1])))
