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
| The half-spread of one quote and its bucket (`relative_half_spread`, `bucket_of`), the session-median weighting, `percentile`, `TICK`, `MIN_QUOTED_SESSIONS` | `docs/stories/MS-market-school.md`, MS-SIM-b (`fno/school/simulator/spreads/`) | reused unchanged: CP1 must not build a second spread measurer |
| The verified 15:00 captures (A4, A4c, A4f) and their reader (MS-P1b `CaptureReader`) | `docs/stories/A-data-foundation.md`; `docs/stories/MS-market-school.md` (MS-P1b) | read only |
| The factory's G1 cost wall | `docs/stories/R-factory.md`, R1 | unchanged; a card cites the pad table it used |

**This document owns:** the pad table (how it is built, versioned and frozen), the pad source a study reads, and the
rule that a measured pad never re-prices a past result.

## Expected design

1. **The unit: a share of the leg's own price** [some evidence]. The table holds MS-SIM-b's relative half-spread
   (`relative_half_spread`: half the gap over the mid, the half floored at half a tick). A leg pays the bucket's
   relative value × that leg's own fill price in the study, never a rupee figure from another strike. Evidence:
   leave-one-session-out on the note's 3,768 two-sided quotes (13-23 Oct 2026), predicting each quote's rupee
   half-spread from the other sessions. The median absolute error is Rs 0.113 against Rs 0.137 for a rupee median on
   out-of-the-money strikes, and Rs 2.46 against Rs 2.92 on in-the-money strikes. Inside one bucket, rupee
   half-spreads vary with the premium (the note's in-the-money medians run Rs 1-80); the share of the price varies less.
   Limit: the check used each quote's own mid, while a study fills at its own price (the close), so Q3 still applies.
   A modelled pad is never below half a tick (MS-SIM-b's `TICK`, imported, not copied).
2. **The pad table, a frozen record.** `fno/costs_pads/table.py` builds one table from every verified 15:00 capture
   (A4, A4c, A4f, read through MS-P1b's `CaptureReader`) with a session strictly before a cut-off date. One row per
   MS-SIM-b bucket (`bucket_of`; bands in `fno/school/simulator/spreads/bucket.py`) × side, with sessions and quotes
   counted, and the median and 75th percentile across session medians (MS-SIM-b's session-median rule and its
   `percentile`). Side is new: a call at or above spot, or a put at or below it, is `otm`; any other strike is `itm`.
   **Why not MS-SIM-b's `SpreadLearner` and `SpreadModel` as they are:** their bucket has no side and is frozen with
   the practice card. Beyond 1% from the money, in-the-money legs paid a larger share than out-of-the-money ones in 26
   of 33 buckets (median ratio 1.5, range 0.25-4; BANKNIFTY 2-4%, 8-21 days: 0.91% against 0.27% of the mid). The
   side split cuts the mean out-of-sample error by 8% (the median by 6%) [some evidence: two calm weeks]. A study also needs a frozen, receipted file. CP1 adds only the side key and the file; it reuses every
   measuring function.
3. **Where it lives.** The table is a data file, written once to Drive with a SHA-256 receipt in GitHub (O9). Its
   version is the SHA-256 plus the cut-off date and the code commit. Building twice from the same inputs gives
   byte-identical files (a test).
4. **The 30-session rule.** A bucket with fewer than 30 recorded sessions (MS-SIM-b's `MIN_QUOTED_SESSIONS`) is
   `provisional`. It pays the larger of the flat Rs 1 and its 75th percentile × the leg's price. [reasoning only: a
   thin bucket never makes a study look cheaper than today's rule]
5. **The pad a study reads.** An interface `PadSource.pad(underlying, strike, spot, expiry, kind, session, price) ->
   float` (Rs a unit) has two classes:
   - `FlatPad`: the Rs 1 of B2, unchanged; it ignores the price.
   - `MeasuredPad`: the bucket's median × price, or the provisional value.

   A new `PaddedPositionCosts`, beside B2's frozen `PositionCosts` (never a subclass that changes its behaviour), takes
   a `PadSource` and passes each leg's own fill price.
6. **One `MeasuredPad` per trial, refusing at construction** (owner: "past results are never re-read"). Only the
   composition root `fno/costs_pads/wiring.py` builds a `MeasuredPad`, from the trial's committed ledger row
   (`fno/research_engine/ledger.py`), its idea card and the table loaded from Drive. It has no constructor without a
   trial. It raises, each by name:
   - `PadTableNotNamed`: the card names no table;
   - `PadTableMismatch`: the SHA-256 the card names is not the loaded table's, or the Drive receipt does not match the
     file read;
   - `PadTableNotRegistered`: the ledger row's `registered_on` is before the table's cut-off date.

   This check is CP1's own code. The ledger guard (`Ledger.require_registered`) only checks that the protocol file is
   unchanged since its commit, which stops a card from naming a table after the fact.
7. **A stress column.** Each study reports its result at the 75th percentile beside the median, as EDGE1 and EDGE2
   reported the Rs 2 pad beside the Rs 1. The decided figure is the median (Q2).

## Acceptance criteria

1. **Build.** Given verified captures for N sessions, the table has one row per (underlying, moneyness, days to expiry,
   side) seen, with sessions, quotes, and the median and 75th percentile across session medians. Tested on fakes:
   - good: two sessions of known spreads give the hand-computed values;
   - bad: a capture whose SHA-256 fails its sidecar is skipped and listed, never read;
   - boundary: a quote exactly at spot is `otm`, for both a call and a put;
   - empty: no captures give an empty table and a named "no sessions" line.
2. **The unit.** A fake leg of price P in a bucket of median relative r pays max(r × P, half a tick). A test plants
   the relative value used as rupees and must fail. A recorded check (in the claims; it reads Drive, so it is not a CI
   test): on the note's captures, relative × mid per quote reproduces the note's published rupee medians (e.g. NIFTY
   monthly, under 1%, 0-7 days: Rs 0.12). EDGE2's `slippage.py` now gets rupees the same way: its second copy of the
   tick floor is removed (branch `story/edge2-slippage-floor`; `summary.json` unchanged to 1e-15).
3. **Reuse, not a copy.** The half-spread, the bucket, the percentile, the tick and the 30-session minimum come from
   MS-SIM-b (an import test, and a test that a changed tick floor in MS-SIM-b changes CP1's table).
4. **Point in time.** The table built with cut-off D reads no capture dated on or after D. Tested with a planted
   capture on D.
5. **The 30-session rule.** A bucket with 29 sessions is `provisional`, priced at max(Rs 1, its 75th percentile × price);
   with 30 sessions it is measured at its median. Boundary tests on both, and a plant pricing a 29-session bucket at
   its median.
6. **Deterministic.** Two builds from the same inputs are byte-identical; the version changes when one input changes.
7. **Frozen code untouched.** `fno/research_engine/cycle_costs.py` and every file a freeze names are unchanged by the
   branch (the freeze tests pass unchanged). `PaddedPositionCosts` with `FlatPad` reproduces `PositionCosts`' pads,
   fills and maximum loss to the paisa on EDGE1's and EDGE2's fixtures (plant: one paisa off fails).
8. **No re-reading.** Each of design 6's three errors is raised on its own planted ledger row and card. A plant
   builds a `MeasuredPad` with no trial and must fail to construct.
9. **Records.** The table goes to Drive write-once with its receipt; a second write of a different file under the same
   version is refused (O9's store). No value is posted to Slack.
10. **Sizes.** Every new file is under 350 lines and this document under 500.

## Gap list

| Requirement | Where |
|---|---|
| Per-bucket half-spread pads (underlying, moneyness, days to expiry) | design 1-2, criteria 1-2 |
| From our recorded bid and ask | design 2 (A4, A4c, A4f at 15:00) |
| Past results never re-read | design 6, criterion 8 |
| A new registered study | design 6 (a trial's card names its table) |
| Two judges | lane line |
| Under 500 lines; link, not restate | this document's tables |

**Out of scope, with the reason:**
- Changing C1's charges or the factory's G1 formula: owned elsewhere; G1 uses whatever cost the card states.
- A16's 15-minute chains. No reader returns their bid and ask as `SlotQuote`s today (`CaptureReader` reads the 15:00
  captures only), so the table has one slot, 15:00. A later story, once such a reader exists.
- Pads for more than one lot, i.e. walking the book. The recorded size at the touch is about 1 lot (the note), so a
  larger order needs depth this table does not hold. It is stated as a limit, and a later story.
- Event-day spreads. The table holds whatever sessions were recorded; a calm sample understates event days, so every
  study states the table's date range. An event-day multiplier needs recorded event days first.
- The desk's and the school's live fill pads (E4, MS-P1d). They fill at recorded quotes, not a modelled pad.
- Stock options. No recorded stock-option chain exists yet.

## Open questions for the owner (recommendation first)

1. **When does a bucket become measured?** At 30 recorded sessions (recommended; MS-SIM-b's rule). A road's two
   monthlies sit in only one or two days-to-expiry bands a session, so the bands fill at different speeds. Expected
   30th session [reasoning only: NSE's calendar, monthly expiries on the last Tuesday and NIFTY's weeklies, no capture
   missed, each moneyness band and side quoted daily; 2027's holidays are not in the calendar yet, so 2027 dates may
   move by a few days; FINNIFTY's and MIDCPNIFTY's next-month quotes are often not two-sided, so theirs come later]:

   | Days to expiry | NIFTY (monthly and weekly) | BANKNIFTY, FINNIFTY, MIDCPNIFTY |
   |---|---|---|
   | 0-7 | 3 Dec 2026 | 24 Mar 2027 |
   | 8-21 | 30 Nov 2026 | 18 Jan 2027 |
   | 22-45 | 16 Dec 2026 | 21 Dec 2026 |
   | 46+ | 5 Jan 2027 | 5 Jan 2027 |

   Until then a bucket is provisional and pays at least Rs 1, so most buckets outside NIFTY stay at today's cost or
   higher into 2027. The alternative is 20 sessions (sooner, noisier).
2. **The decided pad: the median or the 75th percentile?** The median (recommended: it is what a patient order
   typically pays), with the 75th percentile always reported beside it.
3. **Closes versus quotes.** The studies fill at NSE's closing prices, while the table measures the 15:00 quote. Use
   the 15:00 bucket for close-to-close studies (recommended, stated as a limit), or wait for a measurement of the gap
   between the close and the 15:30 quote (no recorder runs at 15:30 today).
4. **Trades before the table's first session.** A backtest of 2019-2025 would otherwise pay spreads measured in a calm
   fortnight of 2026, which can flatter it. Recommended: any trade dated before the table's first session pays
   max(flat Rs 1, measured). Then measured pads never make an older backtest cheaper than today's rule; they can only
   raise its cost. Cheaper pads apply only to trades from the table's first session on, i.e. mostly paper and forward
   tests. The alternative: report both pads and let the judge read the flat one as decided for older trades.

## Depends

MS-SIM-b (merged; read-only reuse, its owner session out of reach as of 25 Oct, orchestrator agreed); A4, A4c and A4f
(recording); O9 (Drive store and receipts). **Size:** M.
