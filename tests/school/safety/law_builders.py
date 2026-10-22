"""The MS-P1d laws on fixtures: the repository's charges and C2's books profile, with a fixed stressed margin in
place of C2's margins file (which has NIFTY rows only)."""

from dataclasses import replace
from datetime import date

from fno.config import ROOT, load_config
from fno.risk.margins import StressedMargin
from fno.school.constants import RoadCode
from fno.school.contracts.decisions import LegSpec, OpenPosition
from fno.school.contracts.safety import AccountView
from fno.school.settings import school_settings
from tests.school.contracts import builders as b

CFG = load_config(ROOT / "config.yaml")
SETTINGS = school_settings(CFG)


class FixedMargin(StressedMargin):
    """Per lot: Rs 5,000 stressed, Rs 6,000 at entry, Rs 4,000 a broker blocks."""

    method = "fixed"

    def margin(self, terms, day: date) -> float:
        return 5_000.0 * terms.lots

    def margin_at_entry(self, terms, day: date) -> float:
        return 6_000.0 * terms.lots

    def broker_margin(self, terms, day: date) -> float:
        return 4_000.0 * terms.lots

    def record(self, day: date | None = None) -> dict[str, str]:
        return {"method": self.method}


def view(**changes) -> AccountView:
    return replace(b.account(), **changes)


def held(position_id: str, strikes=(1000.0, 900.0), road=RoadCode.BANKNIFTY_MONTHLY, opened=b.SESSION) -> OpenPosition:
    short, long = strikes
    legs = (LegSpec(b.key(short), "sell", 1), LegSpec(b.key(long), "buy", 1))
    return replace(b.position(position_id), legs=legs, road=road, opened=opened)
