"""Turns a directional view into one concrete option to buy: strike, price, lots, stop and target."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..analytics import bs_greeks
from ..constants import Direction, OptionKind, OrderSide
from ..models import OptionChain, OptionQuote
from ..naming import groww_contract_name, trade_idea_id
from ..strategies import size_position
from .models import MarketView, TradeIdea

PERCENT = 100.0


@dataclass(frozen=True)
class PickerRules:
    target_delta: float = 0.55  # slightly in the money: moves well with the stock, less time decay than OTM
    strikes_each_side: int = 3  # how far from the money to look
    min_premium: float = 20.0  # below this, charges and the bid-ask gap eat the trade
    max_spread_pct: float = 3.0  # bid-ask gap as % of mid
    min_open_interest: float = 200  # contracts
    risk_free_rate: float = 0.065

    @classmethod
    def from_config(cls, cfg: dict) -> PickerRules:
        return cls(**{k: v for k, v in (cfg or {}).items() if k in cls.__dataclass_fields__})


@dataclass(frozen=True)
class ExitLevels:
    stop_loss_pct: float = 30.0
    take_profit_pct: float = 60.0

    @classmethod
    def from_config(cls, long_option_exits: dict) -> ExitLevels:
        return cls(
            long_option_exits.get("stop_loss_pct_of_premium", 30.0),
            long_option_exits.get("take_profit_pct_of_premium", 60.0),
        )


class ContractPicker:
    def __init__(self, rules: PickerRules, exits: ExitLevels, position_rules: dict):
        self.rules = rules
        self.exits = exits
        self.position_rules = position_rules

    def pick(self, view: MarketView, chain: OptionChain, today: date) -> tuple[TradeIdea | None, str]:
        """The best liquid contract for the view, or None with the reason."""
        if view.direction is Direction.NEUTRAL:
            return None, "no clear direction"
        kind = OptionKind.CALL.value if view.direction is Direction.BULLISH else OptionKind.PUT.value
        quote, reason = self._best_quote(chain, kind)
        if quote is None:
            return None, reason
        entry = round(quote.fill_price(OrderSide.BUY.value), 2)
        lots, exception, size_note = size_position(entry * chain.lot_size, view.strong_evidence, self.position_rules)
        if lots == 0:
            return None, size_note
        idea = TradeIdea(
            id=trade_idea_id(chain.underlying, chain.expiry, quote.strike, kind),
            underlying=chain.underlying,
            contract_name=groww_contract_name(chain.underlying, chain.expiry, quote.strike, kind),
            expiry=chain.expiry,
            strike=quote.strike,
            option_kind=kind,
            entry_price=entry,
            lot_size=chain.lot_size,
            lots=lots,
            stop_price=round(entry * (1 - self.exits.stop_loss_pct / PERCENT), 2),
            target_price=round(entry * (1 + self.exits.take_profit_pct / PERCENT), 2),
            spot=chain.spot,
            view=view,
            exception=exception,
            notes=[size_note] if size_note else [],
        )
        return idea, "ok"

    def _best_quote(self, chain: OptionChain, kind: str) -> tuple[OptionQuote | None, str]:
        candidates = self._near_money(chain, kind)
        liquid = [q for q in candidates if self._liquidity_problem(q) is None]
        if not liquid:
            problems = {self._liquidity_problem(q) for q in candidates} - {None}
            return None, "no liquid contract near the money" + (f" ({'; '.join(sorted(problems))})" if problems else "")
        t = chain.years_to_expiry()
        return min(liquid, key=lambda q: abs(abs(self._delta(chain, q, t)) - self.rules.target_delta)), "ok"

    def _near_money(self, chain: OptionChain, kind: str) -> list[OptionQuote]:
        strikes = chain.strikes()
        atm = strikes.index(chain.atm_strike())
        n = self.rules.strikes_each_side
        window = strikes[max(0, atm - n) : atm + n + 1]
        return [q for k in window if (q := chain.get(k, kind)) is not None]

    def _liquidity_problem(self, quote: OptionQuote) -> str | None:
        price = quote.fill_price(OrderSide.BUY.value)
        if price < self.rules.min_premium:
            return f"premium under Rs {self.rules.min_premium:g}"
        if quote.oi < self.rules.min_open_interest:
            return "thin open interest"
        if quote.spread_pct is not None and quote.spread_pct > self.rules.max_spread_pct:
            return "wide bid-ask gap"
        return None

    def _delta(self, chain: OptionChain, quote: OptionQuote, years: float) -> float:
        sigma = (quote.iv or 15.0) / PERCENT
        return bs_greeks(chain.spot, quote.strike, years, self.rules.risk_free_rate, sigma, quote.kind).delta
