"""Story G10 completion, criterion 3a (pack side): the pack carries `v4_expiry` as the capture recorded it (never
recomputed at release), the future's bid, ask and last trade time from the capture's own `FUT` row received inside the
window (with its own `quoted_at`) and NSE's day volume; a missing or late quote leaves bid and ask None (V5 then voids
itself), never a system_late day; a V4 expiry the capture could not choose becomes a note the release alerts."""

from datetime import date

import pytest

from fno.v4_pack.codec import PackFormatError, pack_bytes, pack_sha256, read_pack
from tests.v4_pack.capture_fixture import OCT, at, meta, rows
from tests.v4_pack.test_pack_builder import build

V4_EXPIRY = date(2026, 10, 27)


def fut(received=None, bid="25040", ask="25042.5"):
    received = received or at(14, 31, 30)
    return {"expiry": OCT.isoformat(), "strike": "", "type": "FUT", "bid": bid, "ask": ask, "last": "25041",
            "last_trade_time": at(14, 30, 58), "response_received_at": received, "valid": "true"}  # fmt: skip


def test_the_future_s_quote_and_v4_expiry_are_carried_with_their_own_times():
    built = build(meta(v4_expiry=V4_EXPIRY.isoformat()), rows() + [fut()])
    future = built.pack.future
    assert (future.bid, future.ask, future.volume) == (25040.0, 25042.5, 1200)  # volume: NSE's, from the sidecar
    assert future.last_trade_time.isoformat() == at(14, 30, 58) and future.quoted_at.isoformat() == at(14, 31, 30)
    assert future.observed_at.isoformat() == at(14, 30, 6)  # last and volume keep the level read's own time
    assert built.pack.v4_expiry == V4_EXPIRY and built.notes == ()
    assert all(q.kind in ("CE", "PE") for q in built.pack.chain)  # the FUT row is never a chain quote
    data = pack_bytes(built.pack)
    assert read_pack(data, pack_sha256(data)) == built.pack


@pytest.mark.parametrize("row", [None, fut(received=at(14, 40, 1))])
def test_no_quote_or_a_late_quote_leaves_bid_and_ask_none_and_the_day_a(row):
    built = build(meta(), rows() + ([row] if row else []))
    assert built.pack is not None and (built.pack.future.bid, built.pack.future.quoted_at) == (None, None)
    assert built.pack.v4_expiry is None  # the sidecar named none


def test_a_v4_expiry_the_capture_could_not_choose_is_a_note():
    built = build(meta(v4_expiry=None, v4_expiry_note="v4 expiry not chosen: 2027-01-05 is outside the calendar"))
    assert built.pack.v4_expiry is None and built.notes == ("v4 expiry not chosen: 2027-01-05 is outside the calendar",)


@pytest.mark.parametrize(
    ("old", "new"),
    [('"volume":1200', '"volume":-1'), (f'"quoted_at":"{at(14, 31, 30)}"', f'"quoted_at":"{at(14, 41)}"')],
)
def test_the_codec_refuses_a_bad_volume_or_a_quote_outside_the_window(old, new):
    data = pack_bytes(build(meta(), rows() + [fut()]).pack)
    assert old.encode() in data
    changed = data.replace(old.encode(), new.encode())
    with pytest.raises(PackFormatError):
        read_pack(changed, pack_sha256(changed))
