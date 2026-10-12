"""Turns a directional view into one concrete option to buy: strike, price, lots, stop and target."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..analytics import Greeks, bs_greeks
from ..constants import INDEX_UNDERLYINGS, Direction, OptionKind, OrderSide
from ..journal import fill_source
from ..models import OptionChain, OptionQuote
from ..naming import groww_contract_name, trade_idea_id
from ..providers import Provider
from ..strategies import size_position
from .models import MarketView, TradeIdea
from .move_check import MoveCheck

PERCENT = 100.0


@dataclass(frozen=True)
class PickerRules:
    target_delta: float = 0.55  # slightly in the money: moves well with the stock, less time decay than OTM
    strikes_each_side: int = 6  # how far from the money to look (the delta and risk filters bound it)
    min_premium: float = 20.0  # below this, charges and the bid-ask gap eat the trade
    max_spread_pct: float = 2.0  # bid-ask gap as % of mid, index options
    max_spread_pct_stock: float = 5.0  # stock options are less liquid
    min_abs_delta: float = 0.30  # nothing further out of the money than this
    max_daily_theta_pct: float = 12.0  # time decay per day as % of premium
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
    def __init__(
        self,
        rules: PickerRules,
        exits: ExitLevels,
        position_rules: dict,
        max_planned_loss: float,
        live_quotes: Provider | None = None,
        move_check: MoveCheck | None = None,
    ):
        self.rules = rules
        self.exits = exits
        self.position_rules = position_rules
        self.max_planned_loss = max_planned_loss  # rupees lost if the stop is hit (2% of capital)
        self.live_quotes = live_quotes  # real bid/ask for the chosen contract when the chain has none
        self.move_check = move_check  # refuses contracts whose target needs an unlikely move

    def pick(self, view: MarketView, chain: OptionChain, today: date) -> tuple[TradeIdea | None, str]:
        """The best liquid contract for the view, or None with the reason."""
        if view.direction is Direction.NEUTRAL:
            return None, "no clear direction"
        kind = OptionKind.CALL.value if view.direction is Direction.BULLISH else OptionKind.PUT.value
        quote, reason = self._best_quote(chain, kind)
        if quote is None:
            return None, reason
        quote, reason = self._confirm_with_live_quote(chain, quote)
        if quote is None:
            return None, reason
        entry = round(quote.fill_price(OrderSide.BUY.value), 2)
        lots, exception, size_note = size_position(entry * chain.lot_size, view.strong_evidence, self.position_rules)
        if lots == 0:
            return None, size_note
        loss_per_lot = entry * self.exits.stop_loss_pct / PERCENT * chain.lot_size
        lots = min(lots, int(self.max_planned_loss // loss_per_lot))
        if lots == 0:
            return None, (
                f"1 lot would lose Rs {loss_per_lot:,.0f} at the stop, "
                f"above the Rs {self.max_planned_loss:,.0f} risk limit per trade"
            )
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
            notes=[n for n in (size_note, self._move_note(chain, quote, entry)) if n],
            fill_source=fill_source(quote),
        )
        return idea, "ok"

    def _move_note(self, chain: OptionChain, quote: OptionQuote, entry: float) -> str | None:
        if self.move_check is None:
            return None
        return self.move_check.detail(chain, entry, self._greeks(chain, quote, chain.years_to_expiry()))

    def _confirm_with_live_quote(self, chain: OptionChain, quote: OptionQuote) -> tuple[OptionQuote | None, str]:
        """A chain without bid/ask (Groww) is checked again against the contract's live bid/ask before buying."""
        if quote.has_book or self.live_quotes is None:
            return quote, "ok"
        live = self.live_quotes.live_quote(chain, quote.strike, quote.kind)
        if live is None or not live.has_book:
            return quote, "ok"  # priced at last price + slippage, and recorded as such
        problem = self._contract_problem(chain, live, self._greeks(chain, live, chain.years_to_expiry()))
        return (None, f"live quote: {problem}") if problem else (live, "ok")

    def _best_quote(self, chain: OptionChain, kind: str) -> tuple[OptionQuote | None, str]:
        years = chain.years_to_expiry()
        problems, usable = set(), []
        for quote in self._near_money(chain, kind):
            greeks = self._greeks(chain, quote, years)
            problem = self._contract_problem(chain, quote, greeks)
            if problem:
                problems.add(problem)
            else:
                usable.append((quote, greeks))
        if not usable:
            detail = f" ({'; '.join(sorted(problems))})" if problems else ""
            return None, "no suitable contract near the money" + detail
        best = min(usable, key=lambda pair: abs(abs(pair[1].delta) - self.rules.target_delta))
        return best[0], "ok"

    def _near_money(self, chain: OptionChain, kind: str) -> list[OptionQuote]:
        strikes = chain.strikes()
        atm = strikes.index(chain.atm_strike())
        n = self.rules.strikes_each_side
        window = strikes[max(0, atm - n) : atm + n + 1]
        return [q for k in window if (q := chain.get(k, kind)) is not None]

    def _contract_problem(self, chain: OptionChain, quote: OptionQuote, greeks: Greeks) -> str | None:
        """Why this contract is a poor buy for a retail trader, or None."""
        rules = self.rules
        price = quote.fill_price(OrderSide.BUY.value)
        if price * self.exits.stop_loss_pct / PERCENT * chain.lot_size > self.max_planned_loss:
            return f"1 lot would lose more than Rs {self.max_planned_loss:,.0f} at the stop"
        max_spread = rules.max_spread_pct if chain.underlying in INDEX_UNDERLYINGS else rules.max_spread_pct_stock
        if price < rules.min_premium:
            return f"premium under Rs {rules.min_premium:g}"
        if quote.oi < rules.min_open_interest:
            return "thin open interest"
        if quote.spread_pct is not None and quote.spread_pct > max_spread:
            return "wide bid-ask gap"
        if abs(greeks.delta) < rules.min_abs_delta:
            return "too far out of the money"
        if -greeks.theta / price * PERCENT > rules.max_daily_theta_pct:
            return "time decay too fast"
        if self.move_check is not None:
            return self.move_check.problem(chain, price, greeks)
        return None

    def _greeks(self, chain: OptionChain, quote: OptionQuote, years: float) -> Greeks:
        sigma = (quote.iv or 15.0) / PERCENT
        return bs_greeks(chain.spot, quote.strike, years, self.rules.risk_free_rate, sigma, quote.kind)
