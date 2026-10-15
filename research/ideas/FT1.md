# Idea card: FT1 fill-timing study (measurement)

Template: `research/ideas/TEMPLATE.md`. FT1 is a **measurement study**, not a trade idea: it tests no edge and has no
pass mark, so the trade fields say "none". Story E8a; protocol `research/2026-10-16-fill-timing/PROTOCOL.md`.

## G0: the idea

| Field | Value |
|---|---|
| Id and version | FT1 v1 (measurement) |
| Ledger trial | 54 |
| Registered research question | How far E8's reaction-time fills move an entry price, 15:00 against 14:00 decisions |
| Proposed by (role or AI) and date | F&O trader and risk manager (response 144 plan item 3); owner decision "history now, then live", 15 Oct 2026 |
| Who pays and why | none (no trade is tested) |
| Forecast it rests on | none |
| Instrument and structure | NIFTY monthly options, nearest monthly expiry more than 7 sessions away; SF, SC, BF, LC, LP, CDS, CCS, PDS, PCS at width 200 (100 and 300 as sensitivity) |
| Entry rule | Decision at 15:00 or 14:00; fills per E8 at R = 5, 30, 60 minutes (protocol section 6) |
| Exit rule | none for `C`; held to expiry at the final settlement price for the flip share only |
| Size | 1 lot (rupee figures only) |
| Worst loss in Rs | none (no trade) |
| Expected gross per trade, with source | none (not measured) |
| Needs a reaction faster than 60 minutes? | The study measures what a 5-60 minute reaction costs |
| Frequency | About 680 decision days, 2 Jan 2024 to 30 Sep 2026 |

## G1-G6

| Field | Value |
|---|---|
| Feasibility screen | Not applicable (measurement, no trade) |
| Data spend | Groww 2024-26 NIFTY option and future 15-minute candles: `registered`, then `spent` for the decision-to-fill windows read (`research/DATA_SPEND.md`); the option prices of 2024-26 are already spent as daily closes, so every figure is **exploratory** |
| Sample plan | All eligible days of the window; cells under 30 days print "too few days" |
| Protocol file and frozen commit | `PROTOCOL.md`, commit in `FREEZE.md` |
| Code hash | In `FREEZE.md` before the full fetch |
| Test type | Historical measurement on real last trades (15-minute candle closes) |
| Pass mark | none |
| Result and verdict | Pending |
