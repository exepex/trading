"""Composition root of `fno/school/safety/` (story MS-P1d): the safety laws of story 3.3 for one slot, in a fixed
order, with the school's own limits (`school` block) and C2's rule classes, cost model and stressed margin (the books
profile's buckets sides and margin age; C2's margins file). Built per slot: C2's caps mark positions held on other
roads at their own road's snapshot of the same slot. Margin room runs only where C2's margins file has rows
(`margin_law.py`)."""

from collections.abc import Mapping
from pathlib import Path

from ...config import ROOT
from ...constants import NIFTY_SYMBOL, RISK_PROFILE_BOOKS
from ...risk.caps import BucketCap, NewRiskPerDay, OpenRiskCap
from ...risk.open_risk import HeldMaxLoss, PositionRisks
from ...risk.profile_settings import profile_settings
from ...risk.rules import MarginRoom, MaxLossPerTrade
from ...risk.settings import risk_settings
from ...risk.trade_costs import SimulatorTradeCosts
from ...risk.wiring import build_margin_age, build_stressed_margin
from ..constants import RefusalReason, RoadCode
from ..contracts.snapshot import SlotSnapshot
from ..settings import SchoolSettings
from .account_laws import BrakeLaw, DailyStopLaw, ProtectedLaw
from .buckets import SchoolBuckets
from .c2_laws import C2Law, MaxLossLaw, cap_numbers, margin_numbers
from .law_set import SafetyLaws
from .margin_law import MarginRoomLaw, MarginRows
from .quote_laws import GATE_REASONS, ImpossiblePriceLaw, QuoteGateLaw


def build_safety_laws(cfg: dict, settings: SchoolSettings, slot: Mapping[RoadCode, SlotSnapshot],
                      root: Path = ROOT) -> SafetyLaws:  # fmt: skip
    books = profile_settings(cfg, RISK_PROFILE_BOOKS)
    costs = SimulatorTradeCosts(cfg["charges"])
    risks = PositionRisks(SchoolBuckets(books.bucket_sides), HeldMaxLoss(cfg["charges"]), costs)
    settings_risk = risk_settings(cfg, root)
    stressed = build_stressed_margin(settings_risk, build_margin_age(books), cfg["lot_sizes"][NIFTY_SYMBOL])
    return SafetyLaws((
        ProtectedLaw(),
        MaxLossLaw(settings.max_loss_rs, cfg["charges"], MaxLossPerTrade(costs, settings.max_loss_rs)),
        C2Law("bucket_cap", BucketCap(risks, settings.bucket_rs), RefusalReason.BUCKET_CAP, cap_numbers, slot),
        C2Law("open_risk", OpenRiskCap(risks, settings.open_risk_rs), RefusalReason.OPEN_RISK, cap_numbers, slot),
        C2Law("new_risk_day", NewRiskPerDay(risks, settings.new_risk_day_rs), RefusalReason.NEW_RISK_DAY, cap_numbers,
              slot),
        MarginRoomLaw(C2Law(MarginRoomLaw.name, MarginRoom(stressed, costs), RefusalReason.MARGIN_ROOM, margin_numbers,
                            slot), MarginRows(settings_risk.margins_file)),
        DailyStopLaw(settings.daily_stop_rs),
        *(QuoteGateLaw(reason) for reason in GATE_REASONS),
        ImpossiblePriceLaw(),
        BrakeLaw(settings.brake_rs),
    ))  # fmt: skip
