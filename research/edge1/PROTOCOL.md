# Protocol: EDGE1, simple rule-based option trades after real costs

Story: `docs/stories/EDGE1-edge-study.md` (judge 467.3 PASS, rev 4). Builder: session_01UkTaDeTRF9ksDgQB9cTU5C. Judge
B reviews this protocol and its freeze before run 1, and reproduces both runs. Research only: nothing here changes the
live daily run, the card, the captures or Book 1.

## 1. The question

Has any simple, rule-based monthly option position on NIFTY or BANKNIFTY made money after every real cost, and is any
of them worth a forward shadow?

## 2. Status: every result is exploratory

This section comes first, because it limits what any result can mean.
- NIFTY's and BANKNIFTY's option daily closes for 2019 to 20 Oct 2026 are `spent` in `research/DATA_SPEND.md` (trials
  1-31, 42, 43-52; G13b's back-fill; GR1). The factory counts `spent` and `exposed` alike.
- The direction was partly foreseen. GR1 measured implied ranges running wide on these years (BANKNIFTY N1's 50% band
  0.624 in 2024; 90% coverage 0.927 in 2025-26).
- So no result can pass G6. EDGE1 is a screen. Its only possible outcome beyond "ruled out" is a **nomination** of at
  most two variants (section 11) for a registered forward shadow, as a proposal to the owner and a later story.
- What is fresh: no variant's P&L has been computed on BANKNIFTY. SC3, and SL2/TP50/EXP on any structure, have not been
  computed on NIFTY either. SC2/T21 and SF/T21 on NIFTY 2019-23 are experiment 1's P1 and P2, re-measured here under
  stricter fill rules and historical lots; they are known before.

## 3. Data, sources and periods

- **NIFTY:** the end-of-day panel (`fno/research_data/panel_reader.py`, `read_nifty_panel`; 1 Jan 2019 to its last
  day). 2021-03-30 is missing, as the panel's README states.
- **BANKNIFTY:** NSE's daily F&O files in Drive (`fno/storage/wiring.py`: the UDiFF and legacy libraries, read by
  `fno/fo_bhavcopy.read_fo_file`). They are turned into the same panel rows as NIFTY's, by the panel's own row code
  with the symbol as a parameter (build part 1).
- **Index closes:** the panel's `underlying` for NIFTY; G13b's BANKNIFTY close table. Spot for strike selection is the
  entry day's index close.
- **Final settlement (EXP):** G13c's settlement chain (`fno/itm_chance/wiring.settlement_chain`: E7, then the legacy
  FUTIDX row), cross-checked against the index close.
- **Lots:** section 8. **Margin:** section 9. **Calendar:** NSE's session calendar (A7); muhurat sessions are never
  decision, entry or exit days.
- **Run 1:** cycles with a decision day from 1 Jan 2019 to 31 Dec 2022.
- **Run 2:** cycles with a decision day from 1 Jan 2023 whose expiry is on or before the index's last data day (the
  NIFTY panel's last day; 20 Oct 2026 for BANKNIFTY's files), so every variant of a cycle can complete, EXP included.
  The same cycles are used for all 12 variants of an index.
- **The seal:** run 1 loads no price dated after its last cycle's planned exit. Its December 2022 cycles exit by late
  January 2023, so run 1 reads at most January 2023's closes; this is stated, not hidden. Run 2 runs once, after run
  1's selection is committed.
- **Weeklies are out of this protocol.** The engine's cycles are monthly, every NIFTY weekly is spent, and BANKNIFTY's
  weeklies ended on 14 Nov 2024. A weekly study would be a separate story.

## 4. Cycles

The engine's monthly cycles (`fno/research_engine/cycles.py: monthly_cycles`), unchanged, for each index on its own
data:
- **Decision day:** the first trading day on which a monthly expiry (one with a future listed that day) is 30-45
  calendar days away.
- **Entry:** the next trading day's close.
- **Planned T21 exit:** the last trading day with 21 or more calendar days to expiry.

BANKNIFTY's monthly expiry is read from its own listed futures, never from a weekday rule, so its weekday changes are
followed as the files list them. The report lists each change with its first expiry.

## 5. Structures (defined risk only; Q1 default)

| Code | Shorts | Wings |
|---|---|---|
| SC2 | call nearest spot x 1.02 (ties up), put nearest spot x 0.98 (ties down) | the engine's rule: the largest width in its list keeping the worst loss at or below Rs 10,000 for the day's lot |
| SC3 | call nearest spot x 1.03, put nearest spot x 0.97 | the same |
| SF | call and put at the ATM strike | the same |

- **Widths.** NIFTY uses the engine's list (300, 250, 200, 150, 100 points). BANKNIFTY uses the same list times 3
  (900, 750, 600, 450, 300), because its strikes are 100 points apart and its index is about 2.3 times NIFTY's
  [reasoning only: so that a wing is a few strikes out on both]. This is fixed now and never tuned.
- **Worst loss.** A width is used only if (width - credit) x lot <= Rs 10,000, with credit per unit after pads. If no
  width fits, the trade is `no_trade_cap`, counted.
- **Building the legs.** SC2 and SF are the engine's `ShortCondor` and `ShortIronFly`. SC3 is `ShortCondor` with the
  offset passed as a parameter, default 0.02 (build part 3: one argument, no change for existing callers).
- **Naked legs.** If the owner chooses Q1 (b), the naked strangle (SC2's shorts without wings) and the naked straddle
  (SF's body without wings) are measured outside the pass family, labelled "cannot be traded under the house rules",
  with their worst loss unbounded. They are never nominated.

## 6. Exits

| Code | Rule |
|---|---|
| T21 | the planned T21 exit day's close |
| EXP | held to expiry, cash-settled at the final settlement price (section 3), with C1's settlement charges |
| SL2 | the first day after entry and before the T21 exit day on which the position's mark (the cost to buy it back at that day's closes) is at least 3 x the entry credit, i.e. a loss of 2 x the credit, exits at that close; else T21 |
| TP50 | the first such day on which the mark is at most 0.5 x the entry credit (half the credit earned) exits at that close; else T21 |

- SL2 and TP50 are checked only on days when every leg traded (volume > 0). Marks use closes, never settlement prices.
  An intraday breach that recovers by the close is not seen; this is stated in the report.
- 12 variants per index: {SC2, SC3, SF} x {T21, EXP, SL2, TP50}.

## 7. Fills, untraded legs and pads (judge 467 SF2, 467.2)

- **Entry:** a trade is taken only if every leg traded on the entry day, priced at its close. Otherwise it is not
  taken, with the reason `untraded_leg_at_entry`. The engine's other statuses (`missing_strikes`, `bad_prices`,
  `no_trade_cap`) are kept as they are.
- **Exit:** at the trigger close (SL2, TP50, where every leg traded by construction), at the planned T21 close, or at
  settlement (EXP). No other day is ever searched for.
  - At a T21 close, a leg that did not trade takes its settlement price, the engine's flagged proxy, and the trade is
    marked `incomplete_exit`.
  - Incomplete exits are kept: they count in the all-trades figures (section 11). The complete-exit figures leave
    them out.
- **Bad prices:** an entry is skipped (`bad_prices`) unless its credit per unit is strictly inside the structure's
  payoff bounds (B2's test, lowest < value < highest).
- **Pads:** Rs 1 a unit a leg at entry and at exit (the engine's `PAD`), against the position; and a second run at
  Rs 2. EXP's settlement takes no exit pad.
- **Exit charges are taken off every exit,** including stops, targets and incomplete exits.

## 8. Lots

- **The lot of each cycle is its contract's market lot:**
  - from 2024, UDiFF's `NewBrdLotQty` on the entry day;
  - before, R2's `derived_lot()`: the same-expiry future's turnover over contracts times settlement price, rounded to
    the nearest whole lot.
- **Cross-check:** every change in the derived series is checked against NSE's lot-size circular for that date. A
  disagreement is listed, and the circular's lot is used, with the circular named.
- **Reporting:** results are given for 1 lot of the time (rupees) and per unit. Today's lot (NIFTY 65, BANKNIFTY 30)
  is a second column, never decided on.
- The wing width the cap picks moves with the lot, so the report shows the width used per year and index.

## 9. Costs and margin

- **Charges:** C1's `fno.costs` with `config.yaml`'s `charges` table, at every order, as the engine does.
  - That table's 0.15% STT is applied to every date, so history is charged more than it paid. This is conservative
    and is the decided figure.
  - A historical-STT run is reported beside it, never decided on. It uses NSE's rates by trade date: 0.05% of premium
    on sold options before 1 Apr 2023, 0.0625% to 30 Sep 2024, 0.1% to 31 Mar 2026, then 0.15% [reasoning only:
    rates from the Finance Acts as I recall them; each date is checked against the Act or NSE's circular in the build,
    and any correction is listed].
- **Margin, return on margin only (not a pass condition):**
  - SPAN plus exposure per lot at entry, from that day's archived SPAN file and C2/A14's calculator, read only;
  - the file is read with `read_span_file(..., allow_short_option_minimum=True)` and checked point in time (A9's
    manifest SHA-256, created before 09:00 IST);
  - the cycle's own lot, NSE's index exposure rule, and C2's stress factor k = 2.1 for a stressed figure beside it.
  - SPAN files start on 2 Jan 2020, so 2019's cycles have no margin figure.
  - A `MarginOutsideModel` case is counted and named.
  - **Build gate:** a few days a year for each index are compared with NSE's published margin before any margin result
    is used. If they do not match, the margin figures are reported as missing.
- Return on margin = net P&L / (SPAN + exposure at entry), per trade; the report also shows the mean over trades.

## 10. Run 1: measure and screen (G1)

For every variant and index on run 1's cycles, on complete-exit trades at the Rs 1 pad:
- **n:** trades taken.
- **Gross and costs:** mean gross per trade (before charges and pads), and mean charges plus pads per trade.
- **Tail:** the share of trades losing more than 2 x their own credit, and their mean loss.

G1 is R1's CostWall (`fno/factory/cost_wall.screen`), as each card's `factory screen` runs it:
- gross is run 1's measured mean (the card's `gross.source` says "run 1, 2019-22, EDGE1"), cost is the measured mean
  charges plus pads, and the tail is the measured tail above;
- a variant passes G1 when the 90% one-sided lower bound of mean gross, minus cost, minus tail, is above 0;
- a variant with fewer than 20 run-1 trades does not pass ("too few run-1 trades").

Run 1 writes `research/edge1/selection.json`: every variant's numbers and its G1 outcome, plus the SD per trade and
trades a year that G3 needs.
It also prints each G1 passer's **expected run-2 trade count** (judge 468 note 1): run 2's monthly expiries, counted
from NSE's session calendar and expiry listings only (no price read), times the variant's run-1 share of cycles
traded. A variant expected under 30 is named before run 2 as likely untestable (p = 1). It is committed before run 2. Judge B reproduces it.

## 11. Run 2: test the G1 passers once, and nominate

Only run 1's G1 passers are tested, on run 2's cycles:
- **D:** mean net per trade (after charges and pads) on complete-exit trades, at the Rs 1 pad.
- **One-sided p of D > 0:** G4's bootstrap code (`fno/forecast_scoring/block_bootstrap.resampled_means`, 10,000
  resamples, seeded by the variant's index k in a fixed list), with the **block length passed in as 1 trade** (judge
  468 SF1). G4's 20 suits daily data. Here the trades are monthly and never overlap (each exits at T21, EXP or earlier,
  before the next cycle's decision), so one trade is the natural block. A 20-trade block on about 45 trades would leave
  about 3 blocks per resample, a near-degenerate null. The build adds `block` as a keyword argument to
  `resampled_means`, defaulting to G4's 20, so no existing caller changes.
  - The test: p = (1 + #{b : M*_b - D >= D}) / (B + 1), with M* the resampled means; that is, the share of re-centred
    means at least as far above 0 as D.
  - **Fewer than 30 trades: not tested, p = 1.** G4's minimum of 40 is twice its block of 20. With a block of 1,
    30 trades is the floor I state for a mean's bootstrap to be usable [reasoning only].
- **Holm** at 0.05 across every variant run 2 tests, **both indices in one family** (`fno/scoreboard/uncertainty.holm`), and registered as the family
  of the one research question in R1's factory.

**Nomination rule** (at most two, in order of Holm-adjusted p). All of these must hold:
1. Holm-significant on D;
2. D > 0 at the Rs 2 pad too;
3. run 2's mean net on **all** trades (incomplete exits included, at their proxy prices) > 0, at both pads;
4. run 1's mean net (complete exits, Rs 1 pad) > 0.

A nomination is a proposal to the owner, never a trade. Without a nominee the answer is "no simple rule found, after
costs, on 2019-2026".

## 12. What the report shows (each figure with its label)

Per variant, index and run:
- **P&L:** trades taken; net P&L total and per trade; the share of trades won; mean gross, charges and pads.
- **Risk:** max drawdown on the cumulative net, in date order; the worst calendar month (by exit day); the worst
  trade.
- **Return on margin:** mean and median per trade, from 2020.
- **Fills:** not-taken trades by reason; incomplete exits and their mean proxy P&L; the share of trades with any proxy
  price.
- **Sensitivities:** the Rs 2 pad, historical STT and today's lot beside the decided figures.

Labels: every figure is *exploratory*. A nominee is *some evidence* at most, and everything else is *reasoning only*.
The width used per year, the lot series with its circular cross-check, BANKNIFTY's expiry-day changes and the margin
build gate's result are listed too.

## 13. Registration and counting

- **Trials:** 24 consecutive trials from the next free ledger number, one per variant and index, each with its own idea
  card (`research/ideas/EDGE1-<index>-<structure>-<exit>.md`). Plus 2 measurements if Q1 is (b). The count is honest:
  every card is a trial whether or not it passes G1.
- **Order:**
  1. the DATA_SPEND rows are committed first, naming the trials;
  2. then each card through `factory register`, one per commit after a pull;
  3. then `factory spend` (it will say exploratory) and `factory plan`;
  4. then `factory question <id> "<text>" --alpha 0.05` for the family, with every card's `pass_level` at 0.05;
  5. then `factory screen` after run 1.
- G4 is this file frozen (`research/edge1/FREEZE.md`, SHA-256 of this file and of the analysis code) and named as each
  ledger row's `protocol_commit`. G6 is the results file. The factory's shadow-only `freeze` and `verdict` are not
  used, so the gate log ends at G3 (or at G1 for a screened-out card).
- The guard refuses `--select` or `--final` on code whose hashes differ from FREEZE.md, and refuses `--final` until
  `selection.json` is committed.

## 14. Deviations

Revision 1 (before the freeze, judge 468): the bootstrap block is 1 trade with a floor of 30 trades; Holm spans both
indices; run 1 prints expected run-2 counts. Any change after the freeze is written here, before any result it could affect, and sent to judge B.
