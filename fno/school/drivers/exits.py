"""A card's exit plan (story MS-P1e, story 3.2's exit column). The exits themselves are E4's `ExitRule` classes
(`fno/desk/exit_rules.py`): `ProfitTarget`, `StopLoss` and `ExitOnDay`, built per position from the card's numbers and
asked through their `reached` interface; no exit logic is rewritten here. They ignore the position they are given, so
the school position is passed as is. Price rules judge the net if every leg closed now at the touch (E4's value,
without exit charges, which the school fill adds); with no two-sided quote on a leg the value is None and they never
fire. The one rule E4 lacks, DR1's "spot back through the window mean", is a small predicate here."""

from dataclasses import dataclass
from datetime import timedelta

from ...constants import SIDE_BUY
from ...desk.exit_rules import ExitContext, ExitOnDay, ExitRule, ProfitTarget, StopLoss
from ..constants import ExitReason
from ..contracts.decisions import OpenPosition, SpotPoint
from ..contracts.snapshot import SlotSnapshot
from .card_params import CardParams
from .history import spot_window
from .session_days import TradingCalendar, last_session_on_or_before, nth_session_after
from .shapes import CDS, PDS

PROFIT_TARGET, LOSS_MULTIPLE = "exit_profit_share", "exit_loss_multiple"
MAX_SESSIONS, MAX_DAYS = "exit_sessions_held", "exit_days_held"
LAST_SESSION_DTE, SPOT_MEAN_WINDOW = "exit_last_session_dte", "exit_spot_mean_window"
EXIT_KEYS = (PROFIT_TARGET, LOSS_MULTIPLE, MAX_SESSIONS, MAX_DAYS, LAST_SESSION_DTE, SPOT_MEAN_WINDOW)


@dataclass(frozen=True)
class ExitPlan:
    profit_share: float | None = None  # close when the net if closed reaches this share of the entry credit or debit
    loss_multiple: float | None = None  # close when the net loss reaches this multiple of it
    sessions_held: int | None = None
    days_held: int | None = None  # calendar days
    last_session_dte: int | None = None  # close on the last session with this many days to expiry (EDGE1's T21)
    spot_mean_window: int | None = None  # a directional position closes when spot is back through its mean

    @classmethod
    def from_params(cls, params: CardParams) -> "ExitPlan":
        return cls(params.number_or_none(PROFIT_TARGET), params.number_or_none(LOSS_MULTIPLE),
                   params.whole_or_none(MAX_SESSIONS), params.whole_or_none(MAX_DAYS),
                   params.whole_or_none(LAST_SESSION_DTE), params.whole_or_none(SPOT_MEAN_WINDOW))  # fmt: skip

    def review(self, position: OpenPosition, snapshot: SlotSnapshot, history: tuple[SpotPoint, ...],
               calendar: TradingCalendar) -> ExitReason | None:  # fmt: skip
        context = ExitContext(snapshot.session, net_if_closed(position, snapshot))
        for rule, reason in self._rules(position, history, snapshot, calendar):
            if rule.reached(position, context):
                return reason
        return None

    def _rules(self, position, history, snapshot, calendar) -> list[tuple[ExitRule, ExitReason]]:
        expiry, basis = min(leg.key.expiry for leg in position.legs), abs(position.entry_net)
        rules: list[tuple[ExitRule, ExitReason]] = [(ExitOnDay(expiry, "expiry"), ExitReason.EXPIRY)]
        if basis > 0 and self.profit_share is not None:
            rules.append((ProfitTarget(self.profit_share * basis), ExitReason.PROFIT_TARGET))
        if basis > 0 and self.loss_multiple is not None:
            rules.append((StopLoss(self.loss_multiple * basis), ExitReason.LOSS_LIMIT))
        if self._through_mean(position, snapshot, history):
            rules.append((ExitOnDay(snapshot.session, "spot back through its mean"), ExitReason.SPOT_THROUGH_MEAN))
        opened = position.opened
        if self.sessions_held is not None:
            day = nth_session_after(calendar, opened, self.sessions_held)
            rules.append((ExitOnDay(day, f"{self.sessions_held} sessions held"), ExitReason.SESSIONS_HELD))
        if self.days_held is not None:
            day = opened + timedelta(days=self.days_held)
            rules.append((ExitOnDay(day, f"{self.days_held} days held"), ExitReason.DAYS_HELD))
        if self.last_session_dte is not None:
            day = last_session_on_or_before(calendar, expiry - timedelta(days=self.last_session_dte))
            rules.append((ExitOnDay(day, f"last session {self.last_session_dte} days before expiry"),
                          ExitReason.DAYS_BEFORE_EXPIRY))  # fmt: skip
        return rules

    def _through_mean(self, position: OpenPosition, snapshot: SlotSnapshot, history: tuple[SpotPoint, ...]) -> bool:
        if self.spot_mean_window is None or position.structure not in (CDS, PDS):
            return False
        window = spot_window(history, snapshot.session, self.spot_mean_window)
        if window is None:
            return False  # the mean cannot be judged
        return snapshot.spot < window.mean if position.structure == CDS else snapshot.spot > window.mean


def net_if_closed(position: OpenPosition, snapshot: SlotSnapshot) -> float | None:
    """Rupees the position would net if every leg closed now at the touch (bid for bought legs, ask for sold ones),
    entry charges counted; None when any leg has no two-sided quote."""
    cash = 0.0
    for leg in position.legs:
        quote = snapshot.quote(leg.key)
        if quote is None or not quote.two_sided:
            return None
        cash += (quote.bid if leg.side == SIDE_BUY else -quote.ask) * leg.lots
    return position.entry_net + cash * position.lot
