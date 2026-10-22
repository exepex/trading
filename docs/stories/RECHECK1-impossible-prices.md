# RECHECK1. The older studies re-checked for impossible prices

**Repository:** trading · **Lane:** 1 (research records) · **Judge:** E · **Builder:** session_01MKtUHByHsR9cNwaP5KhFYH
· **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Branch:** `story/recheck1-text` (text), then
`story/recheck1-build` · **Owner's choice:** `docs/DESK_DECISIONS.md`, 22 Oct ("let's start recheck the older studies
for impossible price flaw") · **Status:** story text for the judge.

**Description.** As the desk (the statistician, the trader and the risk manager), I want every older study that priced
option legs from NSE's daily closes re-checked with EDGE1's impossible-price rule. Each study gets its original and
corrected figures side by side, so the desk knows whether any earlier conclusion rested on prices that cannot exist.

**Does this change a trade or stop decision?** No. Research only. Nothing touches the daily run, the card, Book 1 or a
capture.

**This is a correction report, not a new test.** Every study's data is already `spent` (`research/DATA_SPEND.md`).
A corrected figure can screen an idea out or confirm that it is out. It can never make an idea pass G6 (`FACTORY_RULES.md`
section 4). If a correction flips a "failed after costs" into a positive figure, the report says so plainly and the
owner decides whether a new, registered forward test is worth it.

## The flaw

`fno/research_engine/leg_prices.py` prices a traded leg at its close, which is its last trade. On a thin strike that
trade can be hours older than its neighbour's, so a position can be priced where it cannot be. For example, a
300-wide put spread is valued at 392.10 (experiment 1, SF, 8 Aug 2019), or one side of a condor below zero. The
existing check (`simulator.py`'s `bad_prices`, `exit_outside_payoff`) tests only the whole position against its payoff
bounds. Two broken verticals can offset inside those bounds.

## The rule (EDGE1's, as judge 473.3 passed it, made side-neutral)

- **Valid prices:**
  - **Each vertical is worth between 0 and its width.** A vertical is a sold leg paired with each bought leg of its
    type.
  - **The position is inside its payoff bounds** (`structures.payoff_bounds`).
  - A position with no vertical (a naked or single leg) is checked against its bounds only.
- **Side-neutral (the one change, agreed with EDGE1's builder on 22 Oct):**
  - **Why it is needed:** EDGE1's frozen `research/edge1/edge1study/verticals.py` tests "sold minus bought". That is
    right only when the sold leg is the dearer strike, a credit vertical. Run on sane prices, it calls every debit
    position impossible: BF, long iron fly 22000 CE/PE bought at 200/190, 22300 CE and 21700 PE sold at 80/75, gives
    `False`; a bull call spread bought 200, sold 80, gives `False`.
  - **The form used here:** a vertical's value is the price of its dearer strike minus its cheaper strike, in
    [0, width]. The dearer strike is the lower one for calls and the higher one for puts.
  - On every credit vertical this is EDGE1's test exactly.
  - EDGE1 is unaffected. Its builder checked SC2, SC3 and SF at every width: all are credit.
- **Where it applies, identically for every variant of every study:**

  | Point | What happens |
  |---|---|
  | Entry | Invalid prices are not taken (`impossible_prices_at_entry`). Where the study tries widths, the next width is tried, as the engine already does for an unfillable leg; where it has one width, the trade is not taken. |
  | Trigger days (stop, target) | Never fire on an invalid day; the day is skipped and counted. None of these studies has triggers, so this row is stated for completeness. |
  | Exit priced from closes | Kept, flagged `impossible_exit`, and left out of the decided figure. The all-trades figure uses the proxy: each failing vertical clipped into [0, width], then the position into its bounds. Charges stay at the raw closes. The raw figure is reported beside it. |
  | Exit at expiry, at intrinsic value | Nothing to check: no option price is used. |

- **The proxy's clip moves the cheaper-strike leg.** For a credit vertical that is the bought leg, as in EDGE1.
- **The limit, said once:** a stale close that still lies inside its bounds cannot be detected by any rule like this.

## One shared module, no second copy

- The rule lives in one new module, `fno/research_engine/price_validity.py`, holding `verticals`, `valid` and
  `proxy_value`, side-neutral. The EDGE1 builder agreed this on 22 Oct (option a).
- EDGE1's runs stay on their frozen copy. A test with the shared module proves equality with
  `edge1study/verticals.valid` and `proxy_value` on every SC2, SC3, SF, NS and NT position, on a strike grid and on
  random prices. EDGE1 imports the shared module at its next freeze, if there is one.
- I touch nothing under `research/edge1/`, and no frozen file (below). The re-check code is new, in
  `research/recheck1/`, and imports the shared module.
- The module goes into `fno/`, so it merges no earlier than Mon 26 Oct and never between 14:00 and 16:15 IST.

## Frozen files (checked before any change)

- Experiment 1's `research/2026-10-12-experiment-1/FREEZE.md` hashes 45 files, among them `leg_prices.py`,
  `simulator.py`, `structures.py` and `panel_reader.py`. They are read and imported, never edited.
- The weekly study's `FREEZE.md` (`study.py`, `report.py`, `PROTOCOL.md`) and FT1's (`ft1study/*`) are imported or read
  only.
- `structures.py` is also used by the new module (`payoff_bounds`, `position_value`), read only.
- `fno/freeze_sections.py` and G1 v1-v3's `FREEZE*.md` are checked again at build time. If a file the re-check must
  change is frozen, I stop and report.

## The studies (scope, from a read of each study's code)

| # | Study (trials) | Prices from | Entry check | Exit | Structures |
|---|---|---|---|---|---|
| 1 | Experiment 1, challenge 2019-23 and discovery 2024-26 (22-31) | `leg_price` (close, else settlement) | position bounds only | the close 21 or more days before expiry; `exit_outside_payoff` only flags | SC, SF credit; BF debit |
| 2 | Desk meeting 1, 2024-26 (1-21) | close, else settlement (`desk.py`, not frozen) | none (checked in `desk.py`) | the close 21 or more days before expiry | straddles (naked), condors, bull call and bear put debit spreads |
| 3 | Weekly study W1-W5 (43-52) | its own pricer, close with volume > 0 | none | expiry, intrinsic | W1-W2 single bought; W3-W4 debit; W5 credit condor |
| 4 | R1b's condor re-screen (53-55) | none: experiment 1's SC gross figures typed in | - | - | SC |
| 5 | STR1 samples | `leg_price`, entry only, one 2026 cycle | none | no P&L | LC, LP, CDS, PDS (debit), CCS, PCS (credit) |
| 6 | FT1 fill timing (54) | Groww 1-minute candle closes, stale bars dropped | risk <= 0 only | expiry, intrinsic | SF, SC, CCS, PCS credit; BF, CDS, PDS, LC, LP debit |

**Out of scope, with the reason:**
- **R2 stock options:** stock-option closes in a local cache absent here; it already refuses a price at or above the
  width, and its answer stopped at the cost wall.
- **The 12 Oct backtest:** Yahoo 5-minute index candles, no option close.
- **STR1b:** SPAN margins only, no option price.
- **The live D2 builder (`fno/playbook/candidates.py`):** not a study; it already checks position bounds.
  Applying the per-vertical rule to the live builder is a separate story if the owner wants it.

**A read-only check already done** (the study map, 22 Oct, today's panel): 7 position-level impossible exits in
experiment 1 (SF 2, SC 1, BF 4), the same 7 that it flagged. The per-vertical rule adds more:
- SC entries 11 Aug 2020 and 13 Jul 2021 were traded with a call spread priced above its 250 width;
- BF entries 16 Jul 2019, 11 Aug 2020 and 11 May 2021 have one vertical below zero;
- further exit breaches: SC 15 Apr 2020, and BF 11 Feb 2020 and 15 Mar 2022.

These are leads from an exploration, not results: the build recounts them under the frozen code. W3, W4 and W5 showed
no invalid entry.

## What each study's re-check does

1. **Reproduce first.** Re-run the study's own frozen code on its own data and get its recorded figures exactly, trade
   by trade:
   - experiment 1 at its frozen tree `0c1c957`, if the current tree differs;
   - the weekly study at `188ef58`'s panel end, 13 Oct.
   No correction is reported for a study that does not reproduce. The gap is reported instead.
2. **Apply the rule** to each reproduced trade's entry and exit leg prices. Where a corrected entry takes the next
   width, that trade is re-priced through the study's own frozen functions (charges, pad, lot), never by new arithmetic.
3. **R1b:** re-run `python -m fno factory screen`'s cost wall on experiment 1's corrected SC gross figures (mean and SD
   per period), with the same costs and bound.
4. **STR1:** report whether its sample entries are valid; it has no P&L to correct.
5. **FT1:** apply the entry rule to its same-minute candle prices; exits are intrinsic.
   - It needs the owner's Drive archive (the four `FNO_GDRIVE_*` settings).
   - If this container cannot read it, FT1's re-check is reported as not done, with the reason; it is never skipped
     silently.

## What the report shows (`research/recheck1/RESULTS.md`)

Per study and per variant, side by side:

| Column | Meaning |
|---|---|
| trades | original count; corrected count (entries refused, widths changed) |
| affected | trades touched by the rule: impossible entries, impossible exits; their rupees, raw and proxy |
| headline | the original figure as recorded; corrected all-trades (proxy); corrected decided (impossible exits left out) |
| verdict | original ("failed after costs", "screened out", ...); corrected; **changed: yes or no** |

Each row carries an evidence label. Each study also gets one sentence from the statistician on whether its
conclusion holds, and one from the risk manager on the worst trade, original and corrected.

## Registration

- **Ledger:** no new trial. This is a correction of recorded figures, following the precedent of `research/LEDGER.md`'s
  "Correction, not a trial" row (review 10). It adds one such row per study corrected, in `LEDGER.md`, pointing to the
  results. No trial is added to `research/ledger.csv` and no G0-G6 card is opened; data spent is unchanged.
- **If judge E reads the factory rules otherwise** ("every idea is a trial from G0"), the re-check becomes one ledger
  row with trial numbers claimed through `tools/claim_number.py`, before any run.

## Acceptance criteria

1. The shared module: side-neutral, with tests:
   - credit and debit verticals, condors (where each vertical is valid but the position is not), offsetting breaks,
     single and naked legs;
   - the proxy's clip moving the cheaper-strike leg, and the proxy's sign;
   - equality with EDGE1's frozen functions on every EDGE1 position.
   Planted bugs are caught: a dropped bound, a side-based instead of a strike-based vertical, no position clip.
2. Each study in scope reproduces its recorded figures before any correction, or its gap is reported.
3. Every row of the report table, for every study and variant, with the rule applied at the same points everywhere.
4. Nothing frozen is edited (each freeze's own check passes), nothing under `research/edge1/` changes, and no live
   reader changes.
5. Gates: pytest, ruff, `check_imports`; no file over 350 lines.

## Size (estimate)

- Module about 60 lines, with about 150 lines of tests.
- Re-check scripts about 250 lines across the studies.
- One results file.

## Claims

(For the build; filled in when the code goes to judge E.)
