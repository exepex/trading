"""Story B1 criterion 2: F1, F2 and F3 on three real decision days equal a hand calculation made here straight from
the panel's CSV rows (not through fno's reader or models), to 0.01 volatility points for F1. The pinned numbers are
the values; the builder's claims file (reviews/claude/, story B1) lists the inputs of one day for a calculator."""

import csv
import gzip
import math
from datetime import date

import pytest
from feature_fixtures import black76
from real_cycles import real_context

from fno.composition import build_features
from fno.config import load_app_config
from fno.storage.wiring import PANEL_FOLDER

# decision day -> (F1 in volatility points, F2, F3), recomputed below by hand
PINNED = {
    date(2025, 3, 12): (3.74, False, False),
    date(2025, 9, 22): (2.31, False, True),  # RBI policy of 1 Oct 2025 in the window
    date(2026, 9, 16): (4.43, True, False),
}


@pytest.fixture(scope="module")
def raw():
    """date -> (session, Nifty 50 close, India VIX close), and the option and future rows of the sample days."""
    closes, options, futures = {}, [], []
    for year in (2024, 2025, 2026):
        with gzip.open(PANEL_FOLDER / f"options_{year}.csv.gz", "rt", newline="") as f:
            for row in csv.DictReader(f):
                closes.setdefault(row["date"], (row["session"], float(row["underlying"]), float(row["vix"])))
                if date.fromisoformat(row["date"]) in PINNED:
                    options.append(row)
        with gzip.open(PANEL_FOLDER / f"futures_{year}.csv.gz", "rt", newline="") as f:
            futures += [row for row in csv.DictReader(f) if date.fromisoformat(row["date"]) in PINNED]
    return closes, options, futures


def bisect_vol(price, forward, strike, years, kind):
    lo, hi = 0.01, 2.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if black76(forward, strike, years, mid, kind) > price else (mid, hi)
    return (lo + hi) / 2


def hand_f1(raw, day, expiry):
    closes, options, futures = raw
    rows = [r for r in options if r["date"] == day.isoformat() and r["expiry"] == expiry.isoformat()]
    spot = float(rows[0]["underlying"])
    atm = min({float(r["strike"]) for r in rows}, key=lambda k: (abs(k - spot), k))
    legs = {r["type"]: r for r in rows if float(r["strike"]) == atm}
    assert all(int(legs[k]["volume"]) > 0 for k in ("CE", "PE"))
    forward = next(
        float(r["close"]) for r in futures if r["date"] == day.isoformat() and r["expiry"] == expiry.isoformat()
    )
    years = (expiry - day).days / 365
    iv = sum(bisect_vol(float(legs[k]["close"]), forward, atm, years, k) for k in ("CE", "PE")) / 2 * 100
    series = [c for d, (s, c, _) in sorted(closes.items()) if d <= day.isoformat() and s != "muhurat"][-21:]
    returns = [math.log(b / a) for a, b in zip(series, series[1:])]
    realised = math.sqrt(sum(r * r for r in returns) / 20 * 252) * 100
    return iv - realised


def hand_f2(raw, day):
    closes = raw[0]
    previous = sorted([v for d, (s, _, v) in sorted(closes.items()) if d < day.isoformat() and s != "muhurat"][-250:])
    median = (previous[124] + previous[125]) / 2
    assert len(previous) == 250
    return closes[day.isoformat()][2] > median


@pytest.mark.parametrize("day", sorted(PINNED))
def test_features_equal_the_hand_calculation_on_three_real_days(real_data, raw, day):
    context = real_context(real_data, day)
    f1, f2, f3 = (f.value(real_data, day, context) for f in build_features(load_app_config()))
    assert f1 == pytest.approx(hand_f1(raw, day, context.expiry), abs=0.01)
    assert f2 is hand_f2(raw, day)
    assert (round(f1, 2), f2, f3) == PINNED[day]
