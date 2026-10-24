"""A20a: the readers of NSE's ban list and market lots accept today's real layouts (fixtures cut from
NSE's files of 15-16 Oct 2026) and refuse damaged ones whole, so the archive's content check never keeps a bad copy."""

from datetime import date
from pathlib import Path

import pytest

from fno.fo_bhavcopy import BadFile
from fno.research_data.fo_masters import ban_list_trade_date, read_ban_list, read_lot_sizes
from fno.storage.content_checks import COVERED_SESSION, VALIDATORS
from fno.storage.snapshot_source import FoBanListSource, FoLotSizeSource

FIXTURES = Path(__file__).parents[1] / "fixtures" / "nse" / "fo_masters"
BAN = (FIXTURES / "fo_secban_16102026.csv").read_bytes()
LOTS = (FIXTURES / "fo_mktlots_16102026.csv").read_bytes()


def test_the_ban_list_names_its_trade_date_and_securities_in_order():
    ban = read_ban_list(BAN, "fo_secban.csv")
    assert ban.trade_date == date(2026, 10, 16) and ban.symbols == ("AMBUJACEM", "KAYNES", "SAIL")
    assert ban_list_trade_date("fo_secban.csv", BAN) == date(2026, 10, 16)


def test_an_empty_ban_list_is_valid():
    assert read_ban_list(BAN.splitlines(keepends=True)[0], "fo_secban.csv").symbols == ()


@pytest.mark.parametrize(
    "damaged",
    [b"", b"<html>Access Denied</html>", BAN.replace(b"2,KAYNES", b"3,KAYNES"), BAN + b"oops\n"],
    ids=["empty", "html", "numbering", "stray line"],
)
def test_a_damaged_ban_list_is_refused(damaged):
    with pytest.raises(BadFile):
        read_ban_list(damaged, "fo_secban.csv")


def test_lot_sizes_per_symbol_and_month_skip_the_stock_section_header_and_blank_months():
    lots = read_lot_sizes(LOTS, "fo_mktlots.csv")
    assert lots["NIFTY"]["OCT-26"] == 65 and lots["BANKNIFTY"]["NOV-26"] == 30
    assert "Symbol" not in lots and "DEC-27" not in lots["BANKNIFTY"]  # NSE leaves that month blank for BANKNIFTY
    assert lots["UJJIVANSFB"] == {"OCT-26": 8000, "NOV-26": 8000, "DEC-26": 8000}
    assert read_lot_sizes(LOTS + b"\n\n", "fo_mktlots.csv") == lots  # trailing blank lines are not rows


@pytest.mark.parametrize(
    "damaged",
    [b"SYMBOL,OCT-26\nNIFTY,65\n", LOTS.replace(b"NIFTY     ,65", b"NIFTY     ,6x", 1),
     LOTS.replace(b"NIFTY 50", b"NIFTY 50,EXTRA", 1), LOTS.replace(b",NIFTY     ,", b",NIFTYX    ,", 1),
     LOTS.rstrip(b"\r\n").rsplit(b",", 1)[0] + b"\n"],
    ids=["header", "number", "cells", "no NIFTY", "short last row"],
)  # fmt: skip
def test_damaged_lot_sizes_are_refused(damaged):
    with pytest.raises(BadFile):
        read_lot_sizes(damaged, "fo_mktlots.csv")


def test_the_archive_checks_and_files_them_with_these_readers():
    assert VALIDATORS[FoBanListSource]("fo_secban.csv", BAN).trade_date == date(2026, 10, 16)
    assert VALIDATORS[FoLotSizeSource]("fo_mktlots.csv", LOTS)["NIFTY"]["OCT-26"] == 65
    assert COVERED_SESSION[FoBanListSource]("fo_secban.csv", BAN) == date(2026, 10, 16)
