# EDGE1. Has any simple, rule-based NIFTY or BANKNIFTY option trade made money after real costs?

**Repository:** trading · **Lane:** 1 (new story; research records, the ledger) · **Judge:** B · **Builder:**
session_01UkTaDeTRF9ksDgQB9cTU5C · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Branch:**
`story/edge1-text` (text), then `story/edge1-<part>` (code) · **Owner's choice:** `docs/DESK_DECISIONS.md`, 22 Oct
("Edge study ... through R1's factory") · **Status:** story text for the judge; two owner questions open (Q1, Q2) with
written defaults. Revision 2: all history is exploratory (R1's owner's point, accepted); one card per variant.
Revision 3: judge 467's two should-fixes (SF1 option a with GR1's facts; SF2 the untraded-leg rule) and notes.

**Description.** As the desk (the trader, the strategist, the risk manager and the statistician), I want one honest,
pre-registered answer to "has any simple, rule-based option trade on NIFTY or BANKNIFTY made money after every real
cost?". It should cover the usual premium-selling structures and Book 1's own, with P&L, drawdown, worst month, win
rate and return on margin, each labelled by its evidence. Then the desk knows whether there is anything worth paper
trading. "Nothing works" is a valid answer and is reported in the same detail.

**Does this change a trade or stop decision?** No. Research only. Nothing touches the live daily run, the card, the
captures or Book 1. A variant that passes can only become a registered shadow, through R1's factory and R3, by a later
story and the owner's go.

## What is already known (read before any new number)

| Earlier test | Structures | Data | Result |
|---|---|---|---|
| Experiment 1 (trials 22-31) | SC, SF, BF every month; filters on IV minus RV, VIX, events | NIFTY monthly 2019-23, 60 cycles | Nothing passed. SC every month -34,486; SF -58,219. Positive totals rest on stale exits. |
| Desk meeting 1 (trials 1-21) | Short ATM straddle, unprotected; condors | NIFTY 2024-26 | Straddle +2,87,463 with one trade at -41,030 (1 lot); condors +24,757 to +69,026 on 10-30 tradable months. Exploratory. |
| Weekly study (trials 43-52) | W1-W5, held to expiry | NIFTY weekly Feb 2019 - Oct 2026 | Nothing passed. W5 short iron condor -224 a trade, n 393. |
| R1b re-screen | SC condor | NIFTY 2019-23 and 2024-26 | `screened_out` (net on the bound -990.5 and -453.5). |

The prior that a simple rule passes is low [strong evidence: four tests, all after costs]. This study adds what was not
yet tested: BANKNIFTY, exits beyond the time exit (stop, target, hold to expiry), wider offsets, historical lot sizes,
and return on margin. It does not re-run the failed NIFTY variants as if they were new.

## Data and what it can prove (G2)

- **NIFTY options 2019-2026 (monthly and weekly) are `spent`** (`research/DATA_SPEND.md`, trials 1-31, 42, 43-52). Any
  NIFTY history result is **exploratory by rule**: it can screen ideas out, never pass G6.
- **BANKNIFTY's option closes are spent too** (revision 2, R1's owner, 22 Oct). G13b's implied back-fill read them for
  2019 to 20 Oct 2026 (the DATA_SPEND row "NIFTY and BANKNIFTY ranges from option daily closes", `spent`). The factory
  counts `spent` and `exposed` alike (`fno/factory/data_spend.py`: either makes a test exploratory). My first draft
  called BANKNIFTY's 2023-26 monthlies held back; that was wrong, and is withdrawn.
- **The direction was also partly foreseen (judge 467 SF1, option a taken).** Premium selling pays when implied runs
  wide, and GR1 measured exactly that on these years:
  - BANKNIFTY's N1 implied 50% band held 0.624 of closes in 2024 (judge 442.2's reproduction);
  - its 90% coverage in 2025-26 was 0.927, and a constant shrink beat it (response 314, judge 459);
  - G13b's yearly scores were read as well.
  So even a clean split would have known that selling was favoured. This is a second reason why no historical pass can
  be more than exploratory.
- **So every historical result in EDGE1 is exploratory.** EDGE1 is a screen: it can rule variants out, and it can
  nominate at most two variants for a registered forward shadow (R3). That shadow is the only test that can confirm
  anything.
- **The two-run split is kept anyway, against overfitting:**
  - *run 1:* 2019-01 to 2022-12, both indices; selects and applies G1;
  - *run 2:* 2023-01 to 2026-10, opened once, sealed at load as GR1 did; only run 1's G1 passers.
  - A variant that wins run 1 and loses run 2 is reported as such. Both runs are labelled exploratory.
- **Weeklies:** NIFTY weeklies only, exploratory as everything else; BANKNIFTY's weeklies ended on 14 Nov 2024.
- **Power, said in advance:** run 2 has about 46 monthly trades per index. Take an SD of about Rs 4,000 a trade and a
  true net of Rs 300. G3's plan then needs n = (1.28 x 4,000 / 300)^2, about 290 trades [reasoning only: the SD is
  assumed from experiment 1]. So history can at best nominate; the shadow's own G3 plan sets how long the forward test
  must run.

Sources: NIFTY from the panel (`fno/research_data/panel_reader.py`). BANKNIFTY from NSE's F&O bhavcopy in Drive (legacy
and UDiFF, `fno/fo_bhavcopy.py`, through G13b's `BhavcopyChains`). Expiry-day settlement from G13c's settlement chain
(E7 plus the legacy reader).

## The variants (one family, counted once; Q1 decides the naked ones)

Every variant enters on the engine's monthly cycle: decided 30-45 days before a monthly expiry, entered the next session
at its close. The engine (B2-B4) is reused, not copied.

| Code | Structure | Strikes |
|---|---|---|
| SC2 | Iron condor (Book 1's `b0-monthly-sc`) | Short call nearest spot x 1.02, short put nearest x 0.98, wings at the largest width keeping the worst loss within Rs 10,000 |
| SC3 | Iron condor, wider | Shorts at x 1.03 / x 0.97, same wing rule |
| SF | Short straddle with wings (iron fly) | ATM body, same wing rule |

| Exit code | Exit |
|---|---|
| T21 | Time exit at the last session with 21 or more days to expiry (the engine's and Book 1's) |
| EXP | Hold to expiry, cash-settled at the final settlement price |
| SL2 | Stop when the position's close-to-close loss reaches 2 x the credit; else T21 |
| TP50 | Take profit when 50% of the credit is earned at a close; else T21 |

That is 3 x 4 = **12 variants** per index.

- **Q1 (the owner's):** a short strangle and a short straddle *without* wings are naked short legs, which the house rules
  forbid ("never a naked short leg", worst loss at most Rs 10,000).
  - **Default (a):** defined-risk only, as above.
  - **(b):** also measure the two naked versions, labelled "cannot be traded under the house rules", with their worst
    loss shown unbounded. They would be outside the pass family, so they can never pass.
- Stops and targets are checked on end-of-day closes only. An intraday breach that recovers by the close is missed;
  the report says so.
- **Untraded legs (judge 467 SF2).** The engine prices a leg with no trades at its settlement price, flagged
  (`leg_prices.py`: "a valuation proxy, not an executable price"). Those proxies made experiment 1's positives stale.
  The rule here:
  - A trade is taken only when **every leg traded** (volume > 0) on its entry day, and closed only at a close where
    every leg traded. If no leg-complete close exists by the exit day, the trade is recorded at the exit day with its
    proxies flagged, and it is **left out of the pass and nomination figures**.
  - SL2 and TP50 are checked only on days when every leg traded.
  - Not-taken trades are counted by reason (an untraded leg at entry, missing strikes, bad prices, over the cap).
  - The report shows, per variant and period, the share of trades with any proxy price, and all trades (proxies
    included) beside the traded-only figures.

## Costs (G1) and margin

- **Charges:** C1's `fno.costs` (`order_charges`, `settlement_charges_breakdown`): brokerage, STT, exchange, SEBI, IPFT,
  stamp and GST, from `config.yaml`. As C1 states, today's 0.15% STT is applied to every date, which is conservative
  because STT was lower before Oct 2024. A second run with the historical STT schedule is reported beside it, never
  decided on.
- **Slippage, stated:** the engine's pad of Rs 1 a unit a leg at entry and at exit, with a 2x sensitivity. Beside it
  goes A4's measured 15:00 half-spread by moneyness (13 Oct 2026 onward), as a check of whether Rs 1 is enough today
  [some evidence only: about 8 sessions].
- **Lot sizes:**
  - historical lots per expiry: UDiFF's `NewBrdLotQty` from 2024, and R2's `derived_lot()` before (turnover / (contracts
    x settlement price) of the same-expiry future);
  - results in rupees for 1 lot of the time and per unit. Today's lot (NIFTY 65, BANKNIFTY 30) is a second column;
  - `derived_lot()` is cross-checked against NSE's lot-size circulars at every change date, and any mismatch is listed;
  - the wing width that the Rs 10,000 rule picks moves with the lot, so the width chosen is shown per year and index.
- **BANKNIFTY's expiry-day changes** are listed in the report as read from the files (monthly expiry weekday per year;
  the weeklies' end on 14 Nov 2024), with each change's first expiry.
- **Margin:**
  - C2/A14's SPAN calculator (`fno/nse_margins/calculator.py`, `read_span_file(..., allow_short_option_minimum=True)`)
    on each entry day's archived SPAN file, plus NSE's exposure rule;
  - SPAN files exist from 2 Jan 2020, so return on margin is reported from 2020 only;
  - BANKNIFTY goes through the calculator's `symbol` parameter, which is unproven. **A build gate:** before any
    result, a few days a year are checked against NSE's published margin for both indices. A mismatch stops the margin
    figures, which are reported as missing, never guessed.
  - C2's stress factor k = 2.1 for a stressed figure.
  - **The A14c owner's points (22 Oct), adopted:**
    - SPAN files are read through `prefetch.in_order(per_thread(build_drive_span_files), ...)`, with A14's
      point-in-time checks: the SHA-256 must equal A9's manifest, and the file must be created before 09:00 IST that day.
    - Margin is built per entry day with that day's lot (lots changed: NIFTY 75, 50, 25, 75, 65; BANKNIFTY several
      times). Today's lot is never used on old files.
    - An entry is skipped unless its NOV per unit is strictly inside `payoff_bounds(legs)` (lowest < value < highest),
      as B2's BAD_PRICES test does. A credit equal to the full width, or of 0, is skipped too. This catches the
      impossible April 2020 rows.
    - A missing series (e.g. 1 Aug 2025's file, without 25 Sep 2025) raises `MarginOutsideModel`. It is counted and
      named, never filled.
    - BANKNIFTY's monthly pick in files that also list weeklies (before Nov 2024) is checked, NIFTY and BANKNIFTY are
      kept apart, and a few days a year are checked against NSE's published figures before any result.
    - All variants here are credits, so NOV does not zero the SPAN as it does for a bought fly.

## Registration (R1's factory; nothing new)

- **Ledger:** one trial per variant per index, because every one is tested: **24 consecutive trials from the next free
  ledger number** (71-94 if nothing else registers first), plus 2 if Q1 is (b) (measurements). Each card's `trial` is
  written just before its own `register`. Registered before any result, with `research/edge1/PROTOCOL.md` frozen and hashed as
  GR1's was. The B4 guard (`Ledger.register`, `require_registered`) is enforced.
- **Factory:**
  - **one card per variant and index** (R1's rule: an exit, a structure or an underlying is a new idea), so 24 cards
    in `research/ideas/EDGE1-*.md`;
  - G0 through `python -m fno factory register`, **one card per commit, after `git pull`**, because the trial number
    must be the next ledger number at that moment;
  - the DATA_SPEND rows are committed first, on their own, naming the trial numbers in "Used by";
  - G1 CostWall on run 1's numbers only, with each card's `gross.source` saying so (never run 2's outcomes);
  - G2 `factory spend` (it will say exploratory, as above);
  - G3 `factory plan` with run 1's SD and frequency;
  - one research question for the family (`factory question <id> "<text>" --alpha 0.05`; every card's `pass_level`
    equals it), with cumulative Holm.
  - **G4 and G6 by hand**, as GR1 did: G4 is the ledger's protocol_commit plus the frozen PROTOCOL.md, and G6 is the
    results file. The factory's `freeze` and `verdict` are shadow-only, so the gate log shows G3 as each card's last
    gate. No G4 or G6 row is written by hand.
- **Two runs, as GR1:**
  - Run 1 (development): fits nothing, because every variant is fixed. It measures each variant and applies G1. It
    writes `selection.json` and is committed.
  - Run 2 (2023-26, once): only G1-passing variants, Holm across them.
  - Judge B reproduces both runs before the results are read.

## What the report shows (each with an evidence label)

Per variant, index and period:
- net P&L (total and per trade);
- the share of trades won;
- max drawdown on the cumulative net, and the worst calendar month;
- return on margin: net over SPAN plus exposure at entry;
- costs and pads as a share of gross;
- trades not taken, by reason (missing strikes, unfillable, bad prices, no trade under the cap).

Labels: every result is *exploratory* (spent data), and the strength word is said beside it:
- *some evidence* for a variant that passes run 2's Holm test and was also positive in run 1;
- *reasoning only* for the rest.

**Nomination rule, fixed now.** A variant is nominated for a forward shadow (at most two, by run 2's Holm-adjusted p)
only when all of these hold:
- run 2's one-sided p of mean net per trade > 0 (block bootstrap by month, G4's code), Holm-adjusted across the variants
  run 2 tests, is at most 0.05;
- run 2's mean net is positive at both pad levels;
- run 1's mean net was positive.

A nomination is a proposal to the owner, never a trade.

## Build (after text PASS; nothing merges before Mon 26 Oct unless it is fno/-free)

Extensions to the existing engine, each behind an existing interface, agreed with each owner first:
1. A BANKNIFTY chain source for the cycle simulator, from `BhavcopyChains`, behind the panel's read methods.
2. Historical lot sizes.
3. Exit rules SL2, TP50 and EXP (with G13c's settlement) beside the engine's time exit.
4. The C2 margin call per entry.

No second simulator and no second cost model. The study code goes in `research/edge1/` like GR1's, with tests and
planted-bug proof.

## Open questions for the owner

- Q1: defined-risk only (default a), or also measure the naked strangle and straddle (b)?
- Q2 (revised): accept that EDGE1 can only screen and nominate, and that any nominee's confirmatory test is a forward
  shadow through R3? All history is spent, and the direction was partly foreseen by GR1; the judge notes that holding
  data back costs only time.
