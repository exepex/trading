# Wave 3 judgment, round 1 (2026-10-12)

Scope: 38159c1. Verdict: **FAIL** (0 blocking, 5 should fix, 6 minor). Nothing can enlarge a trade or bypass a limit.
Commands: pytest 147 passed; ruff clean; backtest NIFTY 10 days consistent (exits sum to trades); the committed
30-day report reproduced exactly (243 trades, -Rs 1,86,454); shock maths, Groww batching (50/50/21) and odd payloads
verified; no NSE/Yahoo polling every 20 s; 5-s loop adds no other network calls; no look-ahead in the backtest.

1. Should fix: `prioritise` overrides back-off, refusal pauses and intervals (a 1,800 s pause cut to 20 s), with no
   lock against the watcher thread; untested.
2. Should fix: a failing Groww sign-in is retried every 20 s all day (about 1,100 logins); needs back-off and one alert.
3. Should fix: the shock re-check can price from a chain cached up to 50 s before the shock, and it pushes the
   regular review back.
4. Should fix: the backtest re-enters on the bar it exits (8/26 NIFTY), which the desk's re-entry and post-loss
   cooldowns forbid; the quoted first-run figures include those trades; unmodelled entry filters not disclosed.
5. Should fix: backtest/cli.py wires concrete classes (view builder, exit policy with exit days hard-coded) outside
   services.py.
6. Minor: stock "ATM strike" always equals spot.
7. Minor: report omits unfinished trades, sessions, the 0.2 grading filter, unknown holidays, the 0.08 sigma floor.
8. Minor: duplicated constants (priority news sources, Groww provider name).
9. Minor: Groww index symbols unverified; missing prices silent; groww-check price call unguarded.
10. Minor: test gaps (prioritise, wiring, GrowwLivePrices batching/failure, no-look-ahead).
11. Minor: the 20-s cadence is not held while a scan runs.
