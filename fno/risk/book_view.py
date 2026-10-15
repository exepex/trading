"""One book's risk view, read from its own paper account (E1) and its own owner overrides only (story C2, criterion 7).

Positions, cash and closed equity come from the account's ledger; marks from the market snapshot. The terms of each
open trade (structure, width, lots: what its margin row is looked up by) are recorded when the trade is decided and
passed in; an open trade without terms is an input error, so its margin is never guessed.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from itertools import accumulate
from pathlib import Path

from ..books.account import PaperAccount
from ..books.equity import TradePosition, trade_positions
from .inputs import Market, OpenTrade, RiskBook, RiskInputError, TradeTerms
from .overrides import brake_restarts


def closed_equity_series(start_day: date, starting_cash: float, trades: list[TradePosition]) -> tuple:
    """(day, closed equity at that day's close): the start, then each day on which trades closed."""
    by_day: dict[date, float] = {}
    for trade in trades:
        if not trade.is_open:
            by_day[trade.closed_on] = by_day.get(trade.closed_on, 0.0) + trade.cash_flow
    days = sorted(by_day)
    equities = accumulate((by_day[d] for d in days), initial=starting_cash)
    return tuple(zip((start_day, *days), equities, strict=True))


def _open_trade(trade: TradePosition, terms: Mapping[str, TradeTerms]) -> OpenTrade:
    if trade.trade_id not in terms:
        raise RiskInputError(f"open trade {trade.trade_id} has no recorded terms (structure, width, lots)")
    units = {contract: n for contract, n in trade.units.items() if n}
    opened_on = min(fill.filled_at.date() for fill in trade.fills)
    return OpenTrade(trade.trade_id, terms[trade.trade_id], units, trade.cash_flow, opened_on)


def load_risk_book(
    root: Path, book: str, market: Market, terms: Mapping[str, TradeTerms], premium_reserved: float = 0.0
) -> RiskBook:
    """The book's account marked at `market`, with margin blocked left at zero: the margin rule adds every open
    trade's margin itself (the broker's live total would count a short structure's marked loss twice)."""
    account = PaperAccount(root, book)
    fills = account.fills()
    trades = list(trade_positions(fills).values())
    start_day = date.fromisoformat(account.ledger_rows()[0]["filled_at"]) if account.started else market.day
    state = account.state(market.marks(), margin_blocked=0.0, premium_reserved=premium_reserved)
    return RiskBook(
        book,
        state,
        tuple(_open_trade(t, terms) for t in trades if t.is_open),
        closed_equity_series(start_day, state.starting_cash, trades),
        brake_restarts(root, book, market.day),
    )
