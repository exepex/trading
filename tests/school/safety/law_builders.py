"""The MS-P1d laws on fixtures: the repository's charges and C2's books profile, with fixed stressed margins in place
of MS-P1m's margin per trade (which reads Drive's archived SPAN files)."""

from dataclasses import replace
from datetime import date

from fno.config import ROOT, load_config
from fno.risk.inputs import RiskInputError
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


class NoMargin(FixedMargin):
    """MS-P1m's margin when the session's SPAN file is not archived: every read refuses by name."""

    def margin(self, terms, day: date) -> float:
        raise RiskInputError("school margin: no beginning-of-day SPAN file archived for the session")

    margin_at_entry = broker_margin = margin


class MarginByIndex(FixedMargin):
    """Rs 5,000 a lot on NIFTY, Rs 9,000 on BANKNIFTY (stressed; at entry +1,000; broker -1,000), read from the
    trade's own terms, as MS-P1m's margin is: equal C2 terms on two indices get different margins."""

    PER_LOT = {"NIFTY": 5_000.0, "BANKNIFTY": 9_000.0}

    def margin(self, terms, day: date) -> float:
        return self.PER_LOT[terms.underlying] * terms.lots

    def margin_at_entry(self, terms, day: date) -> float:
        return (self.PER_LOT[terms.underlying] + 1_000.0) * terms.lots

    def broker_margin(self, terms, day: date) -> float:
        return (self.PER_LOT[terms.underlying] - 1_000.0) * terms.lots
