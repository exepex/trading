# Wave 1 judgment, round 1 (2026-10-12)

Scope: 3f012cd..119b3c7 (W1.1-W1.4). Verdict: **FAIL** (1 blocking, 4 should fix, 4 minor).
Commands: pytest 112 passed; ruff check and format clean; all files under 350 lines; trade-stats runs; services
build the iv_rank guard; NSE NIFTY 500 list confirms the "Financial Services" industry name. Probes in scratch only.

| Criterion | Result |
|---|---|
| W1.1 live quote at entry and exit; NSE book used as is | FAIL (finding 1) |
| W1.1 spread re-check on live quote | PASS (contract_picker.py:114; test_a_wide_live_spread...) |
| W1.1 fill_source recorded | PASS with defect (finding 2) |
| W1.1 tests: with book / without book + quote / unavailable | FAIL (finding 4) |
| W1.2 one iv_snapshot per underlying per day after the close | FAIL (finding 3) |
| W1.2 iv_rank 0-100, min_days, excludes today | PASS |
| W1.2 guard blocks above max_iv_rank, abstains without history | PASS |
| W1.3 families and max_per_family | PASS |
| W1.4 trade-stats by entry time, days to expiry, exit reason | PASS |

Findings
1. BLOCKING: an exception from `live_quote` (Groww network/429/token) aborts exits: stop loss not fired in
   review, `close_all` raises and leaves trades open, overnight trim raises before the journal is saved. Fix: catch
   and fall back to the chain price (FILL_LAST_PRICE) in close_value and in the picker; tests with a raising quote.
2. Should fix: `exit_fill_source` stale on the expiry (intrinsic) path and written on open trades at every mark.
   Fix: return the source from close_value, set it only when the trade is finalised; FILL_INTRINSIC at expiry.
3. Should fix: IV observations not tied to their day; a kill-switch day stores nothing and its values are later
   stored under the wrong date. Fix: keep (day, iv); write each under its own day; runner test.
4. Should fix: no test that a chain with bid/ask is used as is (no live_quote call) for picker and close_value.
5. Should fix: `scan-once` writes shadow trades (T001-T003 opened before the market opened are committed in
   journal/shadow_trades.json). Fix: scan-once without the shadow desk, or no shadow fills outside TRADING;
   remove the bad rows.
6. Minor: trade-stats ignores time zones and raises on a missing expiry.
7. Minor: IV history cache never ages out beyond lookback_days.
8. Minor: with no live quote, a Groww entry has no spread check at all.
9. Minor: README (trade-stats), SAFEGUARDS (max_per_family, iv_rank), DATA_SOURCES (Groww bid/ask) and the
   conversation log's Decisions/Open questions sections are behind the code.
