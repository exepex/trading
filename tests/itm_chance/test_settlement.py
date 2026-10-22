"""The outcome rule (judges 452 and 452.1): E7 first, the old-format file's index future behind it, the official
close as the cross-check; nothing is guessed."""

import io
import zipfile
from dataclasses import dataclass
from datetime import date

import pytest

from fno.desk.settlement import SettlementError
from fno.itm_chance.settlement import (
    DIFFERS,
    NO_CLOSE,
    NOT_SETTLED,
    FirstSettlement,
    LegacyFileSettlement,
    settle,
)
from fno.storage.raw_source import NseLegacyFoSource

from .builders import REFUSED, FakePrices

EXPIRY = date(2019, 1, 31)
HEADER = (
    "INSTRUMENT,SYMBOL,EXPIRY_DT,STRIKE_PR,OPTION_TYP,OPEN,HIGH,LOW,CLOSE,SETTLE_PR,CONTRACTS,VAL_INLAKH,OPEN_INT,"
    "CHG_IN_OI,TIMESTAMP"
)


def legacy_file(future: str, option: str) -> bytes:
    lines = [HEADER,
             f"FUTIDX,NIFTY,31-Jan-2019,0,XX,1,1,1,1,{future},1,1,1,1,31-JAN-2019",
             f"OPTIDX,NIFTY,31-Jan-2019,10800,CE,1,1,1,1,{option},1,1,1,1,31-JAN-2019",
             "FUTIDX,NIFTY,28-Feb-2019,0,XX,1,1,1,1,10900.00,1,1,1,1,31-JAN-2019",
             "FUTIDX,BANKNIFTY,31-Jan-2019,0,XX,1,1,1,1,27300.00,1,1,1,1,31-JAN-2019"]  # fmt: skip
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(NseLegacyFoSource.filename_for(EXPIRY).removesuffix(".zip"), "\n".join(lines) + "\n")
    return buffer.getvalue()


@dataclass
class Found:
    data: bytes | None


class FakeLibrary:
    def __init__(self, files: dict[str, bytes]):
        self.files = files

    def get(self, path: str) -> Found:
        return Found(self.files.get(path))


def legacy(future="10830.95", option="0") -> LegacyFileSettlement:
    return LegacyFileSettlement(FakeLibrary({NseLegacyFoSource.path_for(EXPIRY): legacy_file(future, option)}))


@pytest.mark.parametrize("option", ["0", "10830.95"])
def test_the_legacy_file_gives_the_expiring_future_settle(option):
    found = legacy(option=option).final_settlement("NIFTY", EXPIRY)
    assert found.price == 10830.95 and found.source == NseLegacyFoSource.path_for(EXPIRY)


def test_an_option_with_its_own_settle_price_is_refused():
    with pytest.raises(SettlementError, match="neither the future's nor 0"):
        legacy(option="35.10").final_settlement("NIFTY", EXPIRY)


def test_no_legacy_file_is_none():
    assert LegacyFileSettlement(FakeLibrary({})).final_settlement("NIFTY", EXPIRY) is None


def test_the_first_reader_with_a_file_decides():
    first, second = FakePrices({}), FakePrices({EXPIRY: 100.0})
    label, found = FirstSettlement([("e7", first), ("legacy", second)]).final_settlement("NIFTY", EXPIRY)
    assert (label, found.price, first.asked) == ("legacy", 100.0, [EXPIRY])
    both = FirstSettlement([("e7", FakePrices({EXPIRY: 1.0})), ("legacy", second)])
    assert both.final_settlement("NIFTY", EXPIRY)[0] == "e7"


def prices(value) -> FirstSettlement:
    return FirstSettlement([("e7", FakePrices({EXPIRY: value}))])


def test_settlement_equal_to_the_close_is_used():
    s = settle("NIFTY", EXPIRY, prices(10830.95), lambda u, d: 10830.95)
    assert (s.usable, s.price, s.source, s.problem) == (True, 10830.95, "e7", None)


def test_a_settlement_that_differs_from_the_close_is_left_out_with_both_values():
    s = settle("NIFTY", EXPIRY, prices(10830.95), lambda u, d: 10830.90)
    assert not s.usable and s.problem == DIFFERS.format(settle=10830.95, close=10830.90) and s.close == 10830.90


def test_no_close_keeps_the_settlement_and_says_so():
    s = settle("NIFTY", EXPIRY, prices(10830.95), lambda u, d: None)
    assert s.usable and s.problem == NO_CLOSE


def test_no_file_is_not_settled_and_a_refusal_is_left_out_with_its_reason():
    assert settle("NIFTY", EXPIRY, prices(None), lambda u, d: 1.0).problem == NOT_SETTLED
    refused = settle("NIFTY", EXPIRY, prices(REFUSED), lambda u, d: 1.0)
    assert not refused.usable and refused.problem == str(REFUSED)
