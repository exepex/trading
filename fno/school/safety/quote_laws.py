"""Law 5, the quote gate (story 3.3), as one law per reason so every reason is kept: a leg with no quote, a leg
without a valid two-sided A4 quote, an opening side whose displayed size does not cover the units (with the units this
account already took at this snapshot, E4d), and a protective leg that cannot be sold back there (E4c). The one gate
(`execution/entry_gate.py`, on E4's `price_leg` and E4c/E4d's `entry_problems`) judges all four; the fill port uses
the same gate, so a proposal these laws pass is one the fill can take.

Beside it, EDGE1's impossible-price rule: at the touch the fill would take, the position must be worth strictly more
than its worst payoff at expiry and strictly less than its best; anything else promises a trade that cannot lose or
cannot win, which only bad quotes do. It is judged once every leg has a touch; until then the gate refuses."""

from datetime import date

from ...research_engine.structures import BOUGHT, SOLD, Leg, payoff_bounds, position_value
from ..constants import SIDE_BUY, RefusalReason
from ..contracts.decisions import Proposal
from ..contracts.roads import ROADS_BY_CODE
from ..contracts.safety import AccountView, LawResult
from ..contracts.snapshot import SlotSnapshot
from ..execution.desk_view import execution_snapshot, school_legs
from ..execution.entry_gate import entry_refusals, taken_at_snapshot

GATE_REASONS = (
    RefusalReason.MISSING_QUOTE,
    RefusalReason.ONE_SIDED_QUOTE,
    RefusalReason.SIZE_ABOVE_DISPLAYED,
    RefusalReason.PROTECTION_UNSELLABLE,
)


def gate_refusals(proposal: Proposal, account: AccountView, snapshot: SlotSnapshot) -> tuple[RefusalReason, ...]:
    underlying = ROADS_BY_CODE[snapshot.road].underlying
    here = [p for p in account.opened_this_session if p.road == snapshot.road and p.opened == snapshot.session]
    legs = school_legs(underlying, proposal.legs, proposal.lot)
    return entry_refusals(execution_snapshot(snapshot, underlying), legs, taken_at_snapshot(underlying, here))


class QuoteGateLaw:
    def __init__(self, reason: RefusalReason):
        if reason not in GATE_REASONS:
            raise ValueError(f"{reason} is not a quote-gate reason")
        self.reason, self.name = reason, f"quote_gate:{reason}"

    def check(self, proposal: Proposal, account: AccountView, snapshot: SlotSnapshot, session: date) -> LawResult:
        passed = self.reason not in gate_refusals(proposal, account, snapshot)
        return LawResult(self.name, passed, None if passed else self.reason)


class ImpossiblePriceLaw:
    name = "impossible_price"

    def check(self, proposal: Proposal, account: AccountView, snapshot: SlotSnapshot, session: date) -> LawResult:
        legs, prices = [], []
        for leg in proposal.legs:
            quote = snapshot.quote(leg.key)
            if quote is None or not quote.two_sided:
                return LawResult(self.name, True, None)  # not judged: the quote gate refuses this entry
            bought = leg.side == SIDE_BUY
            for _ in range(leg.lots):
                legs.append(Leg(leg.key.strike, str(leg.key.kind), BOUGHT if bought else SOLD))
                prices.append(quote.ask if bought else quote.bid)
        lowest, highest = payoff_bounds(legs)
        value = position_value(legs, prices)
        passed = lowest < value < highest
        return LawResult(self.name, passed, None if passed else RefusalReason.IMPOSSIBLE_LEG_PRICE, None, value)
