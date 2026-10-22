"""The legs a road is judged on (story 3.5): per expiry, the strikes within a card's band of that expiry's money,
counted in that expiry's own strike steps."""

from ..contracts.snapshot import ContractKey, SlotSnapshot
from .strikes import strike_steps

DEFAULT_BAND_STEPS = 10  # the widest band in the drivers' table (RC1: short strike within 10 steps of the money)


def band_keys(snapshot: SlotSnapshot, band_steps: int = DEFAULT_BAND_STEPS) -> tuple[ContractKey, ...]:
    """Every recorded contract at most `band_steps` of its expiry's steps from that expiry's money (its listed strike
    nearest the spot, the lower one on a tie). An expiry with no step (under two strikes) has no band."""
    steps = strike_steps(snapshot.quotes)
    strikes = {expiry: sorted({k.strike for k in snapshot.quotes if k.expiry == expiry}) for expiry in steps}
    money = {e: min(listed, key=lambda strike: (abs(strike - snapshot.spot), strike)) for e, listed in strikes.items()}

    def in_band(key: ContractKey) -> bool:
        return key.expiry in steps and abs(key.strike - money[key.expiry]) <= band_steps * steps[key.expiry]

    return tuple(sorted(key for key in snapshot.quotes if in_band(key)))
