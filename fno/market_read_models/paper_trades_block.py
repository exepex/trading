"""The paper books page (story P2c, screen W3c; contract `FnoPaperTrades`, page `paper_trades`): each book's own paper
account, never added across books, with its published limits from the C5 profile (`open_risk_cap`,
`brake.pause_at`; never typed). Today every book is in its empty state: no trade, no shadow account
(`paper_trades_inputs.py` stops the page, named, once one exists, until its mappings are built)."""

from __future__ import annotations

from .blocks import BlockBuilder, SessionRows
from .home_inputs import BOOK_FAMILIES
from .paper_trades_inputs import AccountFigures, PaperTradesInputs


class FnoPaperTradesBlock(BlockBuilder):
    page_key, served_schema = "paper_trades", "FnoPaperTradesResponse"

    def build(self, rows: SessionRows) -> dict:
        return paper_trades(rows.paper_trades)


def paper_trades(inputs: PaperTradesInputs) -> dict:
    accounts = [_account(a, family, inputs) for a, (family, _) in zip(inputs.accounts, BOOK_FAMILIES, strict=True)]
    return {"accounts": accounts, "shadows": [], "open": [], "closed": []}


def _account(a: AccountFigures, family: str, inputs: PaperTradesInputs) -> dict:
    return {
        "family": family, "as_of": a.as_of.isoformat(), "opening_value": a.opening_value, "value": a.value,
        "cash": a.cash, "open_trades": a.open_trades, "open_max_loss": 0.0, "open_risk_cap": inputs.open_risk_cap,
        "brake": {"loss_from_high": a.loss_from_high, "pause_at": inputs.pause_at},
    }  # fmt: skip
