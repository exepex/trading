"""Story MS-P1d criteria 9 and 11: expiring legs settle at intrinsic against each index's `SttlmPric` from the
already-archived F&O file (stores only: the school never fetches from NSE); no file gives `settlement_needed`."""

from dataclasses import replace

import pytest

from fno.costs import settlement_charges_breakdown
from fno.school.constants import SIDE_BUY, SIDE_SELL, ExitState, OptionKind, RoadCode
from fno.school.contracts.accounts import SettlementUnavailable
from fno.school.contracts.decisions import LegSpec
from fno.school.contracts.snapshot import ContractKey
from fno.school.execution.settlement_source import ArchivedOnly
from fno.storage.raw_store import LocalFolderStore
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c

from .school_builders import CHARGES, REAL_DAY, SETTLEMENTS, fills, settlement_folder, settlement_source

ROAD_OF = {"NIFTY": RoadCode.NIFTY_MONTHLY, "BANKNIFTY": RoadCode.BANKNIFTY_MONTHLY,
           "FINNIFTY": RoadCode.FINNIFTY_MONTHLY, "MIDCPNIFTY": RoadCode.MIDCPNIFTY_MONTHLY}  # fmt: skip


def spread(index: str, short: float, long: float, kind=OptionKind.PUT):
    """A short spread on `index` expiring on the fixture's expiry day: sell `short`, buy `long`."""
    legs = (LegSpec(ContractKey(REAL_DAY, short, kind), SIDE_SELL, 1), LegSpec(ContractKey(REAL_DAY, long, kind),
                                                                              SIDE_BUY, 1))  # fmt: skip
    return replace(b.position(), road=ROAD_OF[index], legs=legs, lot=10, opened=REAL_DAY)


def test_the_settlement_source_conforms(tmp_path):
    c.check_settlement_source(settlement_source(settlement_folder(tmp_path)), ("FINNIFTY", REAL_DAY),
                              ("FINNIFTY", REAL_DAY.replace(day=24)))  # fmt: skip


@pytest.mark.parametrize("index", sorted(SETTLEMENTS))
def test_each_index_settles_at_intrinsic_against_its_own_price(tmp_path, index):
    price = SETTLEMENTS[index]
    short, long = round(price) + 100.0, round(price) - 100.0  # the short put in the money, the long out of it
    result = fills(settlement_folder(tmp_path)).settle(spread(index, short, long), REAL_DAY)
    sold_back, sold_long = result.legs
    assert (sold_back.side, sold_back.price) == (SIDE_BUY, pytest.approx(short - price))
    assert (sold_long.side, sold_long.price, sold_long.charges) == (SIDE_SELL, 0.0, 0.0)
    assert sold_back.charges == pytest.approx(sum(settlement_charges_breakdown(short - price, 10, SIDE_BUY,
                                                                               CHARGES).values()))  # fmt: skip
    assert (
        result.rests_on == settlement_source(settlement_folder(tmp_path / "again")).price(index, REAL_DAY).file_sha256
    )
    assert result.filled_at.isoformat() == f"{REAL_DAY}T15:30:00+05:30"


def test_an_itm_long_pays_exercise_stt(tmp_path):
    price = SETTLEMENTS["BANKNIFTY"]
    long_call = spread("BANKNIFTY", price + 200.0, price - 200.0, OptionKind.CALL)  # bought call 200 in the money
    result = fills(settlement_folder(tmp_path)).settle(long_call, REAL_DAY)
    exercised = [leg for leg in result.legs if leg.side == SIDE_SELL][0]
    assert exercised.price == pytest.approx(200.0)
    assert exercised.charges == pytest.approx(sum(settlement_charges_breakdown(200.0, 10, SIDE_SELL,
                                                                               CHARGES).values()))  # fmt: skip


def test_no_archived_file_means_settlement_needed_and_no_fetch(tmp_path):
    assert ArchivedOnly().fetch("anything") is None
    result = fills(tmp_path).settle(spread("NIFTY", 21400.0, 21300.0), REAL_DAY)
    assert result.state == ExitState.SETTLEMENT_NEEDED and not result.legs


def test_a_file_without_one_clear_price_is_settlement_needed_never_a_guess(tmp_path):
    folder = settlement_folder(tmp_path, {"NIFTY": SETTLEMENTS["NIFTY"]})  # no BANKNIFTY rows in the file
    with pytest.raises(SettlementUnavailable, match="no expiring contracts"):
        settlement_source(folder).price("BANKNIFTY", REAL_DAY)
    assert fills(folder).settle(spread("BANKNIFTY", 45100.0, 45000.0), REAL_DAY).state == ExitState.SETTLEMENT_NEEDED


def test_another_index_or_expiry_is_refused(tmp_path):
    with pytest.raises(ValueError, match="not a school road"):
        settlement_source(settlement_folder(tmp_path)).price("SENSEX", REAL_DAY)
    with pytest.raises(ValueError, match="does not expire wholly"):
        fills(tmp_path).settle(spread("NIFTY", 21400.0, 21300.0), REAL_DAY.replace(day=24))


def test_settlement_with_no_store_stops_by_name_never_waits_forever(monkeypatch, tmp_path):
    """Judge 486 finding 2, on b's stores: no readable store would leave every expired position
    `settlement_needed` for ever, counted at its worst case, with no alert; b's `build_archive_stores` refuses by
    name, and the settlement source is built only over the stores it returns."""
    from fno.school.execution import wiring
    from fno.school.roads.wiring import RawFilesNotConfigured

    def none():
        raise RawFilesNotConfigured("set the service-account settings")

    monkeypatch.setattr(wiring, "build_archive_stores", none)
    with pytest.raises(RawFilesNotConfigured):
        wiring.build_settlement_source()
    folder = settlement_folder(tmp_path)
    monkeypatch.setattr(wiring, "build_archive_stores", lambda: [LocalFolderStore(folder)])
    assert wiring.build_settlement_source().price("FINNIFTY", REAL_DAY).price == SETTLEMENTS["FINNIFTY"]
