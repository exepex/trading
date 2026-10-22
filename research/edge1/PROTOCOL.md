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
- **Moved expiries (revision 6):** NSE moved the expiry of contracts already listed (the 29 Jun 2023 holiday to 28
  Jun; BANKNIFTY to Wednesday in Mar-Apr 2024 and back to Thursday in Jan-Mar 2025; both indices to Tuesday in Sep
  2025). Each monthly contract keeps one date, the one it carried on its last listed day (`edge1study/expiries.py`),
  so a cycle entered before a move still finds its prices and settlement. It is applied after the seal, to the rows
  each run may read.
- **Lots:** section 8. **Margin:** section 9. **Calendar:** NSE's session calendar (A7); muhurat sessions are never
  decision, entry or exit days.
- **Run 1:** cycles with a decision day from 1 Jan 2019 to 31 Dec 2022.
- **Run 2:** cycles with a decision day from 1 Jan 2023 whose expiry is on or before the index's last data day (the
  NIFTY panel's last day; BANKNIFTY's last F&O file day, 19 Oct 2026 at the build, as NSE's 20 Oct file was not yet
  archived), so every variant of a cycle can complete, EXP included. The same cycles are used for all 12 variants of
  an index.
- **The seal:** run 1 loads no row dated after 14 Feb 2023 (its last decision day, 31 Dec 2022, plus 45 days): its
  December 2022 cycles expire in late January 2023, so every run-1 trade can complete, and run 1 reads at most these
  six weeks of 2023; this is stated, not hidden. The rows are cut before any panel is built. Run 2 runs once, after run
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

## 5. Structures (defined risk, the tradeable set; naked ones measured only)

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
- **Naked measurements (owner's Q1 answer, 22 Oct: "also measure").** Two structures per index, each with the T21
  exit only, so 4 measurements:
  - NS: the naked strangle, SC2's two shorts without wings;
  - NT: the naked straddle, SF's ATM body without wings.

  They are labelled **"not tradeable under the house rules"**. They are outside the pass family and the Holm family,
  and are never nominated without an explicit owner rule change. For each, the report shows:
  - P&L as for the other variants;
  - the worst loss per trade and per lot, unbounded, with no cap applied;
  - the margin each would need: SPAN plus exposure from the same calculator, which accepts naked legs.

  The engine's `require_covered` refusal stays as it is for every tradeable structure. The measurements go through a
  research-only structure in `research/edge1/` that builds the same legs without wings and is never registered with
  the engine's tradable list. The fill, untraded-leg and pad rules of section 7 apply to them unchanged.

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
- **Impossible exit prices (revision 7):** a day whose position mark is outside its payoff bounds (lowest <= value
  <= highest) is not a usable price day: SL2 and TP50 never fire on it, and a planned T21 exit on it is kept, flagged
  `impossible_exit` and counted as an incomplete exit.
- **Pads:** Rs 1 a unit a leg at entry and at exit (the engine's `PAD`), against the position; and a second run at
  Rs 2. EXP's settlement takes no exit pad.
- **Exit charges are taken off every exit,** including stops, targets and incomplete exits.

## 8. Lots

- **The lot of each cycle is its contract's market lot on the entry day (revision 5):**
  - from 2024, UDiFF's `NewBrdLotQty`;
  - before, NSE's circular schedule (`edge1study/lots.py`, sources in `LOT_CHECK.md`). R2's `derived_lot()` (the
    same-expiry future's turnover over contracts times settlement price) only checks it: the build found it wanders
    one or two units around the true lot, so it is never used as the lot.
- **Cross-check:** every legacy-file derived lot more than 5% from the schedule is listed (`lot_changes.py`), with the
  result in `LOT_CHECK.md`.
- **Reporting:** results are given for 1 lot of the time (rupees) and per unit. Today's lot (NIFTY 65, BANKNIFTY 30)
  is a second column, never decided on.
- The wing width the cap picks moves with the lot, so the report shows the width used per year and index.

## 9. Costs and margin

- **Charges:** C1's `fno.costs` with `config.yaml`'s `charges` table, at every order, as the engine does.
  - That table's 0.15% STT is applied to every date, so history is charged more than it paid. This is conservative
    and is the decided figure.
  - A historical-STT run (pad 1) is reported beside it, never decided on. Each order is charged at its own trade
    date's rate (entry on the entry day, the exit on its exit day, settlement on expiry): on sold premium 0.05% before
    1 Apr 2023, 0.0625% to 30 Sep 2024, 0.1% to 31 Mar 2026, then 0.15%; on exercise 0.125% to 31 Mar 2026, then
    0.15%. Checked in the build: Finance Act 2023 (NSE circular FATAX56235), Finance (No. 2) Act 2024, Budget 2026
    (NSE/FATAX/73524).
  - Only STT is made historical. NSE's options transaction charge was higher before 1 Oct 2024 (about 0.053% of
    premium against today's 0.03503%) [some evidence: broker charge pages, not a circular read in the build], so
    the decided run under-charges that part of history by about 0.018% of premium per side. STT's gap is larger
    (0.10% of sold premium before Apr 2023), so the decided run stays conservative overall; this is stated, not
    modelled.
- **Margin, return on margin only (not a pass condition):**
  - SPAN plus exposure per lot at entry, from that day's archived SPAN file and C2/A14's calculator, read only;
  - the file is read with `read_span_file(..., allow_short_option_minimum=True)` and checked point in time (A9's
    manifest SHA-256, created before 09:00 IST);
  - the cycle's own lot, NSE's index exposure rule, and C2's stress factor k = 2.1 for a stressed figure beside it.
  - SPAN files start on 2 Jan 2020, so 2019's cycles have no margin figure.
  - A `MarginOutsideModel` case is counted and named.
  - **Check (revision 3):** no independent historical margin exists (NSE publishes the SPAN files, not a margin per
    position; `margins.csv` comes from the same calculator, so it cannot check it; A14c part 2's Groww check is
    paused). Every margin figure is therefore labelled "calculator only, unchecked" [reasoning only]. If A14c part
    2's read-only broker check is live before run 1, one recent day per index is compared and the result reported.
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
traded. A variant expected under 30 is named before run 2 as likely untestable (p = 1).

It is committed before run 2. Judge B reproduces it.

## 11. Run 2: test the G1 passers once, and nominate

Only run 1's G1 passers are tested, on run 2's cycles:
- **D:** mean net per trade (after charges and pads) on complete-exit trades, at the Rs 1 pad.
- **One-sided p of D > 0:** G4's bootstrap code (`fno/forecast_scoring/block_bootstrap.resampled_means`, 10,000
  resamples, seeded by the variant's index k in a fixed list), with the **block length passed in as 2 trades** for
  every variant (judge 468 SF1, 468.1). G4's 20 suits daily data; here a trade is one monthly cycle.
  - T21, SL2 and TP50 trades exit before the next cycle's decision.
  - EXP trades are held to expiry, past the next decision (about 13 Jan for the 27 Feb 2025 expiry, against a 30 Jan
    exit), so consecutive EXP trades overlap by about two weeks and share index moves.
  - A block of 2 keeps such neighbours together, and is used for every exit rule alike, EXP or not (owner, 22 Oct
    2026: judge B's block 2 accepted; one block for all exits is the simpler choice).
  - The build adds `block` as a keyword argument to `resampled_means`, defaulting to G4's 20, so no existing caller
    changes.
  - The test: p = (1 + #{b : M*_b - D >= D}) / (B + 1), with M* the resampled means; that is, the share of re-centred
    means at least as far above 0 as D.
  - **Fewer than 30 trades: not tested, p = 1.** G4's minimum of 40 is twice its block of 20. With a block of 2,
    30 trades (15 blocks) is the floor I state for a mean's bootstrap to be usable [reasoning only].
- **Holm** at 0.05 across every variant run 2 tests, **both indices in one family**
  (`fno/scoreboard/uncertainty.holm`), and registered as the family
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
  card (`research/ideas/EDGE1-<index>-<structure>-<exit>.md`). Then 4 measurement cards (NS and NT per index,
  `hypothesis: no`, `measurement: yes`; the factory never screens a measurement). All 28 cards are written by
  `research/edge1/cards.py`. The count is honest: every card is a trial whether or not it passes G1.
- **Order (revision 4: the factory's own gate order, G1 before G2 and G3):**
  1. the DATA_SPEND rows are committed first, naming the trials;
  2. then each card through `factory register`, one per commit after a pull;
  3. then `factory question <id> "<text>" --alpha 0.05` for the family, with every card's `pass_level` at 0.05;
  4. run 1; its G1 inputs (gross, tail, cost) and G3 inputs (sd per trade, frequency) are copied from
     `selection.json` into each tradeable card and committed;
  5. then `factory screen` on each tradeable card; for each G1 passer only, `factory spend` (it will say
     exploratory) and `factory plan`;
  6. run 2.
- G4 is this file frozen (`research/edge1/FREEZE.md`, SHA-256 of this file and of the analysis code) and named as each
  ledger row's `protocol_commit`. G6 is the results file. The factory's shadow-only `freeze` and `verdict` are not
  used, so the gate log ends at G3 (or at G1 for a screened-out card).
- The guard refuses `--select` or `--final` on code whose hashes differ from FREEZE.md, and refuses `--final` until
  `selection.json` is committed.

## 14. Deviations

- **Revision 7 (after run 1, owner's decision of 22 Oct 2026: "fix and re-run, report both").** Run 1 at 3152ed44
  (`selection_rev6.json`, committed d4ea08d6) exposed impossible exit prices: NSE's option close is each strike's last
  trade, at different times, so an illiquid strike's close can put the position outside its own payoff bounds.
  Examples, one per type:
  - a spread worth more than its width: NIFTY SF T21, 16 Jul to 8 Aug 2019, put spread 11650/11350 at 715.20 and
    323.10 = 392 against a 300 width (net -15,810 on a Rs 10,000 cap);
  - a stop fired on it: NIFTY SC2 SL2, 15 to 21 Dec 2020, put spread 13300/13150 at 156 against a 150 width (net
    -12,096);
  - a lower strike dearer than a higher one: BANKNIFTY SF TP50, 16 to 30 Nov 2021, put 37400 at 1960.40 above put 38300
    at 1755.65, mark -131.75 < 0, the target fired (net +21,533, above the trade's maximum gain of 18,850).
  Affected complete trades in run 1 (exit mark outside the bounds): NIFTY SC2 SL2 1; NIFTY SF T21, SL2, TP50 2 each;
  BANKNIFTY SF T21, SL2 2 each; BANKNIFTY SF TP50 1; every other variant 0 (EXP settles and is unaffected).
  **The rule, one for every variant and both runs:** a day whose position mark is outside `payoff_bounds(legs)` is not
  a usable price day; a trigger never fires on it, and a planned exit on it is kept, flagged `impossible_exit` and
  counted as an incomplete exit (out of the decided mean, in the all-trades mean). Entry already refused such prices
  (`bad_prices`). No variant-specific change. Known limit: a stale close inside the bounds cannot be detected. Run 1
  is re-run from the re-frozen code; the results file shows both runs 1 side by side, and the passer's result with and
  without the +21,533 trade; run 2 then runs once under the same code.
- Revision 6 (before the freeze, the input probe: counts and dates only): four run-2 expiries had no settlement
  (NIFTY and BANKNIFTY 29 Jun 2023, BANKNIFTY 28 Mar 2024 and 29 Jan 2025) because NSE moved those contracts' dates;
  each monthly contract now keeps its final date (section 3). BANKNIFTY's files end on 19 Oct 2026, not 20 Oct.
- Revision 5 (before the freeze, the lot cross-check): the derived lot wanders 72-77 around NIFTY's 75 (turnover is
  at the average price, not the settlement price), so legacy-file lots come from NSE's circular schedule and the
  derived lot only checks it (section 8, `LOT_CHECK.md`).
- Revision 4 (before the freeze): section 13's order follows the factory's gates (G1 screen, then G2 spend and G3
  plan for passers only; the old order put spend and plan before the screen, which the factory refuses), and the 4
  measurement rows are measurement cards registered like the others.
- Revision 3 (before the freeze): the seal is stated as 14 Feb 2023 and enforced at load (section 3); the
  historical-STT dates are sourced, exercise STT added, the higher pre-Oct-2024 exchange charge stated (section 9);
  the margin build gate, which had no independent source, is replaced by an "unchecked" label (section 9).
- Revision 2 (before the freeze): the owner's Q1 answer, with the naked strangle and straddle measured outside every
  family (section 5); Q2 accepted (screen and nominate).
- Revision 1 (before the freeze, judges 468 and 468.1): the bootstrap block is 2 trades (EXP trades overlap), with a
  floor of 30 trades; Holm spans both indices; run 1 prints expected run-2 counts.
- Any change after the freeze is written here, before any result it could affect, and sent to judge B.
