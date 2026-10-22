"""The legs a road is judged on (story 3.5): strikes within a card's band of the money, on every expiry it uses."""

from ..contracts.snapshot import ContractKey, SlotSnapshot

DEFAULT_BAND_STEPS = 10  # the widest band in the drivers' table (RC1: short strike within 10 steps of the money)


def band_keys(
    snapshot: SlotSnapshot, strike_step: float, band_steps: int = DEFAULT_BAND_STEPS
) -> tuple[ContractKey, ...]:
    """Every recorded contract whose strike is at most `band_steps` steps from the money, the strike of the nearest
    expiry nearest to the spot (the lower one on a tie)."""
    nearest = snapshot.expiries[0]
    strikes = {key.strike for key in snapshot.quotes if key.expiry == nearest}
    money = min(strikes, key=lambda strike: (abs(strike - snapshot.spot), strike))
    reach = band_steps * strike_step
    return tuple(sorted(key for key in snapshot.quotes if abs(key.strike - money) <= reach))
