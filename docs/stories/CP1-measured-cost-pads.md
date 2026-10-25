# CP1. Measured cost pads for registered studies

**Repository:** trading · **Lane:** 1, two judges (it sets the cost every future registered study is judged at:
money, and through G1 anything that decides a trade) · **Branch:** `story/cp1-measured-pads` · **Status:** story
text, for the judges before any code.

**Intent served:** `docs/DESK_DECISIONS.md`, 25 Oct 2026, **"DOC1 approved; four third rounds; A14c merge; one-lot
searches paused; measured cost pads"**, item (5): "Future studies use measured per-bucket half-spread pads instead of
C1's flat Rs 1, as a new registered study; past results are never re-read."

**Description:** As the data and backtesting engineer and the cost accountant, I want each future registered study to
pay a slippage pad measured from our own recorded bid and ask, per bucket of underlying, moneyness, days to expiry and
in or out of the money, instead of one flat Rs 1 a unit. Then a study is neither flattered by a pad that is too small
nor killed by one that is too large.

**Why** [some evidence]: `research/edge2/SLIPPAGE_NOTE.md` (3,966 recorded 15:00 quotes, 13-23 Oct 2026). Half the
spread of NIFTY's and BANKNIFTY's near-month and weekly out-of-the-money strikes was Rs 0.03-0.65 a unit, under the flat
Rs 1. Next-month and FINNIFTY/MIDCPNIFTY next-month strikes were Rs 2-80, far over it. The flat pad is wrong in both
directions, by bucket.

## What this story owns, and what it only uses

| Functionality | Owning document | CP1's use |
|---|---|---|
| Charges (brokerage, STT, exchange, SEBI, stamp, GST) and the three ledgers | `docs/stories/C-code-roles.md`, C1 | unchanged; CP1 never touches charges |
| The flat pad (`PAD = 1.0`) and a position's fills, pads and maximum loss | `docs/stories/B-research-engine.md`, B2 (`fno/research_engine/cycle_costs.py`, frozen by experiment 1 and `research/evaluation/`) | never edited; CP1 adds a new pad source beside it |
| The half-spread of one quote and its bucket (`relative_half_spread`, `bucket_of`), the session-median weighting | `docs/stories/MS-market-school.md`, MS-SIM-b (`fno/school/simulator/spreads/`) | reused unchanged: CP1 must not build a second spread measurer |
| The verified 15:00 captures (A4, A4c, A4f) and their reader (MS-P1b `CaptureReader`) | `docs/stories/A-data-foundation.md`; `docs/stories/MS-market-school.md` (MS-P1b) | read only |
| The 15-minute NIFTY chains (A16) | `docs/stories/A16-intraday-quote-recorder.md` | read only, for studies that fill away from 15:00 |
| The factory's G1 cost wall | `docs/stories/R-factory.md`, R1 | unchanged; a card cites the pad table it used |

**This document owns:** the pad table (how it is built, versioned and frozen), the pad source a study reads, and the
rule that a measured pad never re-prices a past result.

## Expected design

1. **The pad table, a frozen, versioned record.** `fno/costs_pads/table.py` builds one table from every verified
   capture with a session strictly before a cut-off date. Each row has underlying, moneyness band, days-to-expiry band,
   side (`otm` or `itm`), time slot (15:00 for the A4 captures; A16's 15-minute slots for NIFTY), sessions counted,
   quotes counted, the median of the session medians of the half-spread (Rs a unit) and its 75th percentile. Bands are
   MS-SIM-b's (moneyness under 1%, 1-2%, 2-4%, 4% and more; 0-7, 8-21, 22-45, 46+ days). Side is new: a call at or
   above spot, or a put at or below it, is `otm`.
2. **Where it lives.** The table is a data file, written once to Drive with a SHA-256 receipt in GitHub (O9). Its
   version is the SHA-256 plus the cut-off date and the code commit. Building twice from the same inputs gives
   byte-identical files (a test).
3. **The 30-session rule.** A bucket with fewer than 30 recorded sessions has no measured pad. Its pad is the larger of
   the flat Rs 1 and the bucket's 75th percentile so far, and the table marks it `provisional`. [reasoning only: 30 is
   MS-SIM-b's own minimum. A thin bucket never makes a study look cheaper than today's rule.]
4. **The pad a study reads.** An interface `PadSource.pad(underlying, strike, spot, expiry, kind, session, slot) ->
   float` (Rs a unit) has two classes:
   - `FlatPad`: the Rs 1 of B2, unchanged.
   - `MeasuredPad(table)`: the bucket's median, or the provisional value.

   A new `PaddedPositionCosts`, beside B2's frozen `PositionCosts` (never a subclass that changes its behaviour), takes a
   `PadSource` per leg. Wired only in a composition root.
5. **Registration names the table.** A study that uses measured pads names the table's version in its protocol and its
   idea card before any result. The ledger guard's frozen-protocol check then covers the table too (the card names a
   SHA-256 that must match the Drive receipt).
6. **Past results are never re-read** (owner). `MeasuredPad` refuses to price any trial whose ledger row was
   registered before the table version's cut-off date or names no table: it raises `PadTableNotRegistered`, by name.
7. **A stress column.** Each study reports its result at the table's 75th percentile beside the median, as EDGE1 and
   EDGE2 reported the Rs 2 pad beside the Rs 1. The decided figure is the median.

## Acceptance criteria

1. **Build.** Given verified captures for N sessions, the table has one row per (underlying, band, band, side, slot)
   seen, with sessions, quotes, median of session medians and 75th percentile. Tested on fakes:
   - good: two sessions of known spreads give the hand-computed medians;
   - bad: a capture whose SHA-256 fails its sidecar is skipped and listed, never read;
   - boundary: a quote exactly at spot is `otm`, for both a call and a put;
   - empty: no captures give an empty table and a named "no sessions" line.
2. **Reuse, not a copy.** The half-spread and the bucket come from MS-SIM-b's `relative_half_spread` and `bucket_of`
   (an import test, and a test that a changed tick floor in MS-SIM-b changes CP1's table).
3. **Point in time.** The table built with cut-off D reads no capture dated on or after D. Tested with a planted
   capture on D.
4. **The 30-session rule.** A bucket with 29 sessions is `provisional`, priced at max(Rs 1, its 75th percentile); with 30
   sessions it is measured at its median. Boundary tests on both.
5. **Deterministic.** Two builds from the same inputs are byte-identical; the version changes when one input changes.
6. **Frozen code untouched.** `fno/research_engine/cycle_costs.py` and every file a freeze names are unchanged by the
   branch (the freeze tests pass unchanged). `PaddedPositionCosts` with `FlatPad` reproduces `PositionCosts`' pads,
   fills and maximum loss to the paisa on EDGE1's and EDGE2's fixtures.
7. **No re-reading.** `MeasuredPad` refuses a trial registered before its table's cut-off, or one whose card names no
   table, or a different table SHA-256, each with its own named error. Tested on planted ledger rows.
8. **Records.** The table goes to Drive write-once with its receipt; a second write of a different file under the same
   version is refused (O9's store). No value is posted to Slack.
9. **Sizes.** Every new file is under 350 lines and this document under 500.

## Gap list

| Requirement | Where |
|---|---|
| Per-bucket half-spread pads (underlying, moneyness, days to expiry) | design 1, criterion 1 |
| From A16 and the 3 pm bid/ask records | design 1 (A4, A4c, A4f at 15:00; A16's slots for NIFTY) |
| Past results never re-read | design 6, criterion 7 |
| A new registered study | design 5 (a study names its table) |
| Two judges | lane line |
| Under 500 lines; link, not restate | this document's tables |

**Out of scope, with the reason:**
- Changing C1's charges or the factory's G1 formula: owned elsewhere; G1 uses whatever cost the card states.
- Pads for more than one lot, i.e. walking the book. The recorded size at the touch is about 1 lot (the note), so a
  larger order needs depth this table does not hold. It is stated as a limit, and a later story.
- Event-day spreads. The table holds whatever sessions were recorded; a calm sample understates event days, so every
  study states the table's date range. An event-day multiplier needs recorded event days first.
- The desk's and the school's live fill pads (E4, MS-P1d). They fill at recorded quotes, not a modelled pad.
- Stock options. No recorded stock-option chain exists yet.

## Open questions for the owner (recommendation first)

1. **When does a bucket become measured?** At 30 recorded sessions (recommended; MS-SIM-b's rule). If no session is
   missed, NIFTY's monthly reaches it on 27 Nov 2026, the other monthlies on 2 Dec and NIFTY's weekly on 4 Dec. The
   alternative is 20 sessions (sooner, noisier).
2. **The decided pad: the median or the 75th percentile?** The median (recommended: it is what a patient order
   typically pays), with the 75th percentile always reported beside it.
3. **Closes versus quotes.** The studies fill at NSE's closing prices, while the table measures the 15:00 quote. Use
   the 15:00 bucket for close-to-close studies (recommended, stated as a limit), or wait for a measurement of the gap
   between the close and the 15:30 quote (no recorder runs at 15:30 today).

## Depends

MS-SIM-b (merged; read-only reuse, its owner session out of reach as of 25 Oct, orchestrator agreed); A4, A4c, A4f and
A16 (recording); O9 (Drive store and receipts). **Size:** M.
