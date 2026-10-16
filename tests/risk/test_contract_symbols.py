"""Story C5d: a contract's underlying in either provider's ID format. The desk's captures take `quotes.provider: auto`
(Groww, else NSE), so C5's bucket map in C2 and C4's own caps must read NSE's option-chain identifiers as they read
Groww's: before this, `OPTIDXNIFTY...` was underlying "OPTIDXNIFTY" and every trade on NSE quotes was refused."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fno.checks.validity_caps import buckets_of
from fno.config import load_app_config
from fno.constants import BUCKET_SHORT_VOL, RISK_PROFILE_BOOKS
from fno.contract_symbols import underlying_of
from fno.risk.buckets import Bucket, StructureBuckets
from fno.risk.profile_settings import profile_settings

from .builders import FLY

FIXTURE = Path(__file__).parents[1] / "fixtures" / "nse_nifty_chain.json"  # NSE's own option-chain answer
SIDES = profile_settings(load_app_config(), RISK_PROFILE_BOOKS).bucket_sides


def nse_identifiers() -> list[str]:
    found = []

    def walk(node):
        if isinstance(node, dict):
            found.extend(v for k, v in node.items() if k == "identifier" and isinstance(v, str))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(json.loads(FIXTURE.read_text(encoding="utf-8")))
    return found


def test_the_fixture_holds_real_nse_identifiers():
    ids = nse_identifiers()
    assert len(ids) >= 4 and "OPTIDXNIFTY13-10-2026CE21950.00" in ids


@pytest.mark.parametrize(
    ("symbol", "underlying"),
    [
        ("OPTIDXNIFTY13-10-2026CE21950.00", "NIFTY"),  # NSE's option chain (the fixture above)
        ("OPTIDXBANKNIFTY28-10-2026PE52000.00", "BANKNIFTY"),
        ("OPTSTKRELIANCE28-10-2026CE3000.00", "RELIANCE"),
        ("NIFTY26OCT25000CE", "NIFTY"),  # Groww's trading symbol
        ("BANKNIFTY26O2852000PE", "BANKNIFTY"),
        ("M&M26OCT3000CE", "M&M"),
    ],
)
def test_both_providers_ids_give_the_underlying(symbol, underlying):
    assert underlying_of(symbol) == underlying


def test_every_real_nse_identifier_is_nifty():
    assert {underlying_of(i) for i in nse_identifiers()} == {"NIFTY"}


def test_c5_buckets_an_nse_position_and_mixes_it_with_a_groww_one():
    nse = nse_identifiers()[:4]
    assert StructureBuckets(SIDES).buckets_of(FLY, nse) == (Bucket("NIFTY", BUCKET_SHORT_VOL),)
    mixed = [nse[0], "NIFTY26OCT25000CE"]  # one leg captured from each provider: still one underlying
    assert StructureBuckets(SIDES).buckets_of(FLY, mixed) == (Bucket("NIFTY", BUCKET_SHORT_VOL),)


def test_c4_buckets_an_nse_position_the_same_way():
    assert buckets_of(FLY, nse_identifiers()[:4], SIDES) == (("NIFTY", BUCKET_SHORT_VOL),)
