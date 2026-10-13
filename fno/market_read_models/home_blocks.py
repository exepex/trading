"""Home's F&O blocks (story P10, W10's contract): the three paper books' accounts (`FnoBooks`, "Who trades") and the
F&O picks panel (`FnoPicks`), each a pure function of the session's Home inputs. The picks panel shows the honest
empty state while no book has an approved strategy."""

from __future__ import annotations

from .blocks import CURRENCY, BlockBuilder, SessionRows

DECISION_UTC = "T09:30:00Z"  # the books decide at 15:00 IST (design 13.5): their figures are as of then
OPEN_TRADE_RISK = (
    "{book} holds {count} open trade(s): its risk used (C2's stress of the open trades) is not computed by this block "
    "yet (story P10), so nothing is published rather than a wrong figure"
)
APPROVED_PICKS = (
    "approved strategies exist ({approved}): their picks are the books' decision records (D3), not built by this block "
    "yet (story P10), so nothing is published rather than an empty panel that is no longer true"
)


class FiguresNotComputed(RuntimeError):
    """A figure this story does not compute yet (an open trade's risk used, an approved strategy's picks)."""


class FnoBooksBlock(BlockBuilder):
    page_key, served_schema = "risk", "FnoBooksResponse"  # W10: "pages risk and scoreboard_b"; the dashboard reads risk

    def build(self, rows: SessionRows) -> dict:
        home = rows.home
        books = []
        for b in home.books:
            if b.open_trades:
                raise FiguresNotComputed(OPEN_TRADE_RISK.format(book=b.name, count=b.open_trades))
            books.append({
                "book": b.number, "family": b.family, "name": b.name, "value": b.value, "pnl": b.pnl,
                "approved": list(home.approved), "limit_used": 0.0, "limit_max": home.limit_max,
                "as_of": rows.day.isoformat() + DECISION_UTC,
            })  # fmt: skip
        return {"currency": CURRENCY, "books": books}


class FnoPicksBlock(BlockBuilder):
    page_key, served_schema = "today", "FnoPicksResponse"  # W10: "fno.pages_history page today (P1)"

    def build(self, rows: SessionRows) -> dict:
        home = rows.home
        if home.approved:
            raise FiguresNotComputed(APPROVED_PICKS.format(approved=", ".join(home.approved)))
        return {"currency": CURRENCY, "fno_state": {"approved": False, "note": home.approval_note}, "rows": [],
                "baskets": {}}  # fmt: skip
