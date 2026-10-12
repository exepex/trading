"""How contracts are named, so every report and alert uses the exact text Groww search shows."""

from __future__ import annotations

from datetime import date

from .constants import OPTION_DISPLAY_NAME


def groww_contract_name(underlying: str, expiry: date, strike: float, kind: str) -> str:
    """'NIFTY 19 Oct 22500 Put': type this into Groww search to find the contract."""
    return f"{underlying} {expiry.day} {expiry:%b} {strike:g} {OPTION_DISPLAY_NAME[kind]}"


def trade_idea_id(underlying: str, expiry: date, strike: float, kind: str) -> str:
    return f"{underlying}-{expiry:%d%b}-{strike:g}{kind}"
