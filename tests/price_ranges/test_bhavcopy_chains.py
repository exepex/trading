"""G13b criterion 8: a day's archived NSE F&O file, UDiFF or the old format, gives every option of the
underlying as a G13 chain (traded closes, the same-expiry future's settlement, the three nearest expiries), the
end-of-day basis builds its ranges from it, and an absent or damaged file gives no chain."""

import io
import zipfile
from datetime import date

from fno.fo_bhavcopy import COLUMNS
from fno.price_distribution.pricing import black76_price
from fno.price_ranges.bhavcopy_chains import BhavcopyChains
from fno.price_ranges.build import CLOSE
from fno.price_ranges.constants import OK
from tests.price_ranges.builders import builder, closes, daily_files

DAY = date(2026, 10, 16)
EXPIRIES = (date(2026, 10, 28), date(2026, 11, 25), date(2026, 12, 30), date(2027, 1, 27))
NAME = "BhavCopy_NSE_FO_0_0_0_20261016_F_0000.csv"


def fo_row(symbol, kind, expiry, strike="", option="", close=0.0, volume=10):
    row = dict.fromkeys(COLUMNS, "")
    row.update(TradDt="2026-10-16", FinInstrmTp=kind, TckrSymb=symbol, XpryDt=expiry.isoformat(), StrkPric=strike,
               OptnTp=option, ClsPric=f"{close:.2f}", SttlmPric=f"{close:.2f}", TtlTradgVol=str(volume),
               UndrlygPric="51000.00")  # fmt: skip
    return row


def fo_file() -> bytes:
    rows = [fo_row("NIFTY", "IDO", EXPIRIES[0], "23000", "CE", 100.0)]  # another underlying, ignored
    for expiry in EXPIRIES:
        days = (expiry - DAY).days
        rows.append(fo_row("BANKNIFTY", "IDF", expiry, close=51_000.0))
        for strike in range(48_000, 54_100, 100):
            for option in ("CE", "PE"):
                price = black76_price(51_000.0, strike, option, days, 0.065, 0.13)
                rows.append(fo_row("BANKNIFTY", "IDO", expiry, str(strike), option, price, 0 if price < 0.5 else 10))
    lines = [",".join(COLUMNS)] + [",".join(r[c] for c in COLUMNS) for r in rows]
    return ("\n".join(lines) + "\n").encode()


def test_a_days_file_gives_the_three_nearest_expiries_of_the_underlying():
    chain = BhavcopyChains([daily_files({DAY: (NAME, fo_file())}, "udiff")]).chain("BANKNIFTY", DAY)
    assert [e.expiry for e in chain.expiries] == list(EXPIRIES[:3]) and chain.source == "bhavcopy"
    assert all(e.future == 51_000.0 for e in chain.expiries) and len(chain.expiries[0].quotes) == 122
    assert chain.observed_at == "2026-10-16T15:30:00+05:30" and chain.snapshot_id == NAME


def test_the_end_of_day_basis_ranges_banknifty_from_the_file():
    chain = BhavcopyChains([daily_files({DAY: (NAME, fo_file())}, "udiff")]).chain("BANKNIFTY", DAY)
    history = closes(last=DAY, base=51_000.0)
    record = builder().build("BANKNIFTY", DAY, "1545", chain, history, CLOSE, "backfill_eod", None)
    implied = [r for r in record["rows"] if r["forecaster"] == "implied"]
    assert {r["status"] for r in implied} == {OK} and record["status"] == OK


def test_no_file_or_a_damaged_one_gives_no_chain():
    assert BhavcopyChains([daily_files({}, "udiff")]).chain("BANKNIFTY", DAY) is None
    damaged = daily_files({DAY: (NAME, b"not,a,bhavcopy\n1,2,3\n")}, "udiff")
    assert BhavcopyChains([damaged]).chain("BANKNIFTY", DAY) is None


def legacy_file() -> bytes:
    """The same chain in NSE's old format (to 5 Jul 2024): zipped, `OPTIDX`/`FUTIDX`, `XX` for futures."""
    header = "INSTRUMENT,SYMBOL,EXPIRY_DT,STRIKE_PR,OPTION_TYP,OPEN,HIGH,LOW,CLOSE,SETTLE_PR,CONTRACTS,VAL_INLAKH,"
    lines = [header + "OPEN_INT,CHG_IN_OI,TIMESTAMP,"]
    for expiry in EXPIRIES:
        days, when = (expiry - DAY).days, expiry.strftime("%d-%b-%Y")
        lines.append(f"FUTIDX,BANKNIFTY,{when},0,XX,0,0,0,50990.00,51000.00,10,1,0,0,16-OCT-2026,")
        for strike in range(48_000, 54_100, 100):
            for option in ("CE", "PE"):
                price = black76_price(51_000.0, strike, option, days, 0.065, 0.13)
                volume = 0 if price < 0.5 else 10
                lines.append(f"OPTIDX,BANKNIFTY,{when},{strike},{option},0,0,0,{price:.2f},{price:.2f},{volume},1,0,0,"
                             "16-OCT-2026,")  # fmt: skip
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("fo16OCT2026bhav.csv", "\n".join(lines) + "\n")
    return buffer.getvalue()


def test_an_old_format_file_gives_the_same_chain():
    chain = BhavcopyChains([daily_files({DAY: ("fo16OCT2026bhav.csv.zip", legacy_file())}, "legacy")]).chain(
        "BANKNIFTY", DAY)  # fmt: skip
    current = BhavcopyChains([daily_files({DAY: (NAME, fo_file())}, "udiff")]).chain("BANKNIFTY", DAY)
    assert [e.expiry for e in chain.expiries] == list(EXPIRIES[:3])
    assert all(e.future == 51_000.0 for e in chain.expiries)  # settlement, not the 50,990 last trade
    assert [e.quotes for e in chain.expiries] == [e.quotes for e in current.expiries]
