"""PROPOSAL, data to confirm: the contracts section. For the nearest expiry, five strikes around today's price,
the chance that a call or a put finishes in the money, read off the forecast range, and today's check of the call
made the session before. The mock fits a normal curve to the forecast quantiles; production reads G13's per-strike
implied probabilities instead (the FL1 and G13 builders confirm). Standard library only."""

import math

STRIKE_STEP = {"NIFTY": 100, "BANKNIFTY": 100}
SESSIONS_TO_EXPIRY = 6  # mock: a weekly expiry about six sessions away; the real date comes from the F&O masters


def _sigma(f, sessions):
    """Spread of the forecast from its 50% range (q25-q75 spans 1.349 standard deviations), scaled to the expiry."""
    return (f["hi50"] - f["lo50"]) / 1.349 * math.sqrt(sessions / 3)


def _p_above(level, mid, sigma):
    return 0.5 * (1 - math.erf((level - mid) / (sigma * math.sqrt(2))))


def strikes(price, step):
    centre = round(price / step) * step
    return [centre + k * step for k in (-2, -1, 0, 1, 2)]


def contract_rows(idx):
    """Rows of (strike, call chance, put chance, call check, put check) for one index."""
    f3 = idx["three"]
    sigma = _sigma(f3, SESSIONS_TO_EXPIRY)
    today = idx["days"][-1]
    sigma_today = (today["hi50"] - today["lo50"]) / 1.349
    rows = []
    for k in strikes(idx["today"], STRIKE_STEP[idx["name"]]):
        p_call = _p_above(k, f3["mid"], sigma)
        implied_call = _p_above(k, today["mid"], sigma_today) >= 0.5
        call_itm = today["close"] > k
        rows.append(dict(strike=k, call=p_call, put=1 - p_call,
                         call_check=implied_call == call_itm, put_check=(not implied_call) == (not call_itm)))
    return rows
