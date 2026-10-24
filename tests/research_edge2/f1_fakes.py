"""Synthetic weekly chains for the F1 tests: no file, no Drive."""

from datetime import date

from edge1study.day_files import DayRows

from fno.research_data.panel_reader import OptionQuote

ENTRY, EXPIRY = date(2024, 3, 1), date(2024, 3, 7)


def quote(strike, kind, close, volume=10, expiry=EXPIRY):
    return OptionQuote(expiry, float(strike), kind, close, close, volume, 100)


def chain(forward=22000.0, step=50, width=20, volume=10, expiry=EXPIRY):
    """Calls and puts around `forward` priced at intrinsic plus a time value falling with distance."""
    out = []
    for i in range(-width, width + 1):
        k = forward + i * step
        tv = max(120.0 - 4.0 * abs(i), 5.0)
        out += [quote(k, "CE", max(forward - k, 0) + tv, volume, expiry), quote(k, "PE", max(k - forward, 0) + tv,
                volume, expiry)]  # fmt: skip
    return tuple(out)


def rows(day, options=(), source="udiff", lots=None):
    return DayRows(day, tuple(options), (), lots or {}, source)
