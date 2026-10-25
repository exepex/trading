"""The held-out indices' lots before UDiFF files (protocol section 7): legacy files carry no lot column, and UDiFF's
board lot covers every file from 2024, so only 2021-2023 expiries use this schedule. FINNIFTY listed with a lot of 40
and MIDCPNIFTY with 75; neither changed before NSE/FAOP/61415 (2 Apr 2024: to 25 and 50 from the July 2024 expiries,
inside the UDiFF years) [some evidence: broker bulletins of the 2024 circulars; the launch circulars were not read in
the build]. NIFTY and BANKNIFTY keep EDGE1's schedule."""

from __future__ import annotations

from datetime import date

from edge1study.lots import circular_lot

LEGACY_LOTS = {"FINNIFTY": 40, "MIDCPNIFTY": 75}
CHANGED_FROM = date(2024, 7, 1)  # the first expiries with the 2024 lots


def held_out_lot(index: str, expiry: date) -> int | None:
    if index in LEGACY_LOTS:
        return LEGACY_LOTS[index] if expiry < CHANGED_FROM else None
    return circular_lot(index, expiry)
