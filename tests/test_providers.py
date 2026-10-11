import json
from datetime import date
from pathlib import Path

from fno import analytics as an
from fno.providers.groww import parse_groww_chain
from fno.providers.public import infer_lot_size, parse_nse_chain

FIXTURE = Path(__file__).parent / "fixtures" / "nse_nifty_chain.json"


def test_parse_real_nse_chain():
    payload = json.loads(FIXTURE.read_text())
    chain = parse_nse_chain(payload, "NIFTY", date(2026, 10, 13), fallback_lot=75)
    assert chain.spot == 22520.45
    assert chain.lot_size == 65  # inferred from order-book quantities
    assert chain.strike_step() == 50
    q = chain.get(22750, "CE")
    assert q.bid == 31.65 and q.ask == 32.05 and q.oi == 65141
    assert an.straddle_expected_move(chain) > 0
    assert 0.3 < an.put_call_ratio(chain) < 3


def test_lot_inference_needs_enough_data():
    assert infer_lot_size([]) is None


def test_parse_groww_chain_documented_shape():
    resp = {
        "status": "SUCCESS",
        "payload": {
            "underlying_ltp": 25641.7,
            "strikes": {
                "25600": {
                    "CE": {"greeks": {"iv": 12.1}, "trading_symbol": "NIFTY25N1825600CE", "ltp": 120.5,
                           "open_interest": 900, "volume": 50},
                    "PE": {"greeks": {"iv": 12.9}, "trading_symbol": "NIFTY25N1825600PE", "ltp": 90.0,
                           "open_interest": 700, "volume": 40},
                }
            },
        },
    }
    chain = parse_groww_chain(resp, "NIFTY", date(2025, 11, 18), lot_size=75)
    assert chain.spot == 25641.7
    assert chain.get(25600, "CE").ltp == 120.5
    assert chain.get(25600, "PE").iv == 12.9
    assert not chain.get(25600, "CE").has_book
