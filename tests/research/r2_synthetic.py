"""Synthetic NSE F&O files and study inputs for the R2 tests (no real data: PROTOCOL.md section 11)."""

from __future__ import annotations

import csv
import io
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2] / "research" / "2026-10-15-r2-stock-options-results"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))

from r2study.bhav import Leg  # noqa: E402
from r2study.spreads import QuotedLeg  # noqa: E402

from fno.fo_bhavcopy import COLUMNS  # noqa: E402

CHARGES = {
    "brokerage_per_order": 20.0,
    "stt_sell_pct": 0.15,
    "exchange_txn_pct": 0.03503,
    "sebi_per_crore": 10.0,
    "ipft_per_crore": 50.0,
    "stamp_duty_buy_pct": 0.003,
    "gst_pct": 18.0,
}
NO_CHARGES = dict.fromkeys(CHARGES, 0.0)
LEGACY_COLUMNS = (
    "INSTRUMENT", "SYMBOL", "EXPIRY_DT", "STRIKE_PR", "OPTION_TYP", "OPEN", "HIGH", "LOW", "CLOSE", "SETTLE_PR",
    "CONTRACTS", "VAL_INLAKH", "OPEN_INT", "CHG_IN_OI", "TIMESTAMP",
)  # fmt: skip
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


def weekdays(first: date, last: date) -> list[date]:
    days, day = [], first
    while day <= last:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def zipped(name: str, rows: list[dict], columns) -> bytes:
    text = io.StringIO()
    writer = csv.DictWriter(text, columns)
    writer.writeheader()
    writer.writerows(rows)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name.removesuffix(".zip"), text.getvalue())
    return buffer.getvalue()


def udiff_name(day: date) -> str:
    return f"BhavCopy_NSE_FO_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"


def legacy_name(day: date) -> str:
    return f"fo{day:%d}{MONTHS[day.month - 1]}{day:%Y}bhav.csv.zip"


def future_row(day, symbol, expiry, close, lot, contracts=1000.0):
    row = dict.fromkeys(COLUMNS, "")
    turnover = contracts * lot * close
    row.update(TradDt=day.isoformat(), FinInstrmTp="STF", TckrSymb=symbol, XpryDt=expiry.isoformat(),
               ClsPric=close, SttlmPric=close, TtlTradgVol=contracts, TtlTrfVal=turnover, OpnIntrst=lot * 5000,
               NewBrdLotQty=lot)  # fmt: skip
    return row


def option_row(day, symbol, expiry, strike, kind, close, contracts=500.0, oi=None, lot=100):
    row = dict.fromkeys(COLUMNS, "")
    row.update(TradDt=day.isoformat(), FinInstrmTp="STO", TckrSymb=symbol, XpryDt=expiry.isoformat(),
               StrkPric=f"{strike:.2f}", OptnTp=kind, ClsPric=close, SttlmPric=close, TtlTradgVol=contracts,
               TtlTrfVal=contracts * lot * close, OpnIntrst=oi if oi is not None else lot * 1000)  # fmt: skip
    return row


def legacy_row(day: date, udiff: dict) -> dict:
    """The same contract in the old format (legacy lot must be derived; OPEN_INT in shares)."""
    stamp = f"{day:%d}-{MONTHS[day.month - 1].title()}-{day:%Y}"
    expiry = date.fromisoformat(udiff["XpryDt"])
    is_future = udiff["FinInstrmTp"] == "STF"
    return {
        "INSTRUMENT": "FUTSTK" if is_future else "OPTSTK", "SYMBOL": udiff["TckrSymb"],
        "EXPIRY_DT": f"{expiry:%d}-{MONTHS[expiry.month - 1].title()}-{expiry:%Y}",
        "STRIKE_PR": "0" if is_future else udiff["StrkPric"], "OPTION_TYP": "XX" if is_future else udiff["OptnTp"],
        "OPEN": udiff["ClsPric"], "HIGH": udiff["ClsPric"], "LOW": udiff["ClsPric"], "CLOSE": udiff["ClsPric"],
        "SETTLE_PR": udiff["SttlmPric"], "CONTRACTS": udiff["TtlTradgVol"],
        "VAL_INLAKH": float(udiff["TtlTrfVal"]) / 100_000, "OPEN_INT": udiff["OpnIntrst"], "CHG_IN_OI": 0,
        "TIMESTAMP": stamp,
    }  # fmt: skip


def chain_rows(day, symbol, expiry, centre, step, lot, contracts=500.0, count=5, atm_price=20.0):
    """Calls and puts at centre +- count steps; prices fall 4 per step away from the money."""
    rows = []
    for i in range(-count, count + 1):
        strike = centre + i * step
        call, put = max(atm_price - 4 * i, 1.0), max(atm_price + 4 * i, 1.0)
        rows.append(option_row(day, symbol, expiry, strike, "CE", call, contracts, lot=lot))
        rows.append(option_row(day, symbol, expiry, strike, "PE", put, contracts, lot=lot))
    return rows


def flat_chain(strikes, close=10.0, contracts=100.0, oi=50_000.0) -> dict:
    return {(float(k), kind): Leg(close, contracts, oi) for k in strikes for kind in ("CE", "PE")}


def quoted(steps, contracts, spread=0.02, mid=10.0, qty=200.0, lot=100, two_sided=True):
    half = mid * spread
    bid, ask = (mid - half, mid + half) if two_sided else (None, mid + half)
    return QuotedLeg(steps, contracts, bid, ask, qty, qty, lot)
