# Live data feeds for NSE index derivatives (research note, 23 Oct 2026)

Orchestrator research for the owner's question "should we find a live data source instead of polling every 15 minutes".
Prices as seen 22-23 Oct 2026. **O** = official page; **U** = unverified. No price is guessed.

| Source | Cost / month | Streaming, depth, limits | Notes |
|---|---|---|---|
| Groww Trade API `GrowwFeed` (owner's plan) | in the ₹499 + tax plan (O, groww.in/blog/api-trading-on-groww) | websocket, LTP and market depth for derivatives and index values (O, groww.in/trade-api/docs/python-sdk/feed); "upto 1000 subscriptions" (O, docs) vs 3,000 (blog): conflict, to test | separate from the REST 10/s, 300/min limits (to verify) |
| Upstox API v3 | free (O, upstox.com/trading-api) | full mode 5-level depth, 2,000 instruments, 2 connections (O) | backup option |
| Zerodha Kite Connect | ₹500 (O) | full mode 5 bid/5 ask, 3,000 per connection, 3 connections (O) | |
| Dhan DhanHQ | ₹499 + tax (O) | 5-level depth, 5,000 per connection, 5 connections (O) | |
| Angel One SmartAPI | free (O) | limits forum-only (U) | |
| TrueData, Global Datafeeds, Accelpix (NSE vendors) | sales quotes; NSE per-user F&O L1 fee ₹875/month on top (O, NSE price list 1 Apr 2026) | 1-second L1 best bid/ask | terms forbid "virtual trading, or simulation use" (TrueData, GDFL; O): may cover paper trading |
| NSE direct | ₹ lakhs a year | non-display F&O L1 ₹23.9 lakh/year (O) | not for individuals |

**Decision (owner, 23 Oct 2026):** buy nothing; test the Groww feed already paid for with a read-only probe from Tue
27 Oct (after v4's clean days): coverage of all four indices' near-money chains, the 1,000 vs 3,000 limit, and whether
it removes the shared-key clash at 3 pm. Adding the feed to the read-only allow-list is a lane-1 change. Open risk:
Groww's terms do not clearly allow read-only use (owner chose not to ask, 22 Oct).
