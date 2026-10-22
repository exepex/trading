"""The school's fixed names (story MS-P1a): roads, outcome and reason codes, report labels and the settings keys.
Frozen here so the parallel parts b-j share one vocabulary; a new code is a small follow-up of MS-P1a, never a copy."""

from datetime import time
from enum import StrEnum

RECORD_SCHEMA_VERSION = 1  # every decision and outcome record carries it; a layout change is a new version
SLOT_1500 = "15:00"  # the pilot's only slot: each road's canonical 3 pm capture of the session
SLOT_TIME = time(15, 0)
MAX_ROADS_PER_SESSION = 5


class RoadCode(StrEnum):
    NIFTY_MONTHLY = "NIFTY-M"
    BANKNIFTY_MONTHLY = "BANKNIFTY-M"
    FINNIFTY_MONTHLY = "FINNIFTY-M"
    MIDCPNIFTY_MONTHLY = "MIDCPNIFTY-M"
    NIFTY_WEEKLY = "NIFTY-W"


class ExpiryKind(StrEnum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"


class OptionKind(StrEnum):
    CALL = "CE"
    PUT = "PE"


class Outcome(StrEnum):
    """Every scheduled road decision ends in exactly one of these (story 3.5); all stay in every denominator."""

    TRADE = "trade"
    TICKET = "ticket"
    NO_TRADE = "no_trade"
    REFUSED = "refused"
    ROAD_CLOSED = "road_closed"
    UNAVAILABLE = "unavailable"


class ClosureReason(StrEnum):
    CAPTURE_MISSING = "capture_missing"
    CAPTURE_INCOMPLETE = "capture_incomplete"
    OUT_OF_WINDOW = "out_of_window"
    HASH_MISMATCH = "hash_mismatch"
    EXPIRY_MISMATCH = "expiry_mismatch"
    LOT_MISMATCH = "lot_mismatch"
    IMPOSSIBLE_PRICE = "impossible_price"


class NoTradeReason(StrEnum):
    N0 = "n0"
    NOT_ENOUGH_HISTORY = "not_enough_history"
    NO_EXPIRY_IN_WINDOW = "no_expiry_in_window"
    NO_STRUCTURE_UNDER_CAP = "no_structure_under_cap"
    RULE_NOT_FIRED = "rule_not_fired"
    POSITION_OPEN = "position_open"


class TicketReason(StrEnum):
    TRADE_LIMIT = "trade_limit"  # fired beyond the slot's max new trades
    DRIVER_STOPPED = "driver_stopped"  # fired while the daily stop or the brake holds the account


class RefusalReason(StrEnum):
    UNPROTECTED = "unprotected"
    MAX_LOSS = "max_loss"
    BUCKET_CAP = "bucket_cap"
    OPEN_RISK = "open_risk"
    NEW_RISK_DAY = "new_risk_day"
    MARGIN_ROOM = "margin_room"
    DAILY_STOP = "daily_stop"
    BRAKE = "brake"
    MISSING_QUOTE = "missing_quote"
    ONE_SIDED_QUOTE = "one_sided_quote"
    SIZE_ABOVE_DISPLAYED = "size_above_displayed"
    PROTECTION_UNSELLABLE = "protection_unsellable"
    IMPOSSIBLE_LEG_PRICE = "impossible_leg_price"
    STALE_SEAL = "stale_seal"


class UnavailableReason(StrEnum):
    DRIVER_ERROR = "driver_error"
    DEADLINE = "deadline"
    SEAL_FAILED = "seal_failed"


class ExitState(StrEnum):
    """An open position's state after the slot's exit review, when it did not close."""

    EXIT_WAITING_QUOTE = "exit_waiting_quote"
    SETTLEMENT_NEEDED = "settlement_needed"


class ExitReason(StrEnum):
    """Why a driver's card closes a position (story 3.2's exit column)."""

    PROFIT_TARGET = "profit_target"
    LOSS_LIMIT = "loss_limit"
    SESSIONS_HELD = "sessions_held"
    DAYS_HELD = "days_held"
    DAYS_BEFORE_EXPIRY = "days_before_expiry"
    SPOT_THROUGH_MEAN = "spot_through_mean"
    EXPIRY = "expiry"  # held to expiry: settled at intrinsic (E7)


class RecordKind(StrEnum):
    """The dashcam's files per session and slot: decisions are sealed before any fill; outcomes and drift rows after."""

    DECISIONS = "decisions"
    OUTCOMES = "outcomes"
    DRIFT = "drift"


class DriverRole(StrEnum):
    RULE = "rule"
    CONTROL = "control"  # N0, RC1, REF: matched controls
    MEASUREMENT_ONLY = "measurement_only"  # PS5, KL1: never ranked, recommended or shown as candidates


REASONS_BY_OUTCOME = {
    Outcome.TRADE: frozenset({""}),
    Outcome.TICKET: frozenset(TicketReason),
    Outcome.NO_TRADE: frozenset(NoTradeReason),
    Outcome.REFUSED: frozenset(RefusalReason),
    Outcome.ROAD_CLOSED: frozenset(ClosureReason),
    Outcome.UNAVAILABLE: frozenset(UnavailableReason),
}

# Report labels (story 3.6): every school report carries the first three.
PAPER_LABEL = "Paper"
NO_LATENCY_LABEL = "no latency [reasoning only]: fills at the quotes the driver saw"
NSE_TERMS_LINE = "Open question: NSE's terms on 'virtual trading or simulation' (settlement uses NSE's archived file)"
FLEET_TOTAL_LABEL = "separate hypothetical accounts, not one budget"
SCHOOL_OFF_LINE = "school off"

# The `school` block of config.yaml (fno/school/settings.py reads exactly these keys).
SETTINGS_KEY = "school"
