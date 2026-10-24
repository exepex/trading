"""Story G10 part 2, criterion 1: a pack built from a capture has every field with its observed_at; a field received
at 14:40:01 is absent; a required field missing gives system_late and no pack; only a clock_ok capture gives A."""

from datetime import datetime

import pytest

from fno.models import IST
from fno.research_engine.implied_vol import Black76
from fno.research_engine.live_features import LiveAtmIvMinusRealised
from fno.v4_pack.builder import PackBuilder
from fno.v4_pack.capture import V4Capture
from fno.v4_pack.codec import pack_bytes, pack_sha256, read_pack
from tests.v4_pack.capture_fixture import DAY, NOV, OCT, at, meta, row, rows

RELEASED = datetime(2026, 10, 22, 14, 40, 30, tzinfo=IST)
METHOD = "g1_v2_live_atm_iv30/sha256:" + "d" * 64


def build(capture_meta=None, capture_rows=None, day=DAY):
    builder = PackBuilder(LiveAtmIvMinusRealised(None, 0.065, Black76()), METHOD, lambda: RELEASED)
    capture = V4Capture("groww/derivatives/quote-snapshots-v4", "nifty_20261022_143100",
                        capture_meta if capture_meta is not None else meta(),
                        tuple(capture_rows if capture_rows is not None else rows()))  # fmt: skip
    return builder.build(day, capture)


def test_a_full_capture_gives_an_a_pack_with_every_fields_own_time():
    built = build()
    pack = built.pack
    assert built.reasons == () and pack.label == "A" and pack.released_at == RELEASED
    assert (pack.spot.value, pack.spot.observed_at.isoformat()) == (25000.0, at(14, 30, 2))
    assert (pack.future.expiry, pack.future.last, pack.future.bid, pack.future.ask) == (OCT, 25040.0, None, None)
    assert pack.india_vix.observed_at.isoformat() == at(14, 30, 6) and pack.india_vix.nse_time.hour == 14
    assert len(pack.chain) == 6 and all(q.observed_at.isoformat() == at(14, 31, 5) for q in pack.chain)
    assert pack.iv30.expiries == (OCT, NOV) and not pack.iv30.flagged and 8 < pack.iv30.value < 20
    assert pack.iv30.method == METHOD and pack.captured_from.endswith("/nifty_20261022_143100")
    data = pack_bytes(pack)
    assert read_pack(data, pack_sha256(data)) == pack  # the builder's pack passes the reader's checks


def test_a_quote_received_at_14_40_01_is_not_in_the_pack_and_14_40_00_is():
    extra = [
        row(NOV, 25100.0, "CE", 420.0, received=at(14, 40, 1)),
        row(NOV, 25100.0, "PE", 320.0, received=at(14, 40)),
    ]
    chain = build(capture_rows=rows() + extra).pack.chain
    assert (NOV, 25100.0, "PE") in {(q.expiry, q.strike, q.kind) for q in chain}
    assert (NOV, 25100.0, "CE") not in {(q.expiry, q.strike, q.kind) for q in chain}


def test_an_invalid_row_is_left_out_of_the_chain():
    chain = build(capture_rows=rows() + [row(NOV, 25200.0, "CE", 300.0, valid="false")]).pack.chain
    assert (NOV, 25200.0, "CE") not in {(q.expiry, q.strike, q.kind) for q in chain}


@pytest.mark.parametrize(
    ("capture_meta", "capture_rows", "reason"),
    [
        (meta(clock_status="clock_skew"), None, "clock not checked ok (clock_skew)"),
        ({k: v for k, v in meta().items() if k != "clock_status"}, None, "clock not checked ok (missing)"),
        (meta(levels_received_at=at(14, 40, 1)), None, "levels"),
        (meta(india_vix=None), None, "no India VIX"),
        (meta(futures=[{"expiry": "2026-10-22", "last": 25000.0, "volume": 1}]), None, "no monthly future"),
        (meta(chains=[]), None, "no spot"),
        (
            None,
            [r for r in rows() if not (r["strike"] == "25000.0" and r["type"] == "PE" and r["expiry"] == "2026-10-27")],
            "ATM call and put",
        ),
        (None, [row(OCT, 25000.0, "CE", 142.0), row(OCT, 25000.0, "PE", 92.0, received=at(14, 29, 59))], "ATM"),
    ],
)
def test_a_required_field_missing_gives_system_late_and_names_why(capture_meta, capture_rows, reason):
    built = build(capture_meta, capture_rows)
    assert built.pack is None and any(reason in r for r in built.reasons)


def test_no_capture_gives_system_late():
    builder = PackBuilder(LiveAtmIvMinusRealised(None, 0.065, Black76()), METHOD, lambda: RELEASED)
    assert builder.build(DAY, None).reasons == ("no canonical v4 capture",)


def test_iv30_needs_a_usable_monthly_and_one_alone_is_flagged():
    october_only = build(capture_rows=[r for r in rows() if r["expiry"] == OCT.isoformat()])
    assert october_only.reasons == ("IV30 not computable from the window's quotes",)  # 5 days left: under 7
    nov_chain = {"expiry": NOV.isoformat(), "spot": 25001.0, "response_received_at": at(14, 30, 4)}
    nov_only = meta(futures=[{"expiry": NOV.isoformat(), "last": 25180.0, "volume": 300}], chains=[nov_chain])
    built = build(nov_only, [r for r in rows() if r["expiry"] == NOV.isoformat()])
    assert built.pack.iv30.flagged and built.pack.iv30.expiries == (NOV,) and built.pack.future.expiry == NOV


def test_on_a_monthly_expiry_day_e_is_the_next_monthly():
    expiry_day = meta(futures=[{"expiry": OCT.isoformat(), "last": 25010.0, "volume": 9},
                               {"expiry": NOV.isoformat(), "last": 25180.0, "volume": 300}],
                      chains=[{"expiry": NOV.isoformat(), "spot": 25001.0, "response_received_at": at(14, 30, 4, OCT)}],
                      levels_received_at=at(14, 30, 6, OCT))  # fmt: skip
    capture_rows = [row(NOV, 25000.0, k, m, received=at(14, 31, day=OCT)) for k, m in (("CE", 470.0), ("PE", 270.0))]
    built = build(expiry_day, capture_rows, day=OCT)
    assert built.pack.future.expiry == NOV and built.pack.spot.value == 25001.0
