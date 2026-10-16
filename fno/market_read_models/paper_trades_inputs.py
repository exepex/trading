"""What the paper books page publishes (story P2c, screen W3c), read from each book's own paper account (E1,
`journal/<book>/account/`, Drive only: downloaded by E2c's `download_private_records` before the publish, read in
memory, never written anywhere else) and the C5 profile's published limits.

- **The marks:** each book's last `equity_history.csv` row on or before the session, as Home's books are (P10).
- **The brake:** C2's own figures: the closed-equity series of the book's closed trades (`closed_equity_series`) and
  its high-water mark after any owner restart (`high_water_mark`), so the page shows the loss the brake measures.
- **Not computed yet (fail closed, named, never a guessed figure):** an open or closed trade, or a shadow account,
  stops the page until their mappings are agreed (the trades' names, structures, exits and E8's fills); the message
  names the book and the count, never an amount."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

from ..books.account import PaperAccount
from ..books.equity import trade_positions
from ..desk.private_files import paper_accounts
from ..models import IST
from ..risk.book_view import closed_equity_series
from ..risk.drawdown import equity_at, high_water_mark
from ..risk.inputs import RiskInputError
from ..risk.overrides import brake_restarts
from ..risk.profile_settings import ProfileSettings
from .home_blocks import FiguresNotComputed

TRADES_NOT_BUILT = "{book}: {count} paper trade(s) on record; the paper books page does not build trades yet (P2c)"
SHADOWS_NOT_BUILT = "{count} shadow account(s) on record; the paper books page does not build shadows yet (P2c)"
BRAKE_UNREADABLE = "{book}: the drawdown brake's history cannot be read ({problem})"


@dataclass(frozen=True)
class AccountFigures:
    book: str
    as_of: date
    opening_value: float
    value: float
    cash: float
    open_trades: int
    loss_from_high: float


@dataclass(frozen=True)
class PaperTradesInputs:
    day: date
    accounts: list[AccountFigures]
    pause_at: float  # C5: the drawdown brake, in rupees of closed equity below its high
    open_risk_cap: float  # C5: the cap on the open positions' maximum losses


class PaperBooksReader:
    def __init__(self, root: Path, books: tuple[str, ...], profile: ProfileSettings):
        self.root, self.books, self.profile = Path(root), books, profile

    def on(self, day: date) -> PaperTradesInputs:
        shadows = [a for a in paper_accounts(self.root) if a not in self.books]  # read after E2c's download
        if shadows:
            raise FiguresNotComputed(SHADOWS_NOT_BUILT.format(count=len(shadows)))
        accounts = [self._figures(book, day) for book in self.books]
        return PaperTradesInputs(day, accounts, self.profile.drawdown_brake_rs, self.profile.open_risk_cap_rs)

    def _figures(self, book: str, day: date) -> AccountFigures:
        account = PaperAccount(self.root, book)
        trades = [
            t for t in trade_positions(account.fills()).values() if min(f.filled_at.date() for f in t.fills) <= day
        ]
        if trades:
            raise FiguresNotComputed(TRADES_NOT_BUILT.format(book=book, count=len(trades)))
        rows = [r for r in account.equity_history() if date.fromisoformat(r["date"]) <= day]
        if not rows:  # not opened by then: its opening balance, nothing traded
            opening = float(account.ledger_rows()[0]["amount_rs"]) if account.started else self.profile.paper_account_rs
            return AccountFigures(book, day, opening, opening, opening, 0, 0.0)
        capital = account.capital(datetime.combine(day, time.max, IST))  # in force that day (E1b)
        last = rows[-1]
        return AccountFigures(
            book, date.fromisoformat(last["date"]), capital, float(last["marked_equity_rs"]), float(last["cash_rs"]),
            int(last["open_trades"]), self._loss_from_high(account, book, day, capital, trades),
        )  # fmt: skip

    def _loss_from_high(self, account: PaperAccount, book: str, day: date, capital: float, trades: list) -> float:
        start = date.fromisoformat(account.ledger_rows()[0]["filled_at"][:10])
        series = closed_equity_series(start, capital, trades)
        try:
            high, _ = high_water_mark(series, brake_restarts(self.root, book, day), self.profile.drawdown_brake_rs)
            return round(high - equity_at(series, day), 2)
        except RiskInputError as exc:
            raise FiguresNotComputed(BRAKE_UNREADABLE.format(book=book, problem=exc)) from exc
