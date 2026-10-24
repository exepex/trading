"""A day's v4 capture as A4e writes it (sidecar keys from response 278's sample), for the pack builder's tests:
NIFTY about 25,000 on 22 Oct 2026, the October (27th) and November (24th) monthlies, ATM legs priced near 12% IV."""

from datetime import date, datetime, time

from fno.models import IST

DAY = date(2026, 10, 22)
OCT, NOV = date(2026, 10, 27), date(2026, 11, 24)
MIDS = {(OCT, 24900.0, "CE"): 205.0, (OCT, 24900.0, "PE"): 55.0, (OCT, 25000.0, "CE"): 142.0,
        (OCT, 25000.0, "PE"): 92.0, (NOV, 25000.0, "CE"): 470.0, (NOV, 25000.0, "PE"): 270.0}  # fmt: skip


def at(hh, mm, ss=0, day=DAY):
    return datetime.combine(day, time(hh, mm, ss), IST).isoformat()


def row(expiry, strike, kind, mid, received=None, valid="true"):
    return {"expiry": expiry.isoformat(), "strike": str(strike), "type": kind, "bid": f"{mid - 1:.2f}",
            "ask": f"{mid + 1:.2f}", "last": f"{mid:.2f}", "last_trade_time": at(14, 29, 50),
            "response_received_at": received or at(14, 31, 5), "valid": valid}  # fmt: skip


def meta(**changes):
    body = {
        "provider": "groww",
        "chains": [{"expiry": OCT.isoformat(), "spot": 25000.0, "request_sent_at": at(14, 30, 1),
                    "response_received_at": at(14, 30, 2)},
                   {"expiry": NOV.isoformat(), "spot": 25001.0, "request_sent_at": at(14, 30, 3),
                    "response_received_at": at(14, 30, 4)}],
        "levels_requested_at": at(14, 30, 5), "levels_received_at": at(14, 30, 6),
        "india_vix": 11.8, "india_vix_time": "22-Oct-2026 14:29",
        "futures": [{"expiry": OCT.isoformat(), "last": 25040.0, "volume": 1200},
                    {"expiry": NOV.isoformat(), "last": 25180.0, "volume": 300}],
        "clock_checks": ["clock_ok", "clock_ok"], "clock_status": "clock_ok", "clock_worst_skew_seconds": 0.2,
    }  # fmt: skip
    return {**body, **changes}


def rows():
    return [row(e, k, t, m) for (e, k, t), m in MIDS.items()]
