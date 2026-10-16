"""The paper books page (story P2c, screen W3c; contract `FnoPaperTrades`, page `paper_trades`): each book's own paper
account, never added across books, with its published limits from the C5 profile (`open_risk_cap`, `brake.pause_at`;
never typed), its closed trades after costs and the shadow accounts, each on its own card and never added to a book
(`paper_trades_inputs.py`, `paper_trades_closed.py`). A book's open trade stops the page, named, until per-trade
marks are recorded."""

from __future__ import annotations

from ..constants import BOOKS
from .blocks import BlockBuilder, SessionRows
from .home_inputs import BOOK_FAMILIES
from .paper_trades_closed import ClosedTrade, result
from .paper_trades_inputs import Marks, PaperTradesInputs

FAMILIES = dict(zip(BOOKS, (family for family, _ in BOOK_FAMILIES), strict=True))  # book1_rules is rule, ...


class FnoPaperTradesBlock(BlockBuilder):
    page_key, served_schema = "paper_trades", "FnoPaperTradesResponse"

    def build(self, rows: SessionRows) -> dict:
        return paper_trades(rows.paper_trades)


def paper_trades(inputs: PaperTradesInputs) -> dict:
    accounts = [
        _marks(a.marks) | {"family": FAMILIES[a.book], "cash": a.marks.cash, "open_trades": a.marks.open_trades,
                           "open_max_loss": 0.0, "open_risk_cap": inputs.open_risk_cap,
                           "brake": {"loss_from_high": a.loss_from_high, "pause_at": inputs.pause_at}}
        for a in inputs.accounts
    ]  # fmt: skip
    shadows = [{"name": s.name, "label": s.label, **_marks(s.marks), "open_trades": s.marks.open_trades}
               for s in inputs.shadows]  # fmt: skip
    return {"accounts": accounts, "shadows": shadows, "open": [], "closed": [_closed(t) for t in inputs.closed]}


def _marks(m: Marks) -> dict:
    return {"as_of": m.as_of.isoformat(), "opening_value": m.opening_value, "value": m.value}


def _closed(t: ClosedTrade) -> dict:
    return {
        "trade_id": t.trade_id, "family": FAMILIES[t.book], "strategy": t.strategy, "structure": t.structure,
        "opened_on": t.opened_on.isoformat(), "closed_on": t.closed_on.isoformat(), "gross": t.gross,
        "costs": t.costs, "net": t.net, "result": result(t.net), "exit": t.exit, "fills": None,
    }  # fmt: skip
