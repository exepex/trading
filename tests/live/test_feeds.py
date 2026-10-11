from fno.live.feeds.nse_feed import parse_ban_list, parse_lot_sizes, parse_oi_spurts
from fno.live.feeds.price_feed import parse_chart_candles, parse_spark, yahoo_symbol

LOTS_CSV = """UNDERLYING ,SYMBOL ,OCT-26 ,NOV-26
NIFTY 50 ,NIFTY ,65 ,65
RELIANCE INDUSTRIES ,RELIANCE ,500 ,500
Symbol ,      ,     ,
"""


def test_parse_lot_sizes():
    assert parse_lot_sizes(LOTS_CSV) == {"NIFTY": 65, "RELIANCE": 500}


def test_parse_ban_list():
    text = "Securities in Ban For Trade Date 12-OCT-2026:\n1,AMBUJACEM\n2,BANDHANBNK\n"
    assert parse_ban_list(text) == {"AMBUJACEM", "BANDHANBNK"}


def test_parse_oi_spurts():
    payload = {
        "data": [
            {"symbol": "TCS", "prevOI": 1000, "changeInOI": 80, "underlyingValue": 2156, "total": 500.0},
            {"symbol": "ZERO", "prevOI": 0, "changeInOI": 5},
        ]
    }
    moves = parse_oi_spurts(payload)
    assert set(moves) == {"TCS"}
    assert moves["TCS"].oi_change_pct == 8.0 and moves["TCS"].traded_value == 5e7


def test_yahoo_symbols():
    assert yahoo_symbol("NIFTY") == "^NSEI"
    assert yahoo_symbol("M&M") == "M&M.NS"


def test_parse_spark_and_chart():
    spark = {"SBIN.NS": {"close": [940.0, None, 959.1], "previousClose": 940.0}}
    quotes = parse_spark(spark, {"SBIN.NS": "SBIN"})
    assert quotes["SBIN"].last_price == 959.1 and quotes["SBIN"].previous_close == 940.0
    chart = {
        "chart": {
            "result": [
                {
                    "timestamp": [1791517500, 1791517800],
                    "indicators": {
                        "quote": [
                            {"open": [1, None], "high": [2, 3], "low": [0.5, 1], "close": [1.5, 2], "volume": [10, 20]}
                        ]
                    },
                }
            ]
        }
    }
    candles = parse_chart_candles(chart)
    assert len(candles) == 1 and candles[0].close == 1.5 and candles[0].start.hour == 9
