"""Small builders for the risk manager's tests (story C2): quotes, markets, books and proposals with fixed prices."""

from __future__ import annotations

from datetime import date, timedelta

from fno.books.equity import AccountState
from fno.constants import OPTION_CALL, OPTION_PUT, STRUCTURE_SHORT_CONDOR, STRUCTURE_SHORT_IRON_FLY
from fno.research_data.panel_reader import FutureQuote
from fno.research_engine.implied_vol import Black76
from fno.research_engine.structures import BOUGHT, SOLD, Leg
from fno.risk.inputs import ContractQuote, Market, OpenTrade, Proposal, ProposedLeg, RiskBook, TradeTerms

DAY = date(2026, 10, 13)
LOT = 65  # NIFTY units per lot (config.yaml lot_sizes)
START = 2_000_000.0  # the owner's paper account (14 Oct 2026)
MODEL = Black76()  # the app's model (fno/risk/wiring.py)
ZERO_CHARGES = dict.fromkeys(
    (
        "brokerage_per_order",
        "stt_sell_pct",
        "exchange_txn_pct",
        "sebi_per_crore",
        "ipft_per_crore",
        "stamp_duty_buy_pct",
        "gst_pct",
    ),
    0.0,
)
CHARGES = {
    "brokerage_per_order": 20.0,
    "stt_sell_pct": 0.15,
    "exchange_txn_pct": 0.03503,
    "sebi_per_crore": 10.0,
    "ipft_per_crore": 50.0,
    "stamp_duty_buy_pct": 0.003,
    "gst_pct": 18.0,
}


def contract(strike: float, kind: str, expiry: date) -> str:
    return f"NIFTY{expiry:%y%m%d}{strike:g}{kind}"


def market(
    spot: float,
    prices: dict[tuple[float, str], float],
    expiry: date,
    iv: float = 0.15,
    day: date = DAY,
    stale: frozenset = frozenset(),
    forward: float | None = None,
    rate: float = 0.065,
) -> Market:
    """A market whose quotes are `(strike, kind) -> mid`, all of one expiry and one implied volatility, with a traded
    same-expiry future at `forward` (the spot unless given)."""
    quotes = {
        contract(k, kind, expiry): ContractQuote(k, kind, expiry, mid, iv, (k, kind) in stale)
        for (k, kind), mid in prices.items()
    }
    future = FutureQuote(expiry, forward or spot, forward or spot, 1, 1)
    return Market(day, spot, rate, quotes, {expiry: future})


def legs_of(spec: list[tuple[float, str, int]]) -> list[Leg]:
    return [Leg(strike, kind, side) for strike, kind, side in spec]


def proposal(trade_id: str, structure: str, width: float, spec, expiry: date, lots: int = 1) -> Proposal:
    proposed = tuple(ProposedLeg(contract(leg.strike, leg.kind, expiry), leg) for leg in legs_of(spec))
    return Proposal(trade_id, TradeTerms(structure, width, lots), LOT, proposed)


def short_fly(atm: float, width: float) -> list[tuple[float, str, int]]:
    return [
        (atm, OPTION_CALL, SOLD),
        (atm, OPTION_PUT, SOLD),
        (atm + width, OPTION_CALL, BOUGHT),
        (atm - width, OPTION_PUT, BOUGHT),
    ]


def short_condor(call: float, put: float, width: float) -> list[tuple[float, str, int]]:
    return [
        (call, OPTION_CALL, SOLD),
        (put, OPTION_PUT, SOLD),
        (call + width, OPTION_CALL, BOUGHT),
        (put - width, OPTION_PUT, BOUGHT),
    ]


def open_trade(
    trade_id: str, structure: str, width: float, spec, expiry: date, cash_flow: float, lots: int = 1
) -> OpenTrade:
    units = {contract(k, kind, expiry): side * lots * LOT for k, kind, side in spec}
    return OpenTrade(trade_id, TradeTerms(structure, width, lots), units, cash_flow)


def book(
    open_trades=(),
    closed=((DAY - timedelta(days=30), START),),
    restarts=(),
    cash=START,
    marked=START,
    name="book1_rules",
    premium_reserved=0.0,
    session_trades=(),
) -> RiskBook:
    """A book with its account state given directly: closed equity is the last value of `closed`."""
    closed_equity = closed[-1][1]
    state = AccountState(
        START, cash, closed_equity, marked - closed_equity, marked, 0.0, premium_reserved, len(open_trades), ()
    )
    return RiskBook(name, state, tuple(open_trades), tuple(closed), tuple(restarts), tuple(session_trades))


FLY = STRUCTURE_SHORT_IRON_FLY
CONDOR = STRUCTURE_SHORT_CONDOR


DECISIONS_HEADER = "# Desk decisions (owner)\n\n| Date | Decision | Detail |\n|---|---|---|\n"


def owner_decision(root, title: str, book: str = "Book 1", day: str = "12 Oct 2026", words: str = "restart it") -> str:
    """Story C5b: writes `docs/DESK_DECISIONS.md` under `root` with one owner row in the standard form; returns the
    restart row's `decision` cell (the title)."""
    path = root / "docs" / "DESK_DECISIONS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DECISIONS_HEADER + f'| {day} | **{title}** (owner: "{words}") | {book} brake restarted |\n')
    return title
