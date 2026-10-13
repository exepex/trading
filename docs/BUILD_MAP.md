# Build map: thin end-to-end slices (owner decision, 13 Oct 2026)

The order of work from 13 Oct 2026. The stories stay as written (`docs/stories/`); this file decides **when** each is
built and **which screen block** it feeds. Owner's question that led here: screens need data that only exists once
the engine runs, so how do UI and engine proceed without rework or misleading screens?

## Rules

1. **The contract is the meeting point.** Every screen block has a signed-off contract (fields, types, examples,
   publisher): W10 (frame, Home), W11 (Screener, Markets), W13 (option chain), and the mockup's `notes.md`. The UI is
   built against the contract; the engine publishes into it; every publication is validated against the schema (as P6
   does). Neither side waits for the other, and neither changes a contract alone.
2. **Three states per block, no more:** real data; empty with a reason and a date ("No forecast scored yet; first
   score on 20 Oct"); labelled Example data **in mockups only**. The real app never shows example numbers (a test per
   block: every figure traces to a published field, or the block is in its empty state).
3. **Build in slices, not layers.** A slice is a thin path from data to a real screen. It is done only when real data
   shows on the real screen and the judge has checked it end to end, not when each layer passes alone.
4. **Mockups follow the slices.** Design only what the next slice needs. Stock screens are paused with stock work.
5. **The engine stays strict.** Every rule, from a person, the rules engine or the AI team, is found on one period and
   proven on unseen years before it trades on paper. No screen hurries this.

## Slices

| # | Slice | Stories, in order | First real thing on screen | State (13 Oct 2026) |
|---|---|---|---|---|
| 0 | Data foundation | A1-A12, O6 (fetch in Actions, reason in triggered routines) | none (feeds all) | A1-A11 done except A8 (waits 20 release days); A12 and O6 with the judge; filings backfill running |
| 1 | Market data | P6 → W12 (Screener, Markets) | live market screens | P6 and W12 in re-judge |
| 2 | Forecast contest, Book 1 | G1 → G2 baselines → G3 Book 1 capture → G4 scoring → P1/P2 read model → Forecast screen (new mockup) | Rule-based forecasts against yardsticks, scored daily | G1 in fix, then ChatGPT review; rest not started |
| 2b | Forecast contest, Books 2 and 3 | F1 isolated AI book sessions → G5 AI books' capture (through O6 triggers) | Hybrid and AI team in the same screen | not started |
| 3 | Paper trading, Book 1 | B5 experiment 1 (freeze after ChatGPT agrees, response 55) → D1-D3 playbook and decision record → C3/C4 checks → E2-E6 paper desk → S1/S2 scoreboard B → F&O book screen (new mockup) | Book 1 paper trades with costs | B5 waits for ChatGPT; rest not started |
| 4 | Paper trading, Books 2 and 3 | D4/D5 envelopes → F2-F7 → S3 scoreboard A | three books trading and compared | not started |
| 5 | Operations | O1 daily routine → O2 failures → P3/P4 Azure and Slack → O3/O4 | runs by itself, alerts | not started |

Two slices are worked at once at most (owner's pace: at most 2 builders plus the judge). Slice 1 finishes first;
slice 2 starts with G2 + G3 as soon as G1 passes.

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
| new | Forecast contest screen | G4 + P1/P2 | slice 2 (mockup next) |
| new | F&O book screen (trades, P&L, risk) | E + S2 | slice 3 (mockup later) |

## Next actions

1. Mockup: the Forecast contest screen (slice 2), against G1's protocol fields.
2. G2 + G3 builder, after G1 passes the judge.
3. Write the missing stories: option-chain read model (32 and 35's F&O block), FII/DII download, India VIX history
   download, F&O news download.
4. Keep the story status lines true: each PASS updates its line the same day.
