# Desk decisions (owner)

Decisions the owner has made for the desk. Every role and both AIs work within them. Newest last.

| Date | Decision | Detail |
|---|---|---|
| 12 Oct 2026 | Shared goal | One team of expert roles; the common goal is net profitable F&O trades (after charges, slippage and tax), found from data and proven on paper |
| 12 Oct 2026 | Maximum loss per trade: **Rs 10,000** (option C) | The worst case of a single trade, including charges; for a Rs 5 lakh paper account that is 2%. Risk manager's companion rule: at most 3 trades open at once (Rs 30,000, 6% of capital at risk in total) |
| 12 Oct 2026 | Tax: **assume the 30% slab** | Measured as 31.2% (30% plus 4% health and education cess) on the year's net F&O profit; losses in the year reduce the taxable profit. The safe choice: what is profitable at 31.2% is profitable at any lower slab |
| 12 Oct 2026 | Holding period: **up to 2-3 weeks**, overnight and weekends allowed (option A) | Trades may stay open across nights and weekends; gap risk is capped by the bought protection within the Rs 10,000 maximum loss |
| 12 Oct 2026 | Decisions **once a day, around 3:00 pm** now; all-day watching later only if data shows it helps (option C) | Strategies are designed and tested on daily data; intraday monitoring is a later, separately tested layer |
| 12 Oct 2026 | Paper account: **Rs 5 lakh** (option B) | With Rs 10,000 per trade (2%) and at most 3 open trades, the worst realistic month is about -6%. Before real money this is revisited: on a Rs 2 lakh real account Rs 10,000 would be 5% a trade, too high. Config: `profiles.paper` (capital 500000, risk 2%, max_open_trades 3) |
