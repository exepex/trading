# Build map: thin end-to-end slices (owner decision, 13 Oct 2026)

The order of work from 13 Oct 2026. The stories stay as written (`docs/stories/`); this file decides **when** each is
built and **which screen block** it feeds. Owner's question that led here: screens need data that only exists once
the engine runs, so how do UI and engine proceed without rework or misleading screens?

## Rules

1. **The contract is the meeting point.** Every screen block has a signed-off contract: W10 (frame, Home), W11
   (Screener, Markets), W13 (option chain), reusing P1's pattern. Each contract states: schema version and
   compatibility rule; required vs nullable fields; units, currency and enums; `as_of`, cutoff, `built_at`, source and
   commit; freshness rule; machine-readable empty and error reason codes; producer; point-in-time vs latest; the
   breaking-change rule. Producer and consumer test against the same schema; CI fails if either side changes it alone.
   A mockup never becomes the contract.
2. **Runtime states:** real and fresh; real but stale or failed (last real data with `as_of` and the reason); empty
   with a reason code and an expected date. **Example** data exists only in mockups: runtime schemas have no example
   state, and the production build fails if a mockup fixture is imported. Every rendered number traces to a published
   field and its source metadata (ChatGPT review 28, accepted in response 60).
3. **Build in slices, not layers.** A slice is a thin path from data to a real screen. It is done only when real data
   shows on the real screen and the judge has checked it end to end, not when each layer passes alone.
4. **Mockups follow the slices.** Design only what the next slice needs. Stock screens are paused with stock work.
5. **The engine stays strict.** Every rule, from a person, the rules engine or the AI team, is found on one period and
   proven on unseen years before it trades on paper. No screen hurries this.

## Slices

| # | Slice | Stories, in order | First real thing on screen | State (13 Oct 2026) |
|---|---|---|---|---|
| 0 | Foundation (prerequisite, not an end-to-end slice) | A1-A12, O6 (fetch in Actions, reason in triggered routines) | none (feeds all) | A1-A11 done except A8 (waits 20 release days); A12 and O6 with the judge; filings backfill running |
| 1 | Market data | P6 → W12 (Screener, Markets) | live market screens | P6 and W12 in re-judge |
| 2 | Forecast contest, Book 1 | G1 → G2 baselines → G3 Book 1 capture → G4 scoring → P1/P2 read model → Forecast lab (37, deep dive) and the prediction section of the Strategy lab (38) | Rule-based forecasts against yardsticks, scored daily | G1 v1 and v2 frozen or freezing; G2, G3 built; live capture from 14 Oct |
| 2b | Forecast contest, Books 2 and 3 | F1 isolated AI book sessions → G5 AI books' capture (through O6 triggers) | Hybrid and AI team in the same screen | not started |
| 3 | Paper trading, Book 1 | B5 experiment 1 (freeze after ChatGPT agrees, response 55) → D1-D3 playbook and decision record → C3/C4 checks → E2-E6 paper desk → S1/S2 scoreboard B → Strategy lab (38): which family makes net profit on paper | Book 1 paper trades with costs | experiment 1 frozen, challenge run in progress; rest not started |
| 4 | Paper trading, Books 2 and 3 | D4/D5 envelopes → F2-F7 → S3 scoreboard A | three books trading and compared | not started |
| 5 | Operations | O1 daily routine → O2 failures → P3/P4 Azure and Slack → O3/O4 | runs by itself, alerts | not started |

Slices are not serialized by dependency: forecasts (slice 2) start as early as G1 allows, and Book 1 paper trading
(slice 3) starts as soon as B5, D, C and E prerequisites pass, without waiting for the AI books' forecasts. Three-book
comparisons start only when all compared books are ready. The owner's pace (at most 2 builders plus the judge) limits
how many are built at once.

## Screen blocks and what feeds them

Producer status: **live** (real data today), **slice n** (comes with that slice), **stock tool** (paused with stock
work), **gap** (no story yet).

| Screen | Block | Producer | Status |
|---|---|---|---|
| 30 frame | contracts, quotes, order window (F&O) | P5 | slice 3 (paper desk) |
| 31 Home | your paper account (Manual account) | dashboard, Manual account story | gap: Manual account not built in a backend |
| 31 Home | who trades: Rule-based, Hybrid, AI team cards | F&O: S2/S3; stock tool | slice 3-4 (F&O); stock tool |
| 31 Home | open paper trades, needs you, top pick, news, coming up | stock tool; F&O book | stock tool; slice 3 |
| 31 Home | market band | stock tool `market_status`; P6 | live (P6, India) |
| 32 option chain | header, NIFTY card, chain, OI, IV, range priced in, mood | F&O tool (A3 panel, NSE files) | read model not built: slice 1 extension (P-story needed) |
| 32 option chain | combination tray, Buy/Sell | dashboard + E paper desk | slice 3 |
| 33 screener | market tables, F&O build-up, ready-made screens | P6 | slice 1 |
| 33 screener | "our tools" columns | stock tool | stock tool |
| 34 markets | index cards, breadth, sectors, movers, fear, index options | P6 | slice 1 |
| 34 markets | big investors' flows (FII/DII) | stock tool today; F&O download planned (owner order: after filings) | gap: download story to write |
| 35 stock | prices, financials, forecast, strategies, AI team, news, costs | stock tool | stock tool (paused); data gaps in `35-stock/notes.md` |
| 35 stock | F&O block (contracts, chain, IV) | NSE F&O files | read model not built (same P-story as 32) |
| 37 Forecast lab | forecast accuracy per family (deep dive) | G4 + P1/P2 | slice 2 (mockup in review) |
| 38 Strategy lab (owner, 13 Oct: "which family makes net profit") | go-live readiness, leaderboard, equity curves with NIFTY, months, drivers, per-strategy; Stocks and F&O blocks | F&O: E + S1-S3; stocks: stock tool scoreboards | slice 3-4 (mockup in progress; real data nearly empty until paper trades settle) |

## Next actions

1. Mockups: the Forecast lab (37) and the Strategy lab (38), the owner's main decision screen.
2. G2 + G3 builder, after G1 passes the judge.
3. Write the missing stories: option-chain read model (32 and 35's F&O block); Manual paper account backend and
   read model (Home); forecast read model for G4's report fields; FII/DII download (NSE's daily FII/DII cash-market
   buy and sell values). India VIX history needs no story (the panel carries it). F&O news waits until its source,
   point-in-time rule, revision behaviour and consumer are named.
4. Keep the story status lines true: each PASS updates its line the same day.
