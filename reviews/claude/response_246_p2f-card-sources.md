# Response 246: P2f, the card page: not built, and why (its sources mapped)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (P2 page builder), 16 Oct 2026. The last P2 page before the owner's pause on
UI work (DESK_DECISIONS row 238). **Recommendation (some evidence: the code and the one committed delivery): do not
build P2f now.** An honest card page needs changes outside P2, in T1 and the contract, which are new work, not work in
progress. Every point below is from the code at main, file:line.

## What T1 records today

- **The public delivery record** (`research/cards/deliveries/<YYYY>/<d>-a<n>.json`, `card_delivery/v1`): day, status,
  reason_code, test, missing, previous_misses, records_used (hashes), Slack's server time and whether it was sent.
  Only one exists: the 15 Oct **test** post. No real card is committed yet.
- **The full card record** (`card_record/v1`, Drive `cards/<YYYY>/<MM>/...json`): the same facts plus the Slack text
  as lines. It holds **no structured trade, weather, forecast, evidence or advocate field**, and **no code reads it
  back** (`CardRecordStore` has `save` only; fno/cards/record_store.py:18-21).
- `CardBuilder.build` always gives NO TRADE: "v1 has no trade fields (slice B)" (fno/cards/card.py:76).

## Why even today's NO TRADE card cannot be built honestly

`FnoCard` requires fields that have no source:

| Required field | Source today |
|---|---|
| `timing.market_data_cutoff` | none (the G3 pack has a `cutoff`, but T1 does not read or record it) |
| `timing.decision_finalized_at` | none (only a display deadline in fno/cards/rule_checks.py:32) |
| `data_checks.passed` | none: only implied by the reason `data_check_failed`; "true" would be invented |
| `data_checks.missing_inputs` | none: T1's gaps are plain strings, not `{input, story, detail}` |
| `paper_trades_so_far` | Drive text lines only (counts from Drive-only accounts); T1 can say "at least N" or "unknown", the contract needs integers |
| `advocate`, `evidence`, `price_of_staying_out` | none (T3, D6 rungs and E8 are not built) |
| `stress` (owner) | none: C5's stress line is not wired into any job, and it has five scenarios per book (iv factors) against the contract's three pairs (VIX moves) for all books |

**Contract mismatches T1 already emits:**
- `reason_code` `trade_fields_not_built` (a version at paper) and `hard_rule_breach` (C4) are not in the contract's
  reason enum, so on those days the page would fail validation.
- T1 has no `retrying` delivery state.

**The trade itself (TRADE and WATCH cards):** every `FnoCardTrade` field has no source in T1. The nearest records are
D3's decision record (`trade.legs`, `trade.max_loss_rs`) and C2's verdict (`numbers.max_loss_rs`, `limit_rs`).

## What a buildable P2f needs (for after the owner's review)

1. **T1** records, in its public delivery record:
   - the pack's cutoff;
   - the decision's final time;
   - the data-check result with named inputs;
   - integer trade counts per book.
   Story T1, its builder.
2. **The contract** aligns the reason enum with T1's codes, or T1 maps them (the screens lead and T1's builder agree).
3. **T1 slice B**, the trade fields: then P2f's over-cap hold (P11, judge 233) has something to check.
4. C5's stress line wired, if the owner wants it on the card.

Until then the card screen (W3f) has its contract example only, and no publish fills it.

## The roles

- **Risk manager (reasoning only):** a card page with invented "passed" checks or guessed counts would look
  trustworthy and not be. A missing page is the honest state.
- **Portfolio manager (reasoning only):** today's card is NO TRADE (no strategy at paper; `playbook/registry.csv`
  holds one research row). The owner loses nothing by its absence on the dashboard: Slack #fno-desk carries the card
  each session.
