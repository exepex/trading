"""A book's Rs 5 lakh paper account (story E1, design 12.6), stored under `journal/<book>/account/`:

- `cash_ledger.csv`: append-only, one row per fill (plus the opening balance). The source of truth.
- `positions.json`: a view rebuilt from the ledger after every write (open legs, cash, closed equity, closed trades).
- `equity_history.csv`: one row per day (cash, closed and marked equity), rewritten for a repeated day.

Reading needs no lock (`PaperAccount`). Writing needs the book's held single-writer lock (`AccountWriter`, opened by
`fno.composition.open_account_writer`). Crash safety: a fill is one appended line, flushed to disk before the view is
rebuilt; a restart drops a half-written last line and rebuilds the view, and a fill ID already in the ledger is not
applied again, so a retried run neither loses nor repeats a fill.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path
from typing import Protocol

from ..accounting.ledgers import Trade
from .equity import AccountState, Mark, account_state, trade_positions, unmarked_state
from .files import append_durably, complete_lines, csv_text, drop_partial_line, write_atomic
from .fills import FILL_KINDS, LEDGER_COLUMNS, Fill, opening_row, same_fill
from .paths import account_folder, file_in_account

CASH_LEDGER_FILE = "cash_ledger.csv"
POSITIONS_FILE = "positions.json"
EQUITY_HISTORY_FILE = "equity_history.csv"
EQUITY_COLUMNS = ("date", "cash_rs", "closed_equity_rs", "marked_equity_rs", "open_trades", "stale_marks", "fills")
STARTING_CASH_RS = 500_000.0  # owner decision and design 12.6: Rs 5 lakh per book
OPENING_ENTRY_ID = "opening"


class AccountError(RuntimeError):
    """A write the account refuses: not started, no lock, a fill ID reused for a different fill, a closed trade."""


class WriterLock(Protocol):
    """What a writer needs from the single-writer lock (`fno.books.lock.AccountLock`)."""

    book: str
    path: Path

    @property
    def held(self) -> bool: ...


def _equity_row(day: date, state: AccountState, fills: int) -> dict[str, str]:
    return {
        "date": day.isoformat(),
        "cash_rs": f"{state.cash:.2f}",
        "closed_equity_rs": f"{state.closed_equity:.2f}",
        "marked_equity_rs": f"{state.marked_equity:.2f}",
        "open_trades": str(state.open_trades),
        "stale_marks": ";".join(state.stale_marks),
        "fills": str(fills),
    }


class PaperAccount:
    """Read access to one book's account. Every file it touches is inside that book's own account folder."""

    def __init__(self, root: Path, book: str):
        self.book = book
        self.folder = account_folder(root, book)

    def file(self, name: str) -> Path:
        return file_in_account(self.folder, name)

    @property
    def started(self) -> bool:
        return self.file(CASH_LEDGER_FILE).exists()

    def ledger_rows(self) -> list[dict[str, str]]:
        if not self.started:
            return []
        reader = csv.DictReader(io.StringIO(complete_lines(self.file(CASH_LEDGER_FILE).read_text(encoding="utf-8"))))
        if tuple(reader.fieldnames or ()) != LEDGER_COLUMNS:
            raise AccountError(f"{self.book}: cash ledger columns must be {LEDGER_COLUMNS}")
        return list(reader)

    def starting_cash(self) -> float:
        rows = self.ledger_rows()
        if not rows:
            raise AccountError(f"{self.book}: the account has not been started")
        return float(rows[0]["amount_rs"])

    def fills(self) -> list[Fill]:
        return [Fill.from_row(row) for row in self.ledger_rows() if row["kind"] in FILL_KINDS]

    def state(self, marks: dict[str, Mark], margin_blocked: float = 0.0, premium_reserved: float = 0.0) -> AccountState:
        return account_state(self.starting_cash(), self.fills(), marks, margin_blocked, premium_reserved)

    def summary(self) -> dict:
        """Everything that needs no marks: the content of `positions.json`."""
        rows = self.ledger_rows()
        return {"book": self.book, "ledger_rows": len(rows), "starting_cash_rs": self.starting_cash()} | unmarked_state(
            self.starting_cash(), self.fills()
        )

    def closed_trades(self) -> list[Trade]:
        """Closed trades in the cost accountant's form (C1), for the three ledgers."""
        return [t.as_ledger_trade() for t in trade_positions(self.fills()).values() if not t.is_open]

    def equity_history(self) -> list[dict[str, str]]:
        path = self.file(EQUITY_HISTORY_FILE)
        return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")))) if path.exists() else []


class AccountWriter:
    """The only way to change an account. Each write first checks that this book's lock is held."""

    def __init__(self, account: PaperAccount, lock: WriterLock):
        self.account = account
        self._lock = lock
        self.require_lock()
        if account.started:
            self._recover()

    def start(self, day: date) -> bool:
        """Open the account with Rs 5 lakh and no positions. Done once; False (and nothing written) if it exists."""
        self.require_lock()
        if self.account.started:
            return False
        opening = opening_row(OPENING_ENTRY_ID, day.isoformat(), STARTING_CASH_RS)
        first = _equity_row(day, account_state(STARTING_CASH_RS, [], {}), fills=0)
        self._write_atomic(EQUITY_HISTORY_FILE, csv_text(EQUITY_COLUMNS, [first], header=True))
        self._write_atomic(CASH_LEDGER_FILE, csv_text(LEDGER_COLUMNS, [opening], header=True))  # marks "started"
        self._write_positions()
        return True

    def apply_fill(self, fill: Fill) -> bool:
        """Record a fill once. False when this exact fill is already recorded (a retry); an error when its ID was used
        for a different fill or its trade is already closed."""
        self.require_lock()
        rows = self.account.ledger_rows()
        if not rows:
            raise AccountError(f"{self.account.book}: the account has not been started")
        for row in rows:
            if row["entry_id"] == fill.fill_id:
                if same_fill(row, fill):
                    return False
                raise AccountError(f"{self.account.book}: fill ID {fill.fill_id} already records a different fill")
        trade = trade_positions(self.account.fills()).get(fill.trade_id)
        if trade is not None and not trade.is_open:
            raise AccountError(f"{self.account.book}: trade {fill.trade_id} closed on {trade.closed_on}; new ID needed")
        self._append_ledger_row(fill.ledger_row(float(rows[-1]["cash_after_rs"])))
        self._write_positions()
        return True

    def record_equity(self, day: date, marks: dict[str, Mark]) -> AccountState:
        """Write the day's row of the equity history (replacing an earlier row for the same day)."""
        self.require_lock()
        state = self.account.state(marks)
        row = _equity_row(day, state, len(self.account.fills()))
        rows = [r for r in self.account.equity_history() if r["date"] != row["date"]] + [row]
        self._write_atomic(EQUITY_HISTORY_FILE, csv_text(EQUITY_COLUMNS, sorted(rows, key=lambda r: r["date"]), True))
        self._write_positions()
        return state

    def require_lock(self) -> None:
        lock = self._lock
        if not (
            lock.held and lock.book == self.account.book and lock.path.parent.resolve() == self.account.folder.resolve()
        ):
            raise AccountError(f"{self.account.book}: writes need this book's single-writer lock, held")

    def _recover(self) -> None:
        """After a crash: drop a half-written last ledger line, then rebuild the view from the ledger."""
        drop_partial_line(self.account.file(CASH_LEDGER_FILE))
        self._write_positions()

    def _append_ledger_row(self, row: dict[str, str]) -> None:
        append_durably(self.account.file(CASH_LEDGER_FILE), csv_text(LEDGER_COLUMNS, [row], header=False))

    def _write_positions(self) -> None:
        self._write_atomic(POSITIONS_FILE, json.dumps(self.account.summary(), indent=1, sort_keys=True) + "\n")

    def _write_atomic(self, name: str, text: str) -> None:
        write_atomic(self.account.file(name), self.account.file(name + ".tmp"), text)
