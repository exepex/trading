"""What the paper books page publishes (story P2c, screen W3c), read from each book's own paper account (E1,
`journal/<book>/account/`, Drive only: downloaded by E2c's `download_private_records` before the publish, read in
memory, never written anywhere else) and the C5 profile's published limits.

- **The marks:** each book's last `equity_history.csv` row on or before the session, as Home's books are (P10).
- **The brake:** C2's own figures: the closed-equity series of the book's closed trades (`closed_equity_series`) and
  its high-water mark after any owner restart (`high_water_mark`), so the page shows the loss the brake measures.
- **Closed trades and shadow accounts** (part 2, `paper_trades_closed.py`): each named as "Strategy <k>, version <n>",
  never by its version tag.
- **Not computed yet (held, never a guessed figure):** a book's open trade holds this page only (story P11): its marks
  and unrealised profit need the session's per-trade marks, and no record holds them yet (E3 keeps them in memory).
  So does a trade or shadow it cannot label, and a brake history C2 refuses. The reason is a fixed sentence, never an
  amount or a book id."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path

from ..books.account import PaperAccount
from ..books.equity import TradePosition, trade_positions
from ..constants import SHADOW_PREFIX
from ..desk.private_files import paper_accounts
from ..desk.records import DeskRecords
from ..desk.trade_counts import version_key
from ..models import IST
from ..playbook.measurement import MEASUREMENT, is_measurement
from ..playbook.schema import Strategy
from ..risk.book_view import closed_equity_series
from ..risk.drawdown import equity_at, high_water_mark
from ..risk.inputs import RiskInputError
from ..risk.overrides import brake_restarts
from ..risk.profile_settings import ProfileSettings
from .paper_trades_closed import NOT_IN_REGISTRY, STRATEGY_LABEL, ClosedTrade, ClosedTrades, PageCannotBeBuilt

OPEN_NOT_BUILT = (
    "A book holds an open trade, and this page cannot mark it for the session yet"  # no per-trade marks (E3)
)
BRAKE_UNREADABLE = "A book's drawdown brake history cannot be read, so its loss from the high is not shown"
SHADOW = "shadow"  # a candidate tested on paper; a measurement version (R3, B0) is MEASUREMENT, never a candidate
NO_VERSION_FILE = "A shadow account's version file cannot be read, so it is never given a label"

Versions = Callable[[str, int], Strategy | None]  # (name, version) -> its playbook file, None when it cannot be read


@dataclass(frozen=True)
class Marks:
    as_of: date
    opening_value: float
    value: float
    cash: float
    open_trades: int


@dataclass(frozen=True)
class AccountFigures:
    book: str
    marks: Marks
    loss_from_high: float


@dataclass(frozen=True)
class ShadowFigures:
    name: str
    label: str
    marks: Marks


@dataclass(frozen=True)
class PaperTradesInputs:
    day: date
    accounts: list[AccountFigures]
    pause_at: float  # C5: the drawdown brake, in rupees of closed equity below its high
    open_risk_cap: float  # C5: the cap on the open positions' maximum losses
    shadows: list[ShadowFigures] = field(default_factory=list)
    closed: list[ClosedTrade] = field(default_factory=list)  # every book's, newest first
    held: str | None = None  # why the page cannot be built today (story P11 holds only this page)


class PaperBooksReader:
    def __init__(
        self, root: Path, books: tuple[str, ...], profile: ProfileSettings, closed: ClosedTrades, versions: Versions
    ):
        self.root, self.books, self.profile, self.closed, self.versions = Path(root), books, profile, closed, versions

    def on(self, day: date) -> PaperTradesInputs:
        try:
            return self._inputs(day)
        except PageCannotBeBuilt as cannot:
            return PaperTradesInputs(day, [], self.profile.drawdown_brake_rs, self.profile.open_risk_cap_rs,
                                     held=cannot.reason)  # fmt: skip

    def _inputs(self, day: date) -> PaperTradesInputs:
        accounts, closed = [], []
        for book in self.books:
            account = PaperAccount(self.root, book)
            done, still_open = _trades(account, day)
            if still_open:
                raise PageCannotBeBuilt(OPEN_NOT_BUILT)
            accounts.append(AccountFigures(book, self._marks(account, day), self._loss_from_high(account, day, done)))
            closed += [self.closed.of(DeskRecords(account), t) for t in done]
        shadows = [
            self._shadow(a, day) for a in paper_accounts(self.root) if a not in self.books
        ]  # after E2c's download
        closed.sort(key=lambda t: (t.closed_on, t.trade_id), reverse=True)
        return PaperTradesInputs(
            day, accounts, self.profile.drawdown_brake_rs, self.profile.open_risk_cap_rs, shadows, closed
        )

    def _marks(self, account: PaperAccount, day: date) -> Marks:
        rows = [r for r in account.equity_history() if date.fromisoformat(r["date"]) <= day]
        if not rows:  # not opened by then: its opening balance, nothing traded
            opening = float(account.ledger_rows()[0]["amount_rs"]) if account.started else self.profile.paper_account_rs
            return Marks(day, opening, opening, opening, 0)
        capital = account.capital(datetime.combine(day, time.max, IST))  # in force that day (E1b)
        last = rows[-1]
        return Marks(date.fromisoformat(last["date"]), capital, float(last["marked_equity_rs"]), float(last["cash_rs"]),
                     int(last["open_trades"]))  # fmt: skip

    def _loss_from_high(self, account: PaperAccount, day: date, closed: list[TradePosition]) -> float:
        if not account.started:
            return 0.0
        start = date.fromisoformat(account.ledger_rows()[0]["filled_at"][:10])
        series = closed_equity_series(start, account.capital(datetime.combine(day, time.max, IST)), closed)
        try:
            restarts = brake_restarts(self.root, account.book, day)
            high, _ = high_water_mark(series, restarts, self.profile.drawdown_brake_rs)
            return round(high - equity_at(series, day), 2)
        except RiskInputError as exc:
            raise PageCannotBeBuilt(BRAKE_UNREADABLE) from exc

    def _shadow(self, name: str, day: date) -> ShadowFigures:
        strategy, version = version_key(name.removeprefix(SHADOW_PREFIX))
        if strategy not in self.closed.order:
            raise PageCannotBeBuilt(NOT_IN_REGISTRY)
        found = self.versions(strategy, version)
        if found is None:
            raise PageCannotBeBuilt(NO_VERSION_FILE)
        kind = MEASUREMENT if is_measurement(found) else SHADOW  # R3's one source: B0 is measurement, never a candidate
        label = STRATEGY_LABEL.format(k=self.closed.order[strategy], n=version)
        return ShadowFigures(label, kind, self._marks(PaperAccount(self.root, name), day))


def _trades(account: PaperAccount, day: date) -> tuple[list[TradePosition], list[TradePosition]]:
    """(closed by the end of the day, still open at it): the trades first filled on or before the day."""
    done, still_open = [], []
    for trade in trade_positions(account.fills()).values():
        if min(f.filled_at.date() for f in trade.fills) > day:
            continue
        (done if trade.closed_on is not None and trade.closed_on <= day else still_open).append(trade)
    return done, still_open
