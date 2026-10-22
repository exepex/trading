"""A card's exit rule (story MS-P1e, story 3.2's exit column). One data class holds every kind of exit a card can
name; a card writes only the ones it uses. Price rules judge the position at the mid of every leg at the slot and
never fire without a two-sided quote on every leg; time rules need no price. The close itself fills at the touch
(MS-P1f/g), so the mid here only decides whether the rule is reached."""

from dataclasses import dataclass
from datetime import date

from ...constants import SIDE_BUY
from ..constants import ExitReason
from ..contracts.decisions import OpenPosition, SpotPoint
from ..contracts.snapshot import SlotSnapshot
from .card_params import CardParams
from .history import spot_window
from .session_days import TradingCalendar, next_session, sessions_between
from .shapes import CDS, PDS

PROFIT_TARGET, LOSS_MULTIPLE = "exit_profit_share", "exit_loss_multiple"
MAX_SESSIONS, MAX_DAYS = "exit_sessions_held", "exit_days_held"
LAST_SESSION_DTE, SPOT_MEAN_WINDOW = "exit_last_session_dte", "exit_spot_mean_window"
EXIT_KEYS = (PROFIT_TARGET, LOSS_MULTIPLE, MAX_SESSIONS, MAX_DAYS, LAST_SESSION_DTE, SPOT_MEAN_WINDOW)


@dataclass(frozen=True)
class ExitRule:
    profit_share: float | None = None  # close when the open profit reaches this share of the entry credit or debit
    loss_multiple: float | None = None  # close when the open loss reaches this multiple of it
    sessions_held: int | None = None
    days_held: int | None = None  # calendar days
    last_session_dte: int | None = (
        None  # close on the last session with at least this many days to expiry (EDGE1's T21)
    )
    spot_mean_window: int | None = None  # a directional position closes when spot is back through this window's mean

    @classmethod
    def from_params(cls, params: CardParams) -> "ExitRule":
        return cls(params.number_or_none(PROFIT_TARGET), params.number_or_none(LOSS_MULTIPLE),
                   params.whole_or_none(MAX_SESSIONS), params.whole_or_none(MAX_DAYS),
                   params.whole_or_none(LAST_SESSION_DTE), params.whole_or_none(SPOT_MEAN_WINDOW))  # fmt: skip

    def review(self, position: OpenPosition, snapshot: SlotSnapshot, history: tuple[SpotPoint, ...],
               calendar: TradingCalendar) -> ExitReason | None:  # fmt: skip
        session, expiry = snapshot.session, min(leg.key.expiry for leg in position.legs)
        if session >= expiry:
            return ExitReason.EXPIRY  # every position ends here; a rule that waits for expiry has no other exit
        return (
            self._price_exit(position, snapshot)
            or self._spot_exit(position, snapshot, history)
            or self._time_exit(position, session, expiry, calendar)
        )

    def _price_exit(self, position: OpenPosition, snapshot: SlotSnapshot) -> ExitReason | None:
        basis = abs(position.entry_net)
        profit = open_profit(position, snapshot)
        if profit is None or basis == 0:
            return None
        if self.profit_share is not None and profit >= self.profit_share * basis:
            return ExitReason.PROFIT_TARGET
        if self.loss_multiple is not None and -profit >= self.loss_multiple * basis:
            return ExitReason.LOSS_LIMIT
        return None

    def _spot_exit(self, position: OpenPosition, snapshot: SlotSnapshot,
                   history: tuple[SpotPoint, ...]) -> ExitReason | None:  # fmt: skip
        if self.spot_mean_window is None or position.structure not in (CDS, PDS):
            return None
        window = spot_window(history, snapshot.session, self.spot_mean_window)
        if window is None:
            return None
        through = snapshot.spot < window.mean if position.structure == CDS else snapshot.spot > window.mean
        return ExitReason.SPOT_THROUGH_MEAN if through else None

    def _time_exit(self, position: OpenPosition, session: date, expiry: date,
                   calendar: TradingCalendar) -> ExitReason | None:  # fmt: skip
        if (
            self.sessions_held is not None
            and sessions_between(calendar, position.opened, session) >= self.sessions_held
        ):
            return ExitReason.SESSIONS_HELD
        if self.days_held is not None and (session - position.opened).days >= self.days_held:
            return ExitReason.DAYS_HELD
        if (
            self.last_session_dte is not None
            and (expiry - next_session(calendar, session)).days < self.last_session_dte
        ):
            return ExitReason.DAYS_BEFORE_EXPIRY
        return None


def open_profit(position: OpenPosition, snapshot: SlotSnapshot) -> float | None:
    """Rupees the position would show closed at the mids of the slot, entry charges counted; None when any leg has no
    two-sided quote (a price that cannot be judged never fires a rule)."""
    value = 0.0
    for leg in position.legs:
        quote = snapshot.quote(leg.key)
        if quote is None or not quote.two_sided:
            return None
        value += (quote.mid if leg.side == SIDE_BUY else -quote.mid) * leg.lots
    return position.entry_net + value * position.lot
