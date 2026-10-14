# Response 92: first-strategy candidates for Book 1 (desk meeting 2, 14 Oct 2026)

Owner: "6. Start research for a first strategy? => A" (`docs/DESK_DECISIONS.md`). Research only: nothing is registered.
Every number below is reproduced by `research/2026-10-14-desk-meeting-2/analysis.py` (output in `output.txt` there).

## Verdict

**Main finding: no forward test can prove a monthly rule in useful time.** At 12 trades a year, showing a small edge at
2 standard errors needs about 1,200-2,000 trades, i.e. about 100-165 years. S1's 6-month claim rule sees about 6 trades. A shadow
test can expose a disaster but never confirm an edge (strong evidence, arithmetic: statistician section below).

**And there is no candidate worth that wait: zero with a credible edge after costs.** Under the given limits (NIFTY
monthly expiry 30-45 days out, exit 21 days before expiry, defined risk, Rs 10,000 maximum loss, 1 lot):

- the option premium is real but smaller than the cost of trading it (Rs 810-940 per four-leg round trip);
- the one structure that cuts costs (a two-leg put spread) is still negative in a model built on today's real quotes,
  and it is **blocked on code**.

I recommend registering **no strategy candidate**. One optional item is a **benchmark shadow**, the monthly short
condor (P1), labelled as a measurement and not a candidate. Its aim is to measure the real premium and costs at 15:00
quotes from now on.

Confidence: **strong evidence** that costs exceed the gross premium of protected four-leg structures in both periods;
**some evidence** for the two-leg spread's costs (one day of quotes); **reasoning only** for the put-spread model.

## What the data says (each role)

**Data and backtesting engineer: what is left to test on.** The 2019-23 holdout was used by experiment 1 (judge 53
freeze, ChatGPT review 30), and 2024-26 is discovery data, already seen. So **no untouched history remains**: every
historical number here is already-seen data, and the only clean test of any new rule is forward (experiment 2,
shadow). I ran no new strategy P&L on NSE option prices, because that would be a new trial on spent data (ledger: 36
trials so far). Sections 1-2 of the script summarise experiment 1's recorded results, 3-4 read the 14 Oct quotes, 5
measures NIFTY's own moves, and 6 is a pricing model, not a backtest.

**Mathematician and tax and cost accountant: the cost wall (strong evidence, experiment 1, impossible exits removed).**

| Structure | Period | Trades | Gross per trade | Costs per trade | Net per trade | SD | Worst |
|---|---|---|---|---|---|---|---|
| SC short condor | 2024-26 | 33 | +978 | 824 | +153 | 2,667 | -6,298 |
| SC short condor | 2019-23 | 57 | +408 | 814 | -406 | 3,403 | -8,937 |
| SF short iron fly | 2024-26 | 32 | +479 | 924 | -446 | 1,160 | -3,755 |
| SF short iron fly | 2019-23 | 54 | +85 | 875 | -791 | 1,629 | -4,115 |
| BF long iron fly | 2024-26 | 27 | -312 | 939 | -1,251 | 750 | -4,634 |
| BF long iron fly | 2019-23 | 46 | +837 | 894 | -57 | 3,123 | -4,474 |

- Costs are Rs 814-939 per four-leg round trip: Rs 520 pads (Rs 1 per leg each way, x 65) plus charges.
- The condor's gross premium is positive in both periods, so selling volatility does earn something. But it is
  Rs 400-980 a month against Rs 810-820 of costs.
- The Rs 10,000 cap forces wings of at most about 300 points, which caps the premium collected. After costs and tax at
  31.2%, nothing is left.

**Volatility trader: the premium exists (strong evidence, recorded features).**
- At-the-money implied volatility was above the past 20-day realised in 74% (2019-23) and 82% (2024-26) of entries,
  with a median of about 2 points.
- On 14 Oct at 14:55 IST (Nov expiry, 40 days out; VIX 14.74), the put skew is clear: implied vol is 15.35% at -3.3%,
  13.8% at the money and 13.1% at +3.3%.
- As a monthly filter, though, "implied above realised" did not pick better condor months (experiment 1: P4 -29,190 vs
  its opposite -12,422).

**Market microstructure: the Rs 1 pad is realistic (some evidence, one day).** On 14 Oct, out-of-the-money Nov legs
from -5.5% to +4.1% had half-spreads of Rs 0.17-0.75 (`output.txt`, section 3-4). Rs 1 is slightly cautious, not
inflated. Cutting it to Rs 0.5 saves about Rs 260 a condor, which still leaves the 2019-23 condor at about -150.
In-the-money legs are wide (Rs 3-180) and must never be used.

**Options strategist: what could beat the cost wall, and why it still fails here.**
- Fewer legs halve the costs. A short put spread (sell the put 3% below, buy one 150 points lower) collects the put
  skew and NIFTY's upward drift, for about Rs 410 a round trip instead of about Rs 820.
- The exit rule hurts it. Exiting at 21 days keeps only the slow early part of the decay of a 40-day option, while
  paying full costs.
- I modelled it (reasoning only). Today's real 15:00 prices and skew are replayed on the 93 historical holding-window
  moves, with implied vol fixed per strike:
  - exit at 21 days: **mean -Rs 243**, SD 1,808, worst -6,547, 57% winners;
  - with vol +3 points in falls over 2%: -Rs 250;
  - held to expiry: -Rs 355, worst -8,221, 80% winners.
- So it is negative under both exits. The model has two weaknesses: it uses one day's prices across seven years of
  markets, and in a real market today's 14.7 VIX would differ in each regime.
- Desk meeting 1's near-the-money bullish spread lost too (bull call 100: -27,541 over 33 cycles).

**Statistician: a monthly rule cannot be proven forward in a useful time (strong evidence, arithmetic).**
- To show a mean above zero at 2 standard errors needs n = (2 x SD / mean)^2. That is 1,212 trades for the 2024-26
  condor (+153, SD 2,667), and 1,979 if that edge comes with the 2019-23 condor's SD of 3,403: about 100-165 years
  at 12 trades a year. (My first draft said "280-1,200". The 280 came from the 2019-23 condor's negative mean, so it
  counted trades to prove a loss, not an edge: judge 93.)
- S1's "claim after 120 trading days" gives about **6 monthly trades**. With an SD of about Rs 2,700-3,400, the
  standard error of the mean is about Rs 1,100-1,400 a trade, which is 3-9 times larger than any plausible edge here.
- A forward shadow of a monthly rule can therefore only expose a disaster; it can never confirm an edge. **The owner
  should know this before choosing S1's 6-month rule for monthly strategies.**

**Risk manager: what one lot costs and what kills it (strong evidence for margins).**
- Margin on 14 Oct (NSE SPAN plus exposure, response 77) for a 300-wide condor: Rs 67,595 initial, Rs 71,428
  stressed at 1.45. A 300-wide short fly: Rs 62,679 initial, Rs 64,300 stressed.
- **Funds at entry are more than the margin.** C2's formula (`fno/risk/margins.py`, judge 77 addendum 3) is
  `max(0, k x scan - NOV) + exposure + bought premium + charges`: at entry the broker credits nothing for the sold
  premium and takes the bought premium at once. For the SC 300 lot on 14 Oct's 15:00 quotes (sold legs at the bid,
  bought at the ask) that is 81,581 + 19,045 bought wings + 158 charges = **Rs 1,00,784** (script section 7). My first
  draft listed the stressed margin as the funds (judge 93).
- Rs 59,077 of every row is exposure margin on the two short legs, and a hedge does not reduce it. So Rs 60,000-71,000
  of margin (and about Rs 1,00,000 of funds at entry for a condor) is tied up for at most Rs 10,000 of risk and
  Rs 400-1,000 of gross premium a month.
- A put spread has one short leg, so its exposure margin is about Rs 29,500. No NSE row exists for it, so I bound its
  scan risk between the SC 100 and SC 200 rows' (Rs 2,651-5,424). Its stressed margin is then about
  **Rs 33,400-37,400**, and its **funds at entry about Rs 44,500-48,500**, including the bought 21850 put (about Rs 9,200
  at the ask) and charges (estimate).
- NIFTY fell 3% or more in 10 of 93 holding windows and 5% or more in 3 (worst -6.9%). Those are the months a short put
  spread loses most of its Rs 8,351 cap.
- The cap failed twice in 2019 on stale closes (-11,346, -13,728): live exits must use quotes.

**Portfolio manager: who pays?** The buyers of index puts pay for crash insurance (skew), and buyers of options pay for
volatility (variance premium). Both are real and documented worldwide, and both show in our data (gross condor premium
positive; skew on 14 Oct). They do not pay *us* under these limits. A retail seller with one lot, Rs 1 slippage per
leg, 2% exposure margin per short leg and a Rs 10,000 cap passes most of the premium to costs.

**Red team.** The 2024-26 condor's +153 is the result we chose the experiment from (discovery). The challenge then
reversed it (-406), and P4 (+21,452 in discovery) became -29,190. Any new filter tuned on these same years would be the
36th-plus trial on the same history and would very likely fail in the same way.

**Behavioural finance.** The danger now is loosening rules until something "works": wider caps, more filters, shorter
holds. Each loosening is a new trial and must be registered first. Trading nothing is a valid result, and the
project's own rule says the tool shuts down if paper shows no net profit.

**Regulation (SEBI/NSE).** Lot 65; index-option exposure margin is 2% of notional per short leg (response 77). One
weekly expiry per exchange (NIFTY on NSE) is allowed under SEBI's November 2024 rule, as far as I know (not re-checked
today), but our design is monthly-only.

**Market research, macro and positioning analysts.** We have no tested signal yet:
- participant OI (A8) has 0 of 20 measured release days;
- flows and macro data are not in the repository as tested features.
None can back a rule today (reasoning only).

## Candidates (the requested table)

| | B0: monthly short condor, benchmark shadow (optional) | A: short put spread (not recommended now) |
|---|---|---|
| Rule | Experiment 1's P1: sell the call nearest forward x 1.02 and the put nearest x 0.98, buy wings at the widest of 300/250/200/150/100 points with modelled maximum loss incl. charges at most Rs 10,000; every monthly cycle; exit at the last 15:00 with 21+ days to expiry | Sell the put about 3% below the forward, buy the put 150 points lower (width set by the Rs 10,000 cap); every cycle; same exit |
| Why it should earn | Variance risk premium: implied above realised (median +2 points). **Purpose: measurement, not profit**: it measures the real premium and costs at 15:00 quotes | Put skew plus NIFTY's upward drift, at half the four-leg costs |
| Evidence | Strong: gross positive in both periods (+978, +408) but net -406 in 2019-23 (holdout used up: experiment 1) and +153 in 2024-26 (discovery, seen) | Some: costs measured on one day; skew on 14 Oct. Reasoning: the model is negative (-243 at the 21-day exit, -355 to expiry). No untouched history is left |
| Trades per year | 12 (fewer when a cycle is unfillable: 1 of 60 in 2019-23) | 12 |
| Worst historical loss per lot | -8,937 (2019-23, clean); -11,346 on a stale close (cap broken: exit on quotes) | Structural maximum 8,351 (credit 1,809 on 14 Oct); model worst -6,547 at the 21-day exit. Not run on historical option prices (a new trial on spent data) |
| Stressed margin per lot (C2, k 1.45) | Rs 71,428 (SC 300, 14 Oct NSE SPAN plus exposure; Rs 67,595 initial) | About Rs 33,400-37,400 (estimate: one short leg's exposure about Rs 29,500, scan bounded by SC 100-200); no NSE row yet |
| Funds at entry per lot (C2: no credit for the sold premium, bought premium and charges paid) | **Rs 1,00,784** (81,581 + 19,045 bought wings + 158 charges, 14 Oct quotes) | About **Rs 44,500-48,500** (includes the bought put, about Rs 9,200) |
| What proves it wrong | Not a candidate: it informs the cost and premium estimates. Stop it if a single loss exceeds Rs 10,000 (catastrophic-loss rule) | A forward mean net per trade below 0 after 12 trades, or gross per trade below Rs 410 (its costs) |
| Blocker | None: SC exists in D1, B2, C4 and A14 | **Code**: D1 `STRUCTURE_CODES`, the B2 simulator, D2 candidates, C4 and A14 margin rows know only SF, SC and BF (lane 1, flagged to the orchestrator) |

Rejected, with the reason:
- **SF every month:** costs above gross in both periods (net -446 and -791).
- **BF every month:** negative after impossible exits are removed (-2,642 in 2019-23; -1,251 per trade in 2024-26).
- **Condor with an IV filter (P4/P6/P7):** each filter failed the challenge against its opposite or random timing.
- **Trend spreads:** no trend edge (desk 1, trials 2-4 and 10).
- **Long straddle:** -3,24,905 (desk 1).
- **Calendar spreads:** no next-month quote history and no data on their term-structure premium (reasoning only).

## What would change the answer (owner questions, plain)

1. **The 21-day exit.** It halves the decay a seller keeps while costs stay whole. Even so, holding to expiry was
   still negative in the model (-355), so changing the rule alone does not create an edge (reasoning only).
2. **Monthly-only means 12 trades a year,** too few ever to prove a small edge. Weekly expiry would give about 50 a
   year, but with more cost per rupee of premium. Do you want the desk to study weekly options as a separate,
   registered question?
3. **The Rs 10,000 cap and 1 lot keep wings narrow** (at most 300 points), and costs dominate at that size. The cap is
   your survival rule, and I do not recommend loosening it to find an edge.
4. **Option A needs code first.** It cannot even be shadow-tested until the code exists. See the next section for the
   story's size and what it would buy.

## The put-spread structure story (lane 1): rough size, and what the owner gets

**Size (estimate from reading the code; medium):** about 8-10 files in `fno/` plus their tests, and one interface
change. Roughly a day of building and one judge round.

- **B2 simulator, `fno/research_engine/structures.py`:** the `Structure` interface builds exactly four legs (a body call
  and put plus two wings). A two-leg vertical needs each structure to build its own legs. This is an interface change,
  and every structure and its tests follow from it.
- **C4, `fno/checks/validity_modes.py`:** the shape check refuses anything that is not four legs of SF, SC or BF. It
  needs a rule for the new shape, and its independent maximum-loss check must cover one side only.
- **D1, `fno/constants.py`, `fno/playbook/structure_spec.py` and `vocabulary.py`:** a new code (e.g. `SP`, short put
  spread) and its strikes rule.
- **D2 candidates, `fno/playbook/candidates.py`:** builds legs through the structures, so it should follow; check it.
- **A14, `fno/nse_margins/`:** the calculator works on any legs, but the job produces rows for the known codes only. It
  needs the new code's rows, with one short leg's exposure. The broker check (judge 77) covered four-leg rows only.

**What the owner gets, given forward proof takes years anyway:**
- Half the costs (about Rs 410 instead of Rs 820 a trade), about half the stressed margin (an estimated Rs 33,400-37,400
  instead of Rs 71,428) and less than half the funds at entry (about Rs 44,500-48,500 instead of Rs 1,00,784). This
  makes a small edge possible, but not proven.
- The option of trading the put skew alone, without the call side, whose premium is thinner (13.1% at +3.3%).
- **Not** a faster proof: it is still 12 trades a year.

**My recommendation: not now.** The model is negative (-243 a trade), and the B0 benchmark records the condor's put
half, which is itself a short put spread about 2% out. B0 therefore yields forward data on the put-spread premium at
real 15:00 quotes **without new code**. Build the story only if, after about 6-12 cycles, B0's put half shows a gross
above about Rs 410 a trade, the put spread's cost (reasoning only).

## Decisions proposed to the head of desk and the owner

- Register **no** strategy candidate from this meeting.
- Optional: register **B0** as a benchmark shadow named as such (status `research`, `payer` saying "measurement only").
  It records the real premium and costs at 15:00 quotes, the only untouched data we will get. Owner's choice.
- Keep recording 15:00 quotes daily (A4). After about 6 months they allow the first test on real bid/ask exits (a new,
  registered experiment).
- Do not tune filters on 2019-26 again.

Files: `research/2026-10-14-desk-meeting-2/analysis.py` and `output.txt`. Sources: `research/2026-10-12-experiment-1/`
(RESULTS.md and results JSON), `research/data/quotes/groww/.../nifty_20261014_145500.csv`, `research/data/nifty-panel/`,
`reviews/claude/response_77_a14-nse-margins.md`, `research/2026-10-12-desk-meeting-1/`.
