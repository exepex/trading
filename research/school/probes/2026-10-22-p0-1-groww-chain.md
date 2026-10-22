# P0 probe 1: Groww option-chain fields and rate-limit types

Market school stage P0 (response 327, section 4). Builder session session_01G5EqV95Wi7yHJ5Hgy2giaY, 22 Oct 2026.
Labels: **strong evidence** (a measured run, a file and line, or Groww's own page quoted), **some evidence**,
**reasoning only**.

## Answer

1. **Groww's option chain has no bid, no ask and no sizes.** Each leg carries only `trading_symbol`, `ltp`,
   `open_interest`, `volume` and `greeks` (`delta`, `gamma`, `iv`, `rho`, `theta`, `vega`). The chain's top level is only
   `strikes` and `underlying_ltp`: **no timestamp** and **no lot size**. Same shape for NIFTY (index) and RELIANCE
   (stock). **[strong evidence: measured run below]**
2. **Bid, ask and sizes come only from `get_quote`, one call per leg.** It returns `bid_price`, `bid_quantity`,
   `offer_price`, `offer_quantity`, a five-level `depth` (`buy`, `sell`: `price`, `quantity`, `orderCount`) and
   `last_trade_time`. **[strong evidence: measured run]**
3. **Consequence for the school:** a two-sided stock-option snapshot from Groww costs **one chain call plus one quote
   call per leg wanted**. 200 stocks x 4 slots x (1 chain + 4 legs) = **4,000 calls a day**, not 800. One slot is 1,000
   calls: 3.3 minutes of Groww's whole Live Data budget (300 a minute, item 4), on a key shared with A16, A4 and A22.
   **[strong evidence for the call count from the fields; reasoning only for the budget]**
4. **Rate-limit types (Groww's own page):** "The rate limits are applied at the type level, not on individual APIs ...
   all APIs grouped under a type (e.g., Orders, Live Data, Non Trading) share the same limit." Live Data = "Market
   Quote, LTP, OHLC": **10 a second and 300 a minute, shared.** So **LTP, OHLC and Quote are one budget, not three**.
   **[strong evidence: https://groww.in/trade-api/docs/curl, "Rate Limits", fetched 22 Oct 2026]** The option chain is
   **not in the table** (it came later, SDK 1.3.0, 24 Nov 2025). That it counts against Live Data is **reasoning only**
   (it is documented on the Live Data page); unverified.
5. No rate-limit headers are sent back: the answers carry Cloudflare and Envoy headers only (`CF-RAY`, `via`,
   `x-envoy-upstream-service-time`, ...), no `X-RateLimit-*` or `Retry-After`. The remaining budget cannot be read; it
   can only be measured by 429s. **[strong evidence: measured run]**

## The measured run

- When: 22 Oct 2026, 20:14:18-20:14:24 IST (outside 08:36-09:15 and 14:30-15:45; the script refused to run inside
  them). Market closed, so bid and ask are empty in the quote (expected after hours; their **presence** as fields is
  what was tested).
- How: the repository's `GrowwProvider` behind `ReadOnlyGroww` (`fno/intraday/read_only.py:13`, read calls only),
  with `requests.get` wrapped to log path, status, time and response headers (never request headers).
- Calls (8 HTTP requests; the SDK makes one `/changelog` call when it is built):

| # | Path | Status | Seconds | Note |
|---|---|---|---|---|
| 1 | `/v1/changelog` | 200 | 0.55 | SDK start-up |
| 2-3 | `/v1/historical/expiries` NIFTY 2026, 2027 | 200, 400 | 1.12, 0.58 | 2027 refused ("Year cannot be in the future"; `fno/providers/groww.py:121` already expects it) |
| 4 | `/v1/option-chain/exchange/NSE/underlying/NIFTY` (27 Oct expiry) | 200 | 1.25 | 261 strikes, 97 KB |
| 5-6 | `/v1/historical/expiries` RELIANCE 2026, 2027 | 200, 400 | 0.60, 0.78 | |
| 7 | `/v1/option-chain/exchange/NSE/underlying/RELIANCE` (nearest expiry) | 200 | 0.84 | 97 strikes, 36 KB |
| 8 | `/v1/live-data/quote` (one RELIANCE option leg) | 200 | 0.85 | 1.2 KB |

- Raw answers: the session scratchpad only (not committed, not in Drive). This note lists field names only.

### Fields

**Chain** (`get_option_chain`, path `/option-chain/...`):
- top level: `strikes`, `underlying_ltp`;
- `strikes[<strike>]`: `CE`, `PE`;
- each leg: `trading_symbol`, `ltp`, `open_interest`, `volume`, `greeks` {`delta`, `gamma`, `iv`, `rho`, `theta`,
  `vega`}.

**Quote** (`get_quote`, path `/live-data/quote`): `average_price`, `bid_price`, `bid_quantity`, `day_change`,
`day_change_perc`, `depth` {`buy`, `sell`: 5 levels of `price`, `quantity`, `orderCount`}, `high_trade_range`,
`implied_volatility`, `last_price`, `last_trade_quantity`, `last_trade_time` (epoch seconds), `low_trade_range`,
`lower_circuit_limit`, `market_cap`, `offer_price`, `offer_quantity`, `ohlc` {`open`, `high`, `low`, `close`},
`oi_day_change`, `oi_day_change_percentage`, `open_interest`, `previous_open_interest`, `total_buy_quantity`,
`total_sell_quantity`, `upper_circuit_limit`, `volume`, `week_52_high`, `week_52_low`.

After hours `bid_price`, `bid_quantity`, `offer_price`, `offer_quantity`, `implied_volatility` were null and depth
level 1 was price 0, quantity 0. The repository's recorders already read these fields in market hours
(`fno/providers/groww_check.py:31-33`, `fno/providers/groww.py:174-179`). **[strong evidence]**

### Provenance gaps for P0b's record fields (response 327, P0b)

- **Source time:** the chain has none. A chain row's time can only be our first-seen time; `last_trade_time` exists per
  leg only in `get_quote`. The sampled leg's last trade was 29 Sep 2026: a quote's price can be weeks old, so the
  "time-bound" check must use `last_trade_time`, not the call time. **[strong evidence]**
- **Lot size:** not in the chain or the quote. It must come from `get_contracts` or NSE's lot file, dated. **[strong
  evidence for the absence]**

## Endpoints and budgets in the SDK (growwapi 1.5.0)

`/usr/local/lib/python3.13/dist-packages/growwapi/groww/client.py` (the installed SDK):
- `get_quote` -> `/live-data/quote` (line 366), one instrument;
- `get_ltp` -> `/live-data/ltp` (line 402), a list of `exchange_symbols`;
- `get_ohlc` -> `/live-data/ohlc` (line 433), a list;
- `get_greeks` -> `/live-data/greeks/...` (line 463);
- `get_option_chain` -> `/option-chain/exchange/{exchange}/underlying/{underlying}` (line 490): a different path
  family from `/live-data/`.
- The SDK raises `GrowwAPIRateLimitException` on HTTP 429 (line 37) and has no client-side limiter.

`get_ltp` and `get_ohlc` are **not** on the read-only allow-list (`fno/intraday/read_only.py:13`), so they were not
called. An LTP batch every 15 minutes needs `get_ltp` added to the allow-list first: a lane-1 change (Groww is an
outside service).

## What the repository has already measured (strong evidence: files)

- 5 requests a second with 4 workers: no errors; failures began near 10 a second (`fno/intraday/pacing.py:1-2`).
- Two recorders on one key on 16 Oct lost 74-87 of about 224 quotes each mark to 429s; one recorder lost none
  (`fno/intraday/claims.py:1-2`).
- The 15:01 index recorder runs at 2.5 a second so that, with A16's 5, the key stays under about 10
  (`fno/quotes/indices.py:24`).

## Groww's published limits and what they mean for us

Rate table (https://groww.in/trade-api/docs/curl, section "Rate Limits", fetched 22 Oct 2026) **[strong evidence]**:

| Type | Requests | Per second | Per minute |
|---|---|---|---|
| Authentication | Generate access token | 5 | 30 |
| Orders | Create, Modify and Cancel Order | 10 | 250 |
| Live Data | Market Quote, LTP, OHLC | 10 | 300 |
| Non Trading | Order Status, Order list, Trade list, Positions, Holdings, Margin | 20 | 500 |

Also quoted: "The /v1/token/api/access endpoint is also subject to a limit of 150 requests per 24 hours." LTP and OHLC:
"Upto 50 instruments are supported for each api call." Whether the limits are per key or per user is not stated.

**What it means [reasoning only, arithmetic on the table]:**
- **300 a minute is 5 a second sustained.** A16 already paces at 5 a second (`fno/intraday/groww_source.py:26`), so
  during an A16 mark the Live Data budget is fully used. The 16 Oct 429s (two takers, about 10 a second) fit both
  caps. Any school capture must run **between** A16's marks and outside A4 (14:55-15:13) and A22 (08:40-09:11),
  under one shared pacer, or it costs the existing recorders quotes.
- **An LTP batch every 15 minutes is cheap:** 200 stocks = 4 calls of 50. Needs `get_ltp` on the allow-list (lane 1).
- **Stock-option chains with two-sided quotes are expensive:** per slot 200 chain calls plus 800 leg quotes = 1,000
  calls = **3.3 minutes of the whole Live Data minute budget**, if the chain counts there. Four slots a day fit in
  calendar time, but each slot needs a 4-minute window with no A16 mark in it. Chains alone (LTP only, no bid/ask) are
  200 calls a slot, 40 seconds.
- Without bid and ask, a stock-option chain cannot pass P1's "two-sided" validity rule. Chains give the survey (which
  strikes trade, OI, volume), quotes give the fill test.

## Not verified

- Whether the chain and quote counters are separate in practice: not measured (that needs a paced test in market hours
  with deliberate 429s, which would cost the recorders quotes; not done). P0b measures it on a small list outside the
  recorder windows.
- Whether Groww allows a second API key per user (owner decision 5 in response 327).
