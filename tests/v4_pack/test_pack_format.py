"""Story G10 part 2, criterion 1 (the format side): every field carries its observed_at, the SHA is of the stored
canonical bytes, and a field observed outside 14:30-14:40 or a broken document is refused."""

import json
from dataclasses import replace
from datetime import date, datetime, time

import pytest

from fno.models import IST
from fno.v4_pack.codec import PackFormatError, pack_bytes, pack_sha256, read_pack
from fno.v4_pack.model import ChainQuote, FutureQuote, Iv30, Level, Pack, VixLevel
from fno.v4_pack.paths import pack_path, release_path

DAY = date(2026, 10, 22)
MONTHLY, NEXT_MONTHLY = date(2026, 10, 27), date(2026, 11, 24)
METHOD = "atm_iv30_g1/sha256:" + "c" * 64


def at(hh, mm, ss=0):
    return datetime.combine(DAY, time(hh, mm, ss), IST)


def quote(expiry, strike, kind, bid=101.5, ask=102.5, seen=(14, 30, 4)):
    return ChainQuote(expiry, strike, kind, bid, ask, 102.0, at(14, 29, 58), at(*seen))


def a_pack(**changes):
    chain = (quote(MONTHLY, 25000.0, "CE"), quote(MONTHLY, 25000.0, "PE", bid=None),
             quote(NEXT_MONTHLY, 25000.0, "CE", seen=(14, 31, 9)))  # fmt: skip
    pack = Pack(DAY, "A", "groww", "groww_api", "a4/2026-10-22/attempt-1", at(14, 32), Level(25012.4, at(14, 30, 1)),
                FutureQuote(NEXT_MONTHLY, 25110.0, 25108.5, 25111.0, at(14, 30, 2)),
                VixLevel(11.82, at(14, 30, 3), at(14, 29, 0)), chain,
                Iv30(0.112, False, (MONTHLY, NEXT_MONTHLY), METHOD, at(14, 31, 9)))  # fmt: skip
    return replace(pack, **changes)


def test_a_pack_round_trips_through_its_canonical_bytes_and_its_sha_is_of_those_bytes():
    pack = a_pack()
    data = pack_bytes(pack)
    assert read_pack(data, pack_sha256(data)) == pack
    assert data == json.dumps(json.loads(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert pack_bytes(a_pack()) == data  # the same pack, the same identity


def test_every_field_carries_its_observed_at_and_mid_only_with_both_sides():
    body = json.loads(pack_bytes(a_pack()))
    assert all("observed_at" in body[name] for name in ("spot", "future", "india_vix"))
    assert body["iv30"]["observed_by"] and all(item["observed_at"] for item in body["chain"])
    assert [item.get("mid") for item in body["chain"]] == [102.0, None, 102.0]
    assert a_pack().observed_by() == at(14, 31, 9)


def test_the_paths_are_drive_paths_per_year():
    assert pack_path(DAY) == "v4/packs/2026/2026-10-22.json"
    assert release_path(DAY) == "v4/days/2026/2026-10-22.json"


@pytest.mark.parametrize("seen", [at(14, 40, 1), at(14, 29, 59)])
def test_a_field_observed_outside_the_window_is_refused(seen):
    late = a_pack(spot=Level(25012.4, seen))
    data = pack_bytes(late)
    with pytest.raises(PackFormatError, match="window"):
        read_pack(data, pack_sha256(data))


def test_the_window_end_itself_is_inside():
    data = pack_bytes(a_pack(spot=Level(25012.4, at(14, 40))))
    assert read_pack(data, pack_sha256(data)).spot.observed_at == at(14, 40)


def _edited(edit):
    body = json.loads(pack_bytes(a_pack()))
    edit(body)
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@pytest.mark.parametrize(
    "edit",
    [
        lambda b: b.update(label="system_late"),  # a system_late day has no pack
        lambda b: b.update(label="A2"),  # A2 dropped (orchestrator, 16 Oct): no fallback pack
        lambda b: b.update(chain=[]),
        lambda b: b["spot"].pop("observed_at"),
        lambda b: b["spot"].update(extra=1),
        lambda b: b["chain"][0].update(kind="XX"),
        lambda b: b["future"].update(expiry="2026-10-22"),  # e is strictly after the day
        lambda b: b["iv30"].update(flagged="no"),
        lambda b: b["spot"].update(value="25012.4"),
        lambda b: b["spot"].update(observed_at="2026-10-22T14:30:01"),  # no offset
        lambda b: b["chain"][0].update(mid=1.0),  # a mid that is not (bid + ask) / 2
        lambda b: b["spot"].update(value=25012),  # not canonical: the stored number is 25012.0
        lambda b: b.update(source=""),
    ],
)
def test_a_broken_pack_is_refused(edit):
    data = _edited(edit)
    with pytest.raises(PackFormatError):
        read_pack(data, pack_sha256(data))


def test_bytes_other_than_the_released_ones_are_refused():
    data = pack_bytes(a_pack())
    with pytest.raises(PackFormatError, match="released"):
        read_pack(data, pack_sha256(data + b" "))
    with pytest.raises(PackFormatError, match="canonical"):
        spaced = json.dumps(json.loads(data), sort_keys=True).encode()
        read_pack(spaced, pack_sha256(spaced))


def test_a_time_without_an_offset_is_never_written():
    with pytest.raises(PackFormatError):
        pack_bytes(a_pack(released_at=datetime(2026, 10, 22, 14, 32)))
