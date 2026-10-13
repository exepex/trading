# The stock tool's followed India companies (W11 input FollowedCompaniesIndia; story P6)

One file per list, `<as_of>.json` (`{"as_of": "YYYY-MM-DD", "companies": [NSE symbols]}`), read by
`fno/market_read_models/followed.py`: a close uses the latest list dated on or before it, to tag its NSE rows "ours"
and count the "ours" universe (orchestrator decision of 13 Oct 2026, dashboard judge 40).

| File | Source |
|---|---|
| `2026-10-12.json` | the stock tool's records of 12 Oct 2026 (its 20 India companies), as fetched for the dashboard's W11 examples (`exepex/omenix-dashboard` `design/mockups/33-screener/source/tracked.json`, commit 348fe34) |

When the stock tool publishes its list (read model `followed_companies`, K5-proposed), a second adapter behind
`FollowedCompaniesSource` reads it and these files stop growing. A list is never edited after a close has used it.
