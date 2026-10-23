"""Both NSE F&O formats read into one record format: real rows from 2 January 2024, a day NSE published both."""

import io
import zipfile
from pathlib import Path

import pytest

from fno.fo_bhavcopy import COLUMNS, BadFile, legacy_date, read_fo_file, read_index_closes, read_index_values

NSE = Path(__file__).parent / "fixtures" / "nse"
CURRENT = "BhavCopy_NSE_FO_0_0_0_20240102_F_0000.csv.zip"
OLD = "fo02JAN2024bhav.csv.zip"
KEY = ("FinInstrmTp", "TckrSymb", "XpryDt", "StrkPric", "OptnTp")
SHARED = ("OpnPric", "HghPric", "LwPric", "ClsPric", "SttlmPric", "OpnIntrst", "ChngInOpnIntrst", "TtlTradgVol")


def by_contract(records):
    return {tuple(float(r[k]) if k == "StrkPric" and r[k] else r[k] for k in KEY): r for r in records}


def read(name, closes=None):
    return read_fo_file(name, (NSE / name).read_bytes(), closes)


def test_index_closes_include_nifty_bank_and_vix():
    closes = read_index_closes((NSE / "ind_close_all_02012024.csv").read_bytes())
    assert closes["Nifty 50"] == 21665.8 and closes["Nifty Bank"] == 47761.65 and closes["India VIX"] == 14.58
    assert closes["Nifty MidSmall Financial Services"] == 13048.62  # a "-" open does not hide the close


def test_index_values_hold_each_index_s_open_high_low_and_close():
    """Story A4h-2: the official day range; a "-" is None, never a number, and the closes equal read_index_closes'."""
    data = (NSE / "ind_close_all_02012024.csv").read_bytes()
    values = read_index_values(data)
    assert values["Nifty 50"]["close"] == 21665.8 and set(values["Nifty 50"]) == {"open", "high", "low", "close"}
    assert values["Nifty 50"]["low"] <= values["Nifty 50"]["close"] <= values["Nifty 50"]["high"]
    assert values["Nifty MidSmall Financial Services"]["open"] is None
    closes = {name: found["close"] for name, found in values.items() if found["close"] is not None}
    assert closes == read_index_closes(data)


def test_both_formats_give_the_same_contracts_and_numbers():
    closes = read_index_closes((NSE / "ind_close_all_02012024.csv").read_bytes())
    new, old = by_contract(read(CURRENT)), by_contract(read(OLD, closes))
    assert set(new) == set(old) and len(new) == 7
    for contract, record in new.items():
        assert set(record) == set(COLUMNS) and set(old[contract]) == set(COLUMNS)
        for field in SHARED:
            assert float(record[field]) == float(old[contract][field]), (contract, field)
        assert abs(float(record["TtlTrfVal"]) - float(old[contract]["TtlTrfVal"])) <= 1000  # lakh rounding
        assert record["TradDt"] == old[contract]["TradDt"] == "2024-01-02"
        if contract[0] in ("IDO", "IDF"):  # the index close is the underlying UDiFF reports
            assert float(record["UndrlygPric"]) == float(old[contract]["UndrlygPric"])


def test_what_the_old_format_lacks_stays_empty_never_guessed():
    old = by_contract(read(OLD, read_index_closes((NSE / "ind_close_all_02012024.csv").read_bytes())))
    stock_option = old[("STO", "RELIANCE", "2024-01-25", 2600.0, "CE")]
    assert stock_option["UndrlygPric"] == "" and stock_option["NewBrdLotQty"] == "" and stock_option["LastPric"] == ""
    future = old[("IDF", "NIFTY", "2024-01-25", "", "")]
    assert future["StrkPric"] == "" and future["OptnTp"] == ""
    no_closes = by_contract(read(OLD))
    assert no_closes[("IDF", "NIFTY", "2024-01-25", "", "")]["UndrlygPric"] == ""  # no index file: left empty


def test_old_dates_do_not_depend_on_language_settings():
    assert legacy_date("02-JAN-2019") == "2019-01-02" and legacy_date("31-Jan-2019") == "2019-01-31"
    with pytest.raises(ValueError):
        legacy_date("31-Foo-2019")


def zipped(name, text):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, text)
    return buffer.getvalue()


def test_damaged_or_unknown_files_are_refused_whole():
    with pytest.raises(BadFile):
        read_fo_file(OLD, b"not a zip")
    with pytest.raises(BadFile):
        read_fo_file("something.csv", b"a,b\n1,2\n")
    with pytest.raises(BadFile):
        read_fo_file(OLD, zipped("x.csv", "TradDt,TckrSymb\n2024-01-02,NIFTY\n"))  # wrong columns for the name
    with pytest.raises(BadFile):
        read_fo_file(OLD, zipped("x.csv", "INSTRUMENT,SYMBOL\nOPTFUT,NIFTY\n"))  # unknown instrument
    with pytest.raises(BadFile):
        read_index_closes(b"Index Name,Closing Index Value\n")
    damaged = bytearray((NSE / OLD).read_bytes())
    damaged[60] ^= 0xFF  # one flipped byte in the compressed data
    with pytest.raises(BadFile):
        read_fo_file(OLD, bytes(damaged))
