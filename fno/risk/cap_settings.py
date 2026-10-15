"""The paper account and its account-level caps (story C5, design 6.2): `config.yaml` `risk.paper_account_rs`,
`risk.caps` and `risk.stress_line`, read once and checked, never hard-coded.

Owner's numbers (`docs/DESK_DECISIONS.md`): Rs 20 lakh paper account (14 Oct 2026); Rs 30,000 a risk bucket, Rs 1.5
lakh of open maximum loss, Rs 50,000 of new maximum loss a session (15 Oct 2026). A missing or malformed value is an
error at start-up, so no proposal is ever checked against a default the owner did not set.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..constants import BUCKET_SIDES
from .settings import RiskSettingsError, Scenario, get_setting, positive_setting, scenarios_at

CAPS = ".caps"


@dataclass(frozen=True)
class CapSettings:
    paper_account_rs: float  # every book and shadow account opens with this cash (E1)
    bucket_cap_rs: float  # open maximum loss of one bucket, the proposal included
    open_risk_cap_rs: float  # open maximum loss of the whole book, the proposal included (a cap on entries, not a stop)
    new_risk_per_day_rs: float  # maximum loss of the trades opened in one session, the proposal included
    bucket_sides: Mapping[str, str]  # structure code -> side of exposure; a code not listed is unmapped (refused)
    stress_line: tuple[Scenario, ...]  # the daily stress line's scenarios (reported, not a limit)


def _sides(caps: Mapping[str, Any]) -> dict[str, str]:
    sides = get_setting(caps, "bucket_sides", CAPS)
    if not isinstance(sides, Mapping) or not sides:
        raise RiskSettingsError("config.yaml risk.caps: `bucket_sides` must map structure codes to sides")
    wrong = {code: side for code, side in sides.items() if side not in BUCKET_SIDES}
    if wrong:
        raise RiskSettingsError(f"config.yaml risk.caps.bucket_sides: sides must be one of {BUCKET_SIDES}: {wrong}")
    return {str(code): str(side) for code, side in sides.items()}


def cap_settings(config: Mapping[str, Any]) -> CapSettings:
    """The checked C5 settings of an app config (`fno.config.load_app_config`)."""
    block = get_setting(config, "risk", "")
    caps = get_setting(block, "caps", "")
    settings = CapSettings(
        positive_setting(block, "paper_account_rs"),
        positive_setting(caps, "bucket_cap_rs", CAPS),
        positive_setting(caps, "open_risk_cap_rs", CAPS),
        positive_setting(caps, "new_risk_per_day_rs", CAPS),
        _sides(caps),
        scenarios_at(block, "stress_line"),
    )
    capped = (settings.bucket_cap_rs, settings.open_risk_cap_rs, settings.new_risk_per_day_rs)
    if max(capped) > settings.paper_account_rs:
        raise RiskSettingsError("config.yaml risk.caps: a cap is larger than the paper account itself")
    return settings
