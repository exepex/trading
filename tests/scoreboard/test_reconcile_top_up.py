"""Story E1b criterion 7: S2's reconciliation still holds to the rupee with a top-up in the ledger: the cash change is
measured against capital, and capital is never part of any trade."""

from datetime import date, datetime

from fno.accounting.ledgers import Order
from fno.books.account import AccountWriter, PaperAccount
from fno.books.fills import Fill
from fno.books.lock import AccountLock
from fno.config import ROOT, load_config
from fno.constants import BOOK1_RULES
from fno.models import IST
from fno.scoreboard.reconcile import reconciliation

CHARGES = load_config(ROOT / "config.yaml")["charges"]


def test_the_cash_ledger_reconciles_with_a_top_up_between_fills(tmp_path):
    def fill(fill_id, side, price, day):
        when = datetime(2026, 10, day, 15, 15, tzinfo=IST)
        return Fill.priced(fill_id, "t", when, "NIFTY26102725000CE", Order(side, price, 65, 0.0), CHARGES)

    with AccountLock(tmp_path, BOOK1_RULES) as lock:
        writer = AccountWriter(PaperAccount(tmp_path, BOOK1_RULES), lock, 500_000.0)
        writer.start(date(2026, 10, 13))
        writer.apply_fill(fill("b", "buy", 200.0, 14))
        writer.apply_fill(fill("s", "sell", 150.0, 15))
        writer.top_up(datetime(2026, 10, 16, 17, 0, tzinfo=IST), 2_000_000.0)
    account = PaperAccount(tmp_path, BOOK1_RULES)
    result = reconciliation(account, [], [])
    assert result["checks"]["cash_ledger"]
    assert result["cash_change_rs"] == round(sum(f.amount for f in account.fills()), 2) < 0  # the trade's loss only
