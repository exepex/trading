from fno.live.learning.trade_stats import entry_bucket, expiry_bucket, format_trade_stats, trade_stats


def trade(opened_at, pnl, expiry="2026-10-20", reason="target"):
    return {"status": "closed", "opened_at": opened_at, "expiry": expiry, "pnl_net": pnl, "exit_reason": reason}


def test_buckets():
    assert entry_bucket("2026-10-13T09:20:00+05:30") == "09:15-10:30 opening"
    assert entry_bucket("2026-10-13T12:45:00+05:30") == "12:00-13:30 midday"
    assert entry_bucket("2026-10-13T14:00:00+05:30") == "13:30-15:30 afternoon"
    assert expiry_bucket("2026-10-13T10:00:00+05:30", "2026-10-15") == "0-4 days to expiry"
    assert expiry_bucket("2026-10-13T10:00:00+05:30", "2026-10-27") == "10+ days to expiry"
    assert entry_bucket("2026-10-13T04:00:00+00:00") == "09:15-10:30 opening"  # 09:30 IST
    assert expiry_bucket("2026-10-13T10:00:00+05:30", None) == "unknown"


def test_groups_count_wins_and_net_pnl():
    trades = [
        trade("2026-10-13T09:30:00+05:30", 1200),
        trade("2026-10-13T09:50:00+05:30", -800, reason="stop loss"),
        trade("2026-10-13T12:10:00+05:30", -500, reason="stop loss"),
        {"status": "open", "opened_at": "2026-10-13T13:00:00+05:30"},
    ]
    stats = trade_stats(trades)
    opening = next(g for g in stats["By time of entry"] if g.label.startswith("09:15"))
    assert (opening.trades, opening.win_rate_pct, opening.net_pnl, opening.per_trade) == (2, 50.0, 400.0, 200.0)
    stops = next(g for g in stats["By exit reason"] if g.label == "stop loss")
    assert stops.trades == 2 and stops.net_pnl == -1300
    assert "By days to expiry at entry" in format_trade_stats(stats)
    assert format_trade_stats(trade_stats([])) == "No closed trades yet."
