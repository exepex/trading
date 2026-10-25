"""Reading the daily run's `fills` result (story E3, fills by book; orchestrator, 25 Oct 2026). Since the AI books trade
beside Book 1, the result is keyed by book: `{book: {"trades": {trade_id: entry}}}`, or `{book: {"outcome", "reason"}}`
when a book opens nothing (blocked, or its orders refused). Before that, Book 1's logs were flat: each trade ID beside
the books' own refusals. Every reader goes through here and reads both shapes; nothing recorded is rewritten."""

from __future__ import annotations

from collections.abc import Iterator, Mapping

from ..constants import BOOKS

TRADES = "trades"


def trade_entries(result: Mapping) -> Iterator[tuple[str | None, str, dict]]:
    """(book, trade ID, entry) of every trade the step wrote or refused; the book is None in an old flat log."""
    for key, value in result.items():
        if not isinstance(value, Mapping):
            continue  # a step-level field: status, reason, retry
        if TRADES in value:
            yield from ((key, trade_id, entry) for trade_id, entry in value[TRADES].items())
        elif key not in BOOKS:
            yield None, key, dict(value)


def trade_fills(result: Mapping, book: str | None = None) -> dict[str, dict]:
    """Each trade's entry by trade ID, for one book when named (two books may share a trade ID: name the book)."""
    return {
        trade_id: entry for owner, trade_id, entry in trade_entries(result) if book is None or owner in (book, None)
    }


def book_refusals(result: Mapping) -> dict[str, dict]:
    """Each book that opened nothing, with its outcome and reason, in either shape."""
    return {key: dict(value) for key, value in result.items()
            if key in BOOKS and isinstance(value, Mapping) and TRADES not in value}  # fmt: skip
