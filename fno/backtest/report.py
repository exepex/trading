"""The backtest's plain-text report: trades, net results and how often each rule called the next 30 minutes."""

from __future__ import annotations

from .simulator import BacktestResult

DISCLAIMER = (
    "APPROXIMATION: option prices are modelled (Black-Scholes, volatility from the stock's own recent moves, "
    "about 10 days to expiry), not real quotes; no bid-ask spread beyond charges; only rules that can be judged "
    "from price history vote (no option chain, OI, news or research). Use it to compare rules, not to predict profit."
)
TRADE_ROW = "{symbol:<12} {trades:>6} {won:>5.0f}% {net:>12,.0f} {avg:>10,.0f}"
RULE_ROW = "{rule:<22} {votes:>7} {hit:>7.1f}%"


def format_report(results: dict[str, BacktestResult], days: int) -> str:
    lines = [f"Backtest over the last {days} days of 5-minute prices", "", DISCLAIMER, ""]
    lines.append(f"{'underlying':<12} {'trades':>6} {'won':>6} {'net P&L Rs':>12} {'per trade':>10}")
    total_trades, total_net, reasons, grades = 0, 0.0, {}, {}
    for symbol, result in sorted(results.items()):
        nets = [t.net_pnl for t in result.trades]
        won = 100.0 * sum(n > 0 for n in nets) / len(nets) if nets else 0.0
        avg = sum(nets) / len(nets) if nets else 0.0
        lines.append(TRADE_ROW.format(symbol=symbol, trades=len(nets), won=won, net=sum(nets), avg=avg))
        total_trades, total_net = total_trades + len(nets), total_net + sum(nets)
        for t in result.trades:
            reasons[t.exit_reason] = reasons.get(t.exit_reason, 0) + 1
        for rule, grade in result.grades.items():
            hits, votes = grades.get(rule, (0, 0))
            grades[rule] = (hits + grade.hits, votes + grade.votes)
    lines.append(f"{'all':<12} {total_trades:>6} {'':>6} {total_net:>12,.0f}")
    lines += ["", "Exits: " + (", ".join(f"{r} {n}" for r, n in sorted(reasons.items())) or "none"), ""]
    lines.append(f"{'rule':<22} {'votes':>7} {'right':>8}   (direction of the next 30 minutes; 50% = coin toss)")
    for rule, (hits, votes) in sorted(grades.items(), key=lambda kv: -kv[1][1]):
        lines.append(RULE_ROW.format(rule=rule, votes=votes, hit=100.0 * hits / votes if votes else 0.0))
    return "\n".join(lines)
